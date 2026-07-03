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
# 排程(cron 00:00 起跑):實測轉錄約 1.5x 即時(每 1 分鐘音檔約 1.5 分鐘 wall-clock,Pi CPU),
# 取保守 1.8x 估計留餘裕。集數長短差很大(35-101 分鐘),故以「音檔總時長」為單次預算
# (而非固定集數),讓單次 wall-clock 可預期、不會因撞到長集而爆掉時段。
#
# 兩層時間保護,確保 ASR 在 05:00 的 claude @analyze_next 班之前收工並釋放「全域重型鎖」:
#   (1) 預算 MAX_AUDIO_MIN_PER_RUN:150 分音檔 ≈ 4.5 小時轉錄(1.8x),00:00 起約 04:30 完成。
#   (2) 硬死線 ASR_DEADLINE_HHMM(預設 04:30):每集開始前估算是否會超過死線,會超過且已做 ≥1 集就停,
#       剩餘集數留待隔夜(它們下次成為最舊、必被處理,不會永遠卡住)。
# 為何重要:ASR(~0.8-1.7GB)與 claude(~1GB)同時跑會 OOM。ASR 持有全域重型鎖時 claude cron 會等待或跳過;
# 若 ASR 不準時釋鎖,05:00 的 yt claude 會一直等不到鎖 → 當日分析無法進行。故死線是硬性要求。
MAX_AUDIO_MIN_PER_RUN = 150
MAX_COUNT_PER_RUN = 6  # 安全上限(避免極短集數時一次抓太多)
# 硬死線:當日 HH:MM 前必須收工(cron 00:00 起跑情境)。白天手動執行(now 已過死線)則自動不套用。
# 測試可用環境變數覆寫,或設 ASR_NO_DEADLINE=1 完全停用死線。
ASR_DEADLINE_HHMM = os.environ.get("ASR_DEADLINE_HHMM", "0430")
WALL_PER_AUDIO_MIN = 1.8  # 保守:每 1 分鐘音檔估 1.8 分鐘 wall-clock(實測約 1.5)
FEEDS_FILE = "podcast_feeds.json"
AUDIO_DIR = "data/podcast_audio"
ASR_DIR = "/home/pi/WorkDir/asr_whisper"
ASR_PY = os.path.join(ASR_DIR, ".venv/bin/python3")
ASR_SCRIPT = os.path.join(ASR_DIR, "transcribe.py")


def compute_deadline():
    """回傳今日死線 datetime;若已過(白天手動執行)或設 ASR_NO_DEADLINE 則回傳 None(不套用死線)。"""
    if os.environ.get("ASR_NO_DEADLINE"):
        return None
    now = datetime.datetime.now()
    try:
        hh, mm = int(ASR_DEADLINE_HHMM[:2]), int(ASR_DEADLINE_HHMM[2:])
    except Exception:
        hh, mm = 4, 30
    dl = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return None if now >= dl else dl


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


def parse_duration(s) -> int:
    """itunes:duration → 秒。支援『2108』『35:08』『01:35:08』。失敗回 0。"""
    if not s:
        return 0
    s = s.strip()
    try:
        if ":" in s:
            parts = [int(p) for p in s.split(":")]
            sec = 0
            for p in parts:
                sec = sec * 60 + p
            return sec
        return int(float(s))
    except Exception:
        return 0


def parse_episodes(xml_bytes: bytes, channel: str):
    """回傳 [(id, title, date(YYYYMMDD), link, audio_url, dur_sec), ...]"""
    ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
    eps = []
    root = ET.fromstring(xml_bytes)
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        guid = (item.findtext("guid") or item.findtext("link") or title).strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate")
        enc = item.find("enclosure")
        audio = enc.get("url") if enc is not None else ""
        dur = parse_duration(item.findtext("itunes:duration", default="", namespaces=ns))
        if not pub or not audio:
            continue
        try:
            d = parsedate_to_datetime(pub).strftime("%Y%m%d")
        except Exception:
            continue
        eps.append((ep_id(guid), title, d, link or audio, audio, dur))
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
    dur_map = {}  # id -> 音檔秒數(供轉錄預算用)
    added, skipped_dup = 0, 0
    for channel, url in feeds.items():
        print(f"[feed] {channel} ...", flush=True)
        try:
            eps = parse_episodes(fetch(url), channel)
        except Exception as e:
            print(f"   [錯誤] 解析失敗: {e}")
            continue
        for vid, title, d, link, audio, dur in eps:
            if not (start <= d <= end):
                continue
            dur_map[vid] = dur
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

    # 轉錄:視窗內、pending、podcast、尚無逐字稿者(最舊優先)。
    # 以音檔總時長為預算:累積到 MAX_AUDIO_MIN_PER_RUN 就停(但至少做 1 集),並設集數安全上限。
    candidates = [v for v in db.get_pending_in_window(days=WINDOW_DAYS, limit=None)
                  if v.source == "podcast" and not db.has_transcript(v.id)]
    todo, budget_min, total_min = [], MAX_AUDIO_MIN_PER_RUN, 0.0
    for v in candidates:
        if len(todo) >= MAX_COUNT_PER_RUN:
            break
        dur_min = dur_map.get(v.id, 0) / 60.0
        if dur_min <= 0:
            dur_min = 60.0  # 無時長資訊時的保守估計
        # 第一集(最舊)一定取(即使單集就超預算);之後放不下的長集先跳過、續抓較短的填滿,
        # 被跳過的長集下次會成為最舊、屆時必被處理,不會永遠卡住。
        if todo and total_min + dur_min > budget_min:
            continue
        todo.append(v)
        total_min += dur_min
    print(f"[asr] 本次處理 {len(todo)} 集,音檔合計約 {total_min:.0f} 分鐘(預算 {budget_min} 分)")
    deadline = compute_deadline()
    if deadline is not None:
        print(f"[asr] 死線 {ASR_DEADLINE_HHMM}(到點前收工釋放重型鎖,讓 05:00 claude 班可跑)")
    os.makedirs(AUDIO_DIR, exist_ok=True)
    done_count = 0
    for v in todo:
        now = datetime.datetime.now()
        # 死線護欄:已達死線就停;或預估本集會跨過死線且已完成 >=1 集就停(剩餘留待隔夜)。
        if deadline is not None:
            if now >= deadline:
                print(f"[asr] 已達死線 {ASR_DEADLINE_HHMM},停止本次(剩餘 {len(todo)-done_count} 集留待下次)")
                break
            dur_min_est = (dur_map.get(v.id, 0) / 60.0) or 60.0
            est_wall_min = dur_min_est * WALL_PER_AUDIO_MIN
            if done_count >= 1 and now + datetime.timedelta(minutes=est_wall_min) > deadline:
                print(f"[asr] 本集預估需約 {est_wall_min:.0f} 分,會超過死線 {ASR_DEADLINE_HHMM},"
                      f"停止本次(剩餘 {len(todo)-done_count} 集留待下次)")
                break
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
        done_count += 1


if __name__ == "__main__":
    main()
