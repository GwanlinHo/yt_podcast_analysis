#!/bin/bash
# 安全同步到公開 repo：白名單 add(不用 git add .) + 推送前金鑰/敏感檔掃描護欄。
# 只發布報表產物與分析結果; 刻意不含 data/transcripts(第三方 podcast 逐字稿, 版權考量, 留本機)。
# 原始碼/設定變更請人工另行 commit。

set -o pipefail
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

# 發布白名單(目錄項會納入其下新檔)。data/ 整目錄納入, 但 data/transcripts 與 data/podcast_audio
# 已在 .gitignore -> git add 自動排除(不公開逐字稿/音檔), 其餘 data 產物(database/csv/索引/analysis)照發布。
WHITELIST=(index.html archives.html report data podcast_feeds.json)

SECRET_PATTERNS='(sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'
FORBIDDEN_FILES='(^|/)(\.env|\.env\..+|\.credentials\.json|credentials\.json|\.git-credentials|.+\.pem|id_rsa|.+\.key)$'

echo "正在從遠端拉取最新狀態..."
git pull || { echo "[X] 拉取衝突或錯誤，請手動解決後再繼續。"; exit 1; }

for p in "${WHITELIST[@]}"; do
  [ -e "$p" ] && git add -- "$p"
done

if git diff --cached --quiet; then
  echo "沒有白名單內的變更需要提交。"
  exit 0
fi

STAGED="$(git diff --cached --name-only)"
BAD="$(printf '%s\n' "$STAGED" | grep -iE "$FORBIDDEN_FILES")"
if [ -n "$BAD" ]; then
  echo "[X] staged 含禁列敏感檔，中止推送："; printf '%s\n' "$BAD"
  printf '%s\n' "$BAD" | while IFS= read -r bf; do [ -n "$bf" ] && git reset -q HEAD -- "$bf"; done
  exit 1
fi
HIT="$(git diff --cached -U0 | grep -aE "$SECRET_PATTERNS" | head -5)"
if [ -n "$HIT" ]; then
  echo "[X] staged 內容命中金鑰樣式，中止推送(請檢查)："; printf '%s\n' "$HIT"
  exit 1
fi

echo "發現白名單變更，提交並推送..."
git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')" || exit 1
git push || exit 1

# Pages 部署護欄(共用函式庫,失敗自動重觸發一次;見 _lib/pages_guard.sh)
PAGES_GUARD=/home/pi/WorkDir/_lib/pages_guard.sh
if [ -r "$PAGES_GUARD" ]; then
  source "$PAGES_GUARD"
  verify_pages_or_retrigger
else
  echo "[!] 找不到 $PAGES_GUARD,略過 Pages 部署驗證。"
fi
