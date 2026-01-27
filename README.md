# YouTube Tech & Podcast Analysis

這是一個用於自動化追蹤與分析 YouTube 財經/Podcast 頻道的工具組。

## 功能

- **fetch_yt_list.py**: 自動抓取指定頻道（如股癌、財報狗、財女珍妮、M觀點等）過去一週發布的影片，並產生 Markdown 清單 (`videolist.md`)。
- **財經週報生成**: 透過 Gemini Agent 分析 `videolist.md` 中的影片內容，自動彙整重點議題與提及標的，生成 HTML 週報。

## 專案結構

- `fetch_yt_list.py`: 影片清單抓取腳本。
- `videolist.md`: 最近一週的影片清單（自動生成）。
- `report/`: 存放生成的 HTML 財經週報。
- `GEMINI.md`: 記錄 Agent 的標準作業流程 (SOP) 與輸出規範。

## 安裝與使用

1. 安裝相依套件：
   ```bash
   pip install -r requirements.txt
   ```

2. 執行抓取腳本：
   ```bash
   python fetch_yt_list.py
   ```

3. 生成分析報告：
   請呼叫 Gemini Agent 並下達指令：「整理影片重點」或「生成財經週報」。Agent 將依據 `GEMINI.md` 中的規範執行分析並輸出 HTML 檔案至 `report/` 目錄。

## 輸出範例

- **影片清單**: `videolist.md` (Markdown 格式)
- **財經週報**: `report/weekly_finance_report_YYYY-MM-DD.html` (HTML 格式，不含表情符號)