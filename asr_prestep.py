"""ASR 前置步驟(獨立、純 Python、不啟動 claude)。

流程:
  1. 讀 podcast_feeds.json,抓各頻道 RSS,收錄「報告視窗(近7天)內」的集數,
     upsert 進 database.json(source=podcast,帶 audio_url enclosure)。
  2. 對視窗內、pending、且尚無逐字稿的 podcast 影片:下載音檔 → 用 faster-whisper
     (asr_whisper 專案,small/beam1/分段)轉成逐字稿,存到 data/transcripts/<id>.txt。

為何獨立:ASR(~0.8-1.7GB)與 claude(~1GB)同時跑會 OOM。這步在 cron 的
claude -p @analyze_next 之前先把逐字稿準備好;claude 只負責讀逐字稿做分析,不做 ASR。

設計給 cron:每次最多轉 MAX_PER_RUN 集(避免單次過久);一天三班足以消化每日新集。
"""
import json, os, re, subprocess, hashlib, datetime
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from storage import Storage, Video, TRANSCRIPT_DIR

WINDOW_DAYS = 7
# 排程警語:ASR 每集約 1.5-2 小時(Pi CPU)。現有 yt cron 每 2 小時一班,塞不下多集。
# 本步驟應安排為「獨立、有充足時段」的班次(例如夜間單班),而非塞進 2 小時的 cron 縫隙。
# 上限設 2,避免單次過久;每日新 podcast 集數約 1-2 集,分天消化即可。
MAX_PER_RUN = 2
FEEDS_FILE = "podcast_feeds.json"
AUDIO_DIR = "data/podcast_audio"
ASR_DIR = "/home/pi/WorkDir/asr_whisper"
ASR_PY = os.path.join(ASR_DIR, ".venv/bin/python3")
ASR_SCRIPT = os.path.join(ASR_DIR, "transcribe.py")


def ep_id(guid: str) -> str:
    """由 guid 產生穩定、檔名安全的 11 碼 id(模仿 YouTube id 長度)。"""
    return "pc_" + hashlib.md5(guid.encode("utf-8")).hexdigest()[:8]


def ep_number(title: str):
    """從標題擷取集數編號(財報狗『533.』、M觀點『EP312』、兆華『EP1122』);無則 None。
    用於跨來源去重:同頻道若已有相同集數的影片(例如先前用 YouTube 做過的),就不重複收錄 podcast 版。"""
    m = re.search(r"(\d{2,5})", title or "")
    return m.group(1) if m else None


def fetch(url: str) -> bytes:
    out = subprocess.run(["curl", "-sL", "--max-time", "60", url], capture_output=True)
    return out.stdout


def parse_episodes(xml_bytes: bytes, channel: str):
    """回傳 [(id, title, date(YYYYMMDD), link, audio_url), ...]"""
    eps = []
    root = ET.fromstring(xml_bytes)
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        guid = (item.findtext("guid") or item.findtext("link") or title).strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate")
        enc = item.find("enclosure")
        audio = enc.get("url") if enc is not None else ""
        if not pub or not audio:
            continue
        try:
            d = parsedate_to_datetime(pub).strftime("%Y%m%d")
        except Exception:
            continue
        eps.append((ep_id(guid), title, d, link or audio, audio))
    return eps


def main():
    db = Storage()
    today = datetime.datetime.now()
    start = (today - datetime.timedelta(days=WINDOW_DAYS)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    # 跨來源去重用:每個頻道「已成功分析」影片的集數編號集合。
    # 只對 analyzed 去重(若同集數的 YouTube 版只是 pending/skipped、未成功分析,
    # podcast 版仍應收錄並分析,以正式補上該集)。
    existing_eps = {}
    for v in db.videos.values():
        if v.status != "analyzed":
            continue
        n = ep_number(v.title)
        if n:
            existing_eps.setdefault(v.channel, set()).add(n)

    feeds = json.load(open(FEEDS_FILE, encoding="utf-8"))
    added, skipped_dup = 0, 0
    for channel, url in feeds.items():
        print(f"[feed] {channel} ...", flush=True)
        try:
            eps = parse_episodes(fetch(url), channel)
        except Exception as e:
            print(f"   [錯誤] 解析失敗: {e}")
            continue
        for vid, title, d, link, audio in eps:
            if not (start <= d <= end):
                continue
            if vid in db.videos:
                continue  # 同一 podcast 集已收錄
            n = ep_number(title)
            if n and n in existing_eps.get(channel, set()):
                skipped_dup += 1  # 同頻道同集數已用其他來源(如 YouTube)做過,跳過避免重複
                continue
            v = Video(id=vid, title=title, url=link, date=d, channel=channel,
                      source="podcast", audio_url=audio)
            if db.upsert_video(v):
                print(f"   [New] {d} {title[:36]}")
                added += 1
                if n:
                    existing_eps.setdefault(channel, set()).add(n)
    db.save_database()
    if skipped_dup:
        print(f"[feed] 跳過 {skipped_dup} 集(同集數已由其他來源分析過,去重)")
    print(f"[feed] 視窗內新增 podcast 集數: {added}")

    # 轉錄:視窗內、pending、podcast、尚無逐字稿者(最舊優先,單次上限 MAX_PER_RUN)
    todo = [v for v in db.get_pending_in_window(days=WINDOW_DAYS, limit=None)
            if v.source == "podcast" and not db.has_transcript(v.id)]
    todo = todo[:MAX_PER_RUN]
    print(f"[asr] 待轉錄 {len(todo)} 集(本次處理上限 {MAX_PER_RUN})")
    os.makedirs(AUDIO_DIR, exist_ok=True)
    for v in todo:
        mp3 = os.path.join(AUDIO_DIR, f"{v.id}.mp3")
        tpath = db.transcript_path(v.id)
        print(f"[asr] {v.date} {v.channel} {v.title[:30]} ...", flush=True)
        try:
            subprocess.run(["curl", "-sL", "--max-time", "600", "-o", mp3, v.audio_url], check=True)
            subprocess.run([ASR_PY, ASR_SCRIPT, mp3, "--out", tpath,
                            "--model", "small", "--chunk", "180"], check=True)
            ok = os.path.exists(tpath) and os.path.getsize(tpath) > 0
            print(f"[asr] {'完成' if ok else '失敗(無逐字稿)'}: {tpath}")
        except Exception as e:
            print(f"[asr] 轉錄失敗: {e}")
        finally:
            if os.path.exists(mp3):
                os.remove(mp3)  # 音檔用完即刪,省空間


if __name__ == "__main__":
    main()
