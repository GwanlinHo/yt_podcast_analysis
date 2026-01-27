# 財經影片週報生成流程 (Finance Video Weekly Report Workflow)

## 1. 觸發條件 (Trigger)
當使用者要求「整理影片重點」、「生成財經週報」或針對 `videolist.md` 進行分析並要求輸出 HTML 時。

## 2. 執行步驟 (Execution Steps)
1.  **讀取清單**：讀取 `videolist.md` 獲取最新的影片連結與標題。
2.  **內容獲取**：
    *   使用 `web_fetch` 讀取影片資訊、摘要或逐字稿。
    *   若直接讀取失敗，使用 `google_web_search` 搜尋該集數的重點整理（關鍵字如：「股癌 EPxxx 重點」、「財報狗 xxx 摘要」）。
3.  **分析歸納**：針對每一集影片進行以下處理：
    *   **重點議題摘要**：提取該集探討的主要財經議題，需具備邏輯性與脈絡。
    *   **提及標的整理**：提取文中提及的股票、ETF 或商品，並標註代碼、多空看法及情境。
4.  **生成報告**：依據下方的 HTML 格式規範輸出檔案至 `report/` 目錄下，檔名格式為 `weekly_finance_report_YYYY-MM-DD.html`。

## 3. 輸出格式規範 (HTML Format Specification)

*   **嚴格禁止使用表情符號 (NO EMOJIS)**：所有內容、標題、圖示位置均不得出現表情符號。
*   HTML 檔案需包含 CSS 樣式以確保閱讀體驗，結構如下：

*   **Header**: 包含標題（如「財經 YouTube 影片重點彙整」）與生成日期。
*   **Container**: 主要內容區塊。
*   **Creator Section**: 每個創作者一個區塊（Card 樣式）。
    *   **Creator Name**: 創作者名稱（H2）。
    *   **Episode Block**: 每一集一個子區塊。
        *   **Episode Title**: 影片標題與連結（H3）。
        *   **Summary Section**:
            *   標題：「📌 重點議題摘要」
            *   內容：條列式重點（ul/li）。
        *   **Targets Section**:
            *   標題：「🎯 提及標的」
            *   表格（Table）：包含欄位 [代碼/名稱]、[多空/觀點]、[提及情境說明]。

### 範例 CSS 風格 (參考)
*   使用乾淨、現代的風格 (無襯線字體)。
*   標的表格需有邊框，表頭背景色需區隔。
*   多空觀點可用顏色標示（如：看多/紅、看空/綠、中性/灰）。
*   **響應式設計 (RWD)**：
    *   必須包含 `@media screen and (max-width: 768px)` 設定。
    *   在手機版面下，`table` 必須轉換為卡片式 (Card) 佈局：
        *   隱藏 `thead`。
        *   `tr` 轉為獨立區塊 (Block)，加上邊框與圓角。
        *   `td` 轉為區塊，第一欄 (標的) 作為卡片標題，第二欄 (觀點) 與第三欄 (說明) 依序排列。
        *   使用 `::before` 偽元素補上「觀點：」、「說明：」等標籤，確保手機閱讀清晰。

---
