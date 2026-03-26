# 財經週報系統操作手冊 (Finance Report System SOP)

## 系統架構簡介
本系統採用「自動化資料庫」與「AI 分析」分離的架構。
*   **資料來源**: `data/database.json` (由 `daily_update.py` 自動維護)
*   **分析結果**: `data/analysis/{video_id}.json`
*   **最終報表**: `report/latest_report.html` (由 `generate_report.py` 生成)

---

## Agent 指令集 (Command Set)

### 1. 每日更新與啟動 (`@daily_update`)
**時機**: 每日早晨，或使用者要求「更新片單」時。
**對象**: 股癌、財報狗、財女珍妮、M觀點、**兆華與股惑仔**。
**動作**:
1.  **更新資料庫**: 執行 `uv run daily_update.py`。
2.  **檢查狀態**:
    *   若無新影片 (Pending = 0)：回報「今日無新影片，目前資料庫已同步」。
    *   **若有新影片 (Pending > 0)**：
        *   報告新增數量（例如：「發現 3 部新影片」）。
        *   **[自動觸發]**: 立即執行 **`@analyze_next`** 的流程（搜尋 -> 分析 -> 存檔 -> 更新報表）。
        *   完成第一集後，主動詢問使用者：「還有 X 部影片待處理，是否繼續？」

### 2. 分析下一集 (`@analyze_next` 或 「繼續」)
**時機**: 使用者要求「開始分析」、「分析下一集」或系統閒置時。
**動作**:
1.  **獲取任務**: 執行以下 Python 指令獲取一部待處理影片：
    ```python
    from storage import Storage
    pending = Storage().get_pending_videos()
    if pending:
        v = pending[0]
        print(f"TARGET_VIDEO_ID:{v.id}")
        print(f"TARGET_VIDEO_TITLE:{v.title}")
    else:
        print("NO_PENDING_VIDEOS")
    ```
2.  **判斷狀態**:
    *   若輸出 `NO_PENDING_VIDEOS`: 回報「目前沒有待分析的影片」。
    *   若取得 `TARGET_VIDEO_ID`: 進入步驟 3。
3.  **執行深度分析 (Core AI Task)**:
    *   **策略**: 使用 `google_web_search` 搜尋 `TARGET_VIDEO_ID` + "逐字稿" 或 "重點摘要"。
    *   **深度彙整**: 除了基本重點，須額外挖掘以下維度：
        *   **🌍 總體環境 (Macro Outlook)**: 總經趨勢、市場情緒、大環境變動。
        *   **⚠️ 風險因素 (Risk Factors)**: 產業威脅、個股風險、觀察指標。
        *   **💬 關鍵金句 (Quotes)**: 節錄最具代表性的核心結論。
4.  **存檔**:
    *   將分析結果整理為 JSON 物件 (Python Dict)：
    ```python
    {
        "key_points": ["重點1", "重點2"...],
        "macro_outlook": ["觀點1"...],
        "targets": [{"code": "2330", "name": "台積電", "view": "多", "rationale": "..."}],
        "risk_factors": ["風險1"...],
        "quotes": "核心金句"
    }
    ```
    *   執行 `Storage().save_analysis("TARGET_VIDEO_ID", content)`。
5.  **更新報表 (Conditional Update)**:
    *   執行 `uv run generate_report.py`。
    *   系統會自動判斷內容是否變動，若有變動則更新 `latest_report.html`。
    *   回報「已完成 [影片標題] 的分析與歸檔」。

### 3. 發布與結算週報 (`@publish`)
**時機**: 週末或分析工作告一段落，使用者要求「結算週報」或「同步報告」。
**動作**:
1.  **結算週報**: 執行 `uv run generate_report.py --weekly`。
    *   此舉會更新 `latest_report.html` 並產出一份帶日期的存檔 `report/weekly_finance_report_YYYY-MM-DD.html`。
2.  **發布與同步**: 執行 `./sync.sh` (Git Commit & Push)。

---

## 分析規範 (Analysis Guidelines)
*   **重點議題**: 須包含邏輯推演，而非僅列出結論。
*   **提及標的**:
    *   `view`: 看多 (Bullish)、看空 (Bearish)、中性 (Neutral)。
    *   `rationale`: 必須說明「為什麼」，例如「營收創新高」、「技術面破線」等。
*   **格式**: 嚴禁使用 Emoji。

## 疑難排解
*   若 `database.json` 損毀，請檢查 JSON 格式是否正確。
*   若爬蟲失敗，可能是 `yt-dlp` 需要更新 (`pip install -U yt-dlp`)。
