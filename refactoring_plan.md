# 財經週報系統重構計畫 (Dynamic Finance Weekly Report Refactoring Plan)

## 設計理念 (Design Philosophy)
本系統採行**「自動化骨架，AI 靈魂」**的分層架構，旨在將非認知型任務剝離，最大化 AI 的高價值產出。

*   **自動化骨架 (Python Script)**：負責所有確定性、重複性任務，包括資料爬取、檔案 I/O、HTML 渲染、版本控制與排程管理。此層級不依賴 AI 推論。
*   **AI 靈魂 (Gemini Agent)**：專注於非結構化資料的處理，包括影片內容的語意理解、重點摘要、情緒判斷與投資標的提取。AI 僅在「內容生成」階段介入，並將結果注入系統。

## 專案目標
將原本「每週一次批次處理」的流程，轉型為「每日更新、持續整合」的動態報表系統。
- **即時性**：每日早晨更新片單，隨時可查看最新報告。
- **分散負載**：將分析工作分散至週間，避免週末算力瓶頸。
- **彈性**：支援「待分析」與「已分析」內容並存於同一份報告中。

## 系統架構

### 1. 檔案結構變更
```text
yt_analysis/
├── data/
│   ├── database.json          # [New] 核心資料庫 (儲存影片 Metadata 與狀態)
│   └── analysis/              # [New] 分析結果存檔區
│       ├── {video_id}.json    # 單集影片的分析數據
│       └── ...
├── report/
│   ├── latest_report.html     # [New] 本週即時報告 (每日更新)
│   └── history/               # [New] 歷史報告歸檔
├── daily_update.py            # [New] 每日排程腳本 (Fetch + Render)
├── generate_report.py         # [New] 報告生成核心邏輯
├── storage.py                 # [New] 資料存取層封裝
└── GEMINI.md                  # [Update] Agent SOP 更新
```

### 2. 資料流 (Data Flow)
1.  **Cron (每日)** -> `daily_update.py` -> 更新 `database.json` -> 觸發 `generate_report.py` (包含新影片佔位符) -> 更新 `latest_report.html`。
2.  **User/Agent (週間)** -> 讀取 `database.json` (Pending) -> 分析影片 -> 寫入 `data/analysis/{id}.json` -> 更新 `database.json` (Done) -> 觸發 `generate_report.py` -> 更新 `latest_report.html`。
3.  **Cron (週末)** -> 歸檔 `latest_report.html` -> 重置週次。

---

## 任務清單 (Task Breakdown)

### Phase 1: 基礎建設與資料層 (Infrastructure & Data Layer)
- [ ] **1.1 初始化目錄結構**
    - 建立 `data/`, `data/analysis/`, `report/history/` 目錄。
- [ ] **1.2 實作資料存取模組 (`storage.py`)**
    - 定義 `Video` 資料結構 (Dataclass)。
    - 實作 `load_database()`, `save_database()`。
    - 實作 `save_analysis(video_id, content)`, `get_analysis(video_id)`。
    - 實作 `upsert_video()` 邏輯 (避免重複，更新狀態)。

### Phase 2: 每日更新機制 (Daily Update Mechanism)
- [ ] **2.1 改造爬蟲邏輯 (`fetch_yt_list.py` -> `daily_update.py`)**
    - 修改 `fetch_yt_list.py` 的邏輯，使其不再直接輸出 MD，而是呼叫 `storage.py` 更新資料庫。
    - 加入「日期過濾」：只抓取本週 (週一至今日) 的影片。
- [ ] **2.2 整合自動化流程**
    - 確保腳本能被 Crontab 呼叫 (處理路徑問題)。

### Phase 3: 報告生成引擎 (Report Generation Engine)
- [ ] **3.1 設計 HTML 模板**
    - 建立支援「已分析 (完整內容)」與「待分析 (僅標題/連結)」兩種狀態的 HTML 結構。
    - 確保 RWD 手機版顯示正常。
- [ ] **3.2 實作生成器 (`generate_report.py`)**
    - 從 `database.json` 讀取本週所有影片。
    - 若狀態為 `analyzed`，讀取對應 JSON 並填入模板。
    - 若狀態為 `pending`，填入「待處理」佔位符。
    - 輸出 `report/latest_report.html`。

### Phase 4: Agent 整合與歸檔 (Agent Integration & Automation)
- [ ] **4.1 更新 Agent SOP (`GEMINI.md`)**
    - 新增指令：「分析下一集」 (讀 DB -> 搜 -> 寫 JSON -> 重新生成 HTML)。
    - 新增指令：「本週歸檔」 (Move HTML -> Push Git)。
- [ ] **4.2 建立/更新執行腳本 (`sync.sh` / `run_daily.sh`)**
    - 方便使用者一鍵執行或設定 Crontab。

---

## 執行記錄
*   2026-02-02: 計畫書建立。
