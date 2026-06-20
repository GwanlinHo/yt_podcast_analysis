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
**對象**: 股癌、財報狗、財女珍妮、M觀點、兆華與股惑仔。
**動作**:
1.  **更新資料庫**: 執行 `uv run daily_update.py`。
2.  **檢查狀態**:
    *   若無新影片 (Pending = 0)：回報「今日無新影片，目前資料庫已同步」。
    *   若有新影片 (Pending > 0)：
        *   報告新增數量（例如：「發現 3 部新影片」）。
        *   [自動觸發]: 立即執行 `@analyze_next` 的批次流程（取視窗內最新一批 -> 逐部搜尋/分析/存檔 -> 最後一次性更新報表並同步）。
        *   cron 為非互動環境，不需詢問使用者是否繼續;本批(上限 8 部)處理完即結束，剩餘的留待下次 cron 自動接續。

### 2. 分析待處理影片 (`@analyze_next` 或 「繼續」)
**時機**: 使用者要求「開始分析」、「分析下一集」或系統閒置時(cron 每次執行)。

**重要原則 — 批次處理且只處理「報告視窗內」影片**:
週報只顯示最近 7 天的影片,因此分析器只處理視窗內、且**最舊優先**(即將滑出視窗者先搶救)的待分析影片,報告才會有內容。視窗外的舊積壓刻意放棄(`get_pending_in_window` 不會回傳),不要去分析它們。單次 cron 以 `limit`(預設 8 部)為上限,逐部分析完後**一次性**重新生成報告。

**動作**:
1.  **獲取本批任務清單**: 執行以下 Python 指令,取得視窗內、最舊優先、最多 8 部待處理影片：
    ```python
    from storage import Storage
    batch = Storage().get_pending_in_window()  # 近7天、最舊優先、上限8
    if batch:
        for v in batch:
            print(f"TARGET:{v.id}\t{v.title}\t{v.url}")
    else:
        print("NO_PENDING_IN_WINDOW")
    ```
2.  **判斷狀態**:
    *   若輸出 `NO_PENDING_IN_WINDOW`: 回報「報告視窗內無待分析影片,目前資料庫已同步」,**跳到步驟 5 仍執行一次報表生成以確保同步**。
    *   若取得 `TARGET:` 清單: **逐一(for-loop)**對清單中每一部影片執行步驟 3-4(深度分析 + 存檔)。全部完成後再進入步驟 5。
3.  **執行深度分析 (Core AI Task) — 對清單中每一部影片**:
    *   **來源 0(podcast 影片,最優先)**: 若 `Storage().get_transcript(video_id)` 有內容(即 `data/transcripts/<id>.txt` 存在),代表 ASR 前置步驟(`asr_prestep.py`)已先把該集 podcast 音檔轉成逐字稿。**直接讀這份逐字稿忠實萃取分析,不要再做 yt-dlp/WebSearch**。財報狗、M觀點、兆華與股惑仔 已改為 podcast RSS 來源,逐字稿一律由前置步驟提供(ASR 不在 claude 執行期間做,以免 OOM)。
    *   **以下雙來源策略僅適用於 YouTube 來源影片(財女珍妮、股癌)(務必先抓真實素材，嚴禁靠標題或主題新聞臆測創作者觀點)**:
        1.  **首選 yt-dlp 字幕**: 直接抓該影片的 YouTube 中文自動字幕。實測可用指令(需 Node runtime + 官方遠端元件):
            ```bash
            export PATH=/home/pi/.config/nvm/versions/node/v22.17.0/bin:$PATH
            uv run yt-dlp --js-runtimes node --remote-components ejs:github \
              --skip-download --write-auto-subs --sub-langs "zh" --sub-format "vtt" \
              -o "/tmp/yt_subs/%(id)s.%(ext)s" "<影片URL>"
            ```
            (專案 venv 的 yt-dlp 已釘為新版,故用 `uv run yt-dlp`;若 venv 版本又過舊抓不到,退而改用 `uvx yt-dlp@latest` 相同參數。)
            抓到後清掉 vtt 時間軸與重複行,得到純文字逐字稿,據此忠實萃取。
        2.  **備援:他人忠實整理(限有公開逐字稿/筆記的節目)**: 若該影片**無字幕**或抓取失敗,改用 WebSearch 找該集的**逐字稿或忠實重點整理**。可信來源範例:
            - **股癌(Gooaye)**: 有專門的逐字稿/筆記站,逐集發布且忠實反映謝孟恭發言 —— `vocus.cc/@read_gooaye`(閱讀股癌)、`yasac.substack.com`(呀沙係)、`socialworkerdaily.com`。搜尋「股癌 EP編號 重點整理 / 逐字稿」即可,並用 WebFetch 取全文。
            - 其他節目若能找到**第三方逐字稿/詳細筆記**亦可採用;但這必須是「忠實記錄該集內容」的整理,不是同主題的市場新聞。
        3.  **兩者皆無真實素材時**: **跳過該片、不要存檔**(維持 pending,留待之後素材出現再由 cron 重試)。**絕不可用主題新聞或標題自行編造創作者的觀點、選股與金句**;同主題的市場新聞 ≠ 該集逐字稿,不可拿來冒充創作者觀點。
    *   **無字幕、無逐字稿、無忠實筆記的純音訊節目**(財報狗、M觀點、兆華與股惑仔 podcast)需另以語音辨識(ASR)取得逐字稿,屬獨立工作項,未就緒前這些片維持 pending / 逾期 skipped。
    *   **深度彙整**: 根據逐字稿,除了基本重點，須額外挖掘以下維度：
        *   **總體環境 (Macro Outlook)**: 總經趨勢、市場情緒、大環境變動。
        *   **風險因素 (Risk Factors)**: 產業威脅、個股風險、觀察指標。
        *   **關鍵金句 (Quotes)**: 節錄最具代表性的核心結論。
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
5.  **更新報表與自動同步 (本批全部分析完後，只執行一次)**:
    *   執行 `uv run generate_report.py`。
    *   系統會自動判斷內容是否變動，若有變動則更新 `latest_report.html` 及其複本 `index.html`，並自動執行 `./sync.sh` 同步至 GitHub。
    *   回報本批成果:「本批已分析 N 部影片並同步;視窗內尚餘 M 部待處理(下次 cron 續處理)」。M 可用 `len(Storage().get_pending_in_window(limit=None))` 取得。

### 3. 發布與結算週報 (`@publish`)
**時機**: 週末或分析工作告一段落，使用者要求「結算週報」或「同步報告」。
**動作**:
1.  **結算週報**: 執行 `uv run generate_report.py --weekly`。
    *   此舉會更新 `latest_report.html` 並產出一份帶日期的存檔 `report/history/weekly_finance_report_YYYY-MM-DD.html`。
    *   [新行為]: 此指令也會自動觸發 `./sync.sh` 完成發布。
2.  **確認狀態**: 報告完成並檢查 GitHub 更新狀態。

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
*   若抓字幕時報「no subtitles / n challenge solving failed」: 本機 yt-dlp 版本過舊或缺 JS runtime。請改用 `uvx yt-dlp@latest --js-runtimes node --remote-components ejs:github`(見上方雙來源策略)。並非每支影片都有字幕,無字幕者改走 WebSearch 備援。
*   影片狀態有三種: `pending`(待分析)、`analyzed`(已分析)、`skipped`(逾期無資料略過)。`daily_update.py` 每次執行會呼叫 `evict_stale_pending()`,把發布日超過一週、仍找不到任何可分析素材(雙來源皆失敗)的 pending 影片標記為 `skipped`,踢出待分析清單、不再重試;紀錄保留,全量知識庫顯示為「無資料略過」。
