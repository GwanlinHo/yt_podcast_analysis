# YouTube Finance Analysis (財經影片分析系統)

本系統用於自動化追蹤、分析 YouTube 財經頻道（如股癌、財報狗、財女珍妮、M觀點等），並透過 AI 生成結構化的分析報告。

## 🌟 特色功能

- **自動化更新**: 透過 `daily_update.py` 追蹤新影片。
- **AI 深度分析**: 透過 Gemini Agent 歸納重點議題，標註多空觀點與邏輯。
- **GitHub 自動同步**: **[新功能]** `generate_report.py` 成功更新報表後，會自動執行 `./sync.sh` 將最新的 `index.html` 上傳至 GitHub。
- **GitHub Pages 支援**: 支援 GitHub Pages，方便手機隨時透過 URL 查看最新報表。
- **條件式報告生成**: 只有在內容有實質更新時才更新報表，節省儲存空間與減少 Git 無意義提交。
- **週報存檔機制**: 可定期產出帶日期的歷史週報檔案。

## 📱 行動端查看 (GitHub Pages)

本專案支援 GitHub Pages，你可以透過以下步驟設定：
1.  前往 GitHub Repository 的 **Settings** > **Pages**。
2.  將 **Build and deployment** > **Branch** 設定為 `main` (或你使用的分支)，資料夾選取 `/ (root)`。
3.  儲存後，你就可以透過以下網址隨時隨地查看最新的財經摘要：
    **👉 [https://GwanlinHo.github.io/yt_podcast_analysis/](https://GwanlinHo.github.io/yt_podcast_analysis/)**

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
- **`@daily_update`**: 獲取新片清單，並自動分析第一部新影片。
- **`@analyze_next`**: 分析下一部影片，並**自動同步至 GitHub**。

### 2. 生成報表與同步 (自動化)
- **生成最新狀態**: `uv run generate_report.py` (僅內容變動時更新 `index.html` 且**自動推送到 GitHub**)。
- **結算帶日期週報**: `uv run generate_report.py --weekly` (產生週報存檔並**自動同步**)。
- **手動同步**: 仍可直接執行 `./sync.sh` 進行強制同步。

## 📋 分析規範

- **重點議題**: 須包含邏輯推演，而非僅列出結論。
- **提及標的**: 需標註多空觀點 (`Bullish`/`Bearish`/`Neutral`) 與具體理由 (`rationale`)。
- **格式**: 為求專業感，嚴禁在報告內容中使用 Emoji。