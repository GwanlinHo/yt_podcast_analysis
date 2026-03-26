# YouTube Finance Analysis (財經影片分析系統)

本系統用於自動化追蹤、分析 YouTube 財經頻道（如股癌、財報狗、財女珍妮、M觀點等），並透過 AI 生成結構化的分析報告。

## 🌟 特色功能

- **自動化更新**: 透過 `daily_update.py` 追蹤新影片。
- **AI 深度分析**: 透過 Gemini Agent 歸納重點議題，標註多空觀點與邏輯。
- **GitHub Pages 支援**: 自動同步更新根目錄的 `index.html`，方便手機隨時查看。
- **條件式報告生成**: 只有在內容有實質更新時才更新報表，節省儲存空間。
- **週報存檔機制**: 可定期產出帶日期的歷史週報檔案。

## 📱 行動端查看 (GitHub Pages)

本專案支援 GitHub Pages，你可以透過以下步驟設定：
1.  前往 GitHub Repository 的 **Settings** > **Pages**。
2.  將 **Build and deployment** > **Branch** 設定為 `main` (或你使用的分支)，資料夾選取 `/ (root)`。
3.  儲存後，你就可以透過 `https://<你的帳號>.github.io/<專案名稱>/` 隨時隨地查看最新的財經摘要。

## 📂 專案結構

- `index.html`: **[核心]** 供 GitHub Pages 顯示的最新報告網頁。
- `generate_report.py`: 生成 HTML 報表與同步 `index.html` 的腳本。
- `daily_update.py`: 每日更新影片資料庫。
- `storage.py`: 資料庫 (JSON) 存取邏輯。
- `data/`: 存放影片資料庫與詳細分析結果。
- `report/`: 存放 `latest_report.html` 與帶日期的歷史週報存檔。
- `GEMINI.md`: 標準作業流程 (SOP) 與分析規範。

## 🚀 操作流程

### 1. 每日更新與分析
透過 Gemini Agent 執行指令：
- **`@daily_update`**: 獲取新片清單。
- **`@analyze_next`**: 自動分析下一部影片內容。

### 2. 結算週報與同步
- **生成最新狀態**: `uv run generate_report.py` (僅內容變動時更新 `index.html`)。
- **結算帶日期週報**: `uv run generate_report.py --weekly`。
- **同步至 GitHub**: 執行 `./sync.sh` 或透過指令 `@publish`。

## 📋 分析規範

- **重點議題**: 須包含邏輯推演，而非僅列出結論。
- **提及標的**: 需標註多空觀點 (`Bullish`/`Bearish`/`Neutral`) 與具體理由 (`rationale`)。
- **格式**: 為求專業感，嚴禁在報告內容中使用 Emoji。