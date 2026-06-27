#!/usr/bin/env python3
"""ASR 清理機制 — 清過期音檔 / 逐字稿 / 一次性暫存稿。

由 yt_asr_prestep.sh 在 ASR 轉錄完成後、sync.sh 之前自動呼叫(每天 00:00)。
三個清理目標:
  1. data/podcast_audio/*.mp3  : 已轉好稿(殘留) / status=skipped / 不在DB(孤兒) 的音檔;保留 pending 待轉的。
  2. data/transcripts/*.txt    : 對應影片日期早於 N 天前的逐字稿(已滑出週報視窗);孤兒稿按檔案時間判定。
  3. asr_whisper/transcripts/  : 檔案時間超過 M 天的一次性 ASR 暫存(書導讀/驗證等手動任務)。

刪逐字稿安全:generate_report.py 不讀逐字稿,報告由 data/analysis/*.json 生成。
podcast_audio 已被 .gitignore 擋掉,不會進公開 repo;transcripts 被 git 追蹤,刪除由 sync.sh 一併同步。

用法:
  python3 asr_cleanup.py            # 實際清理
  python3 asr_cleanup.py --dry-run  # 只預覽會刪哪些,不動檔案
"""
import os
import json
import datetime
import sys

YT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(YT_DIR, "data", "podcast_audio")
TRANSCRIPT_DIR = os.path.join(YT_DIR, "data", "transcripts")
DB_PATH = os.path.join(YT_DIR, "data", "database.json")
STAGING_DIR = "/home/pi/WorkDir/asr_whisper/transcripts"

TRANSCRIPT_KEEP_DAYS = 14   # 逐字稿:週報視窗 7 + 緩衝 7
STAGING_KEEP_DAYS = 7       # 一次性暫存稿

DRY_RUN = "--dry-run" in sys.argv
today = datetime.date.today()


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[%s] %s" % (ts, msg))


def parse_date(s):
    if s and len(s) == 8 and s.isdigit():
        try:
            return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except ValueError:
            return None
    return None


def mtime_date(path):
    return datetime.date.fromtimestamp(os.path.getmtime(path))


def main():
    removed = []

    videos = {}
    if os.path.exists(DB_PATH):
        with open(DB_PATH, encoding="utf-8") as f:
            videos = json.load(f).get("videos", {})

    have_t = set()
    if os.path.isdir(TRANSCRIPT_DIR):
        have_t = set(f[:-4] for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt"))

    # 1) 音檔:轉完殘留 / skipped / 孤兒 才清;pending 待轉一律保留
    if os.path.isdir(AUDIO_DIR):
        for f in sorted(os.listdir(AUDIO_DIR)):
            if not f.endswith(".mp3"):
                continue
            vid = f[:-4]
            path = os.path.join(AUDIO_DIR, f)
            v = videos.get(vid)
            reason = None
            if vid in have_t:
                reason = "已轉好稿,音檔殘留"
            elif v is None:
                reason = "不在DB(孤兒)"
            elif v.get("status") == "skipped":
                reason = "status=skipped"
            if reason:
                removed.append(("音檔", path, reason))

    # 2) 逐字稿:對應影片日期早於 cutoff(孤兒用檔案時間)才清
    cutoff_t = today - datetime.timedelta(days=TRANSCRIPT_KEEP_DAYS)
    if os.path.isdir(TRANSCRIPT_DIR):
        for f in sorted(os.listdir(TRANSCRIPT_DIR)):
            if not f.endswith(".txt"):
                continue
            vid = f[:-4]
            path = os.path.join(TRANSCRIPT_DIR, f)
            v = videos.get(vid)
            ref = parse_date(v.get("date")) if v else None
            if ref is None:
                ref = mtime_date(path)
            if ref < cutoff_t:
                removed.append(("逐字稿", path, "影片日期 %s 早於 %s" % (ref, cutoff_t)))

    # 3) 一次性暫存稿:檔案時間超過 cutoff 才清
    cutoff_s = today - datetime.timedelta(days=STAGING_KEEP_DAYS)
    if os.path.isdir(STAGING_DIR):
        for f in sorted(os.listdir(STAGING_DIR)):
            if not f.endswith(".txt"):
                continue
            path = os.path.join(STAGING_DIR, f)
            if mtime_date(path) < cutoff_s:
                removed.append(("暫存", path, "檔案時間 %s 早於 %s" % (mtime_date(path), cutoff_s)))

    # 執行
    prefix = "[DRY-RUN] " if DRY_RUN else ""
    if not removed:
        log(prefix + "清理完成,無可清項目。")
        return
    log(prefix + "共 %d 個檔案待清:" % len(removed))
    for kind, path, reason in removed:
        size_kb = os.path.getsize(path) / 1024.0
        log("  [X] %s %s (%.0fKB; %s)" % (kind, os.path.basename(path), size_kb, reason))
        if not DRY_RUN:
            os.remove(path)
    if DRY_RUN:
        log("[DRY-RUN] 以上僅預覽,未實際刪除。")
    else:
        log("清理完成,已刪除 %d 個檔案。" % len(removed))


if __name__ == "__main__":
    main()
