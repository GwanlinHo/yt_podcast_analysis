# YouTube Tech & Podcast Analysis (財經影片分析系統)

本系統用於自動化追蹤、分析 YouTube 財經頻道，並生成結構化的分析報告。系統採用資料庫與 AI 分析分離的架構。

## 功能

- **自動化更新**: 透過 `daily_update.py` 追蹤指定頻道（如股癌、財報狗、財女珍妮、M觀點等）的新影片。
- **AI 深度分析**: 透過 Gemini Agent 對影片重點議題進行歸納，並標註提及標的多空觀點。
- **結構化報表**: 自動生成 HTML 格式的財經週報與最新分析報告。
- **資料庫管理**: 所有影片資訊與分析結果皆以 JSON 格式持久化儲存。

## 專案結構

- `daily_update.py`: 每日更新資料庫腳本。
- `generate_report.py`: 生成 HTML 報表腳本。
- `storage.py`: 資料庫存取邏輯 (Storage Class)。
- `data/`:
  - `database.json`: 影片清單與狀態資料庫。
  - `analysis/`: 存放各影片詳細分析結果的 JSON 檔案。
- `report/`: 存放生成的 HTML 財經週報與最新報表 (`latest_report.html`)。
- `GEMINI.md`: 記錄 Agent 的標準作業流程 (SOP) 與輸出規範。
- `sync.sh`: Git 同步腳本，用於發布報告。

## 安裝與使用

1. **環境設定** (建議使用 [uv](https://github.com/astral-sh/uv)):
   ```bash
   uv sync
   ```

2. **操作流程** (透過 Gemini Agent 指令):
   - **`@daily_update`**: 更新影片資料庫並檢查有無新影片。
   - **`@analyze_next`**: 針對下一部待處理影片進行內容摘要與標的分析。
   - **`@publish`**: 生成最新報表並執行 `sync.sh` 同步至遠端。

## 輸出規範

- **重點議題**: 須包含邏輯推演。
- **提及標的**: 需標註多空觀點 (`view`) 與理由 (`rationale`) 與對應標的。
- **格式規範**: 嚴禁使用 Emoji。