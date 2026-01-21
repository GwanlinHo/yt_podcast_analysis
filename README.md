# YouTube Tech & Podcast Analysis

這是一個用於自動化追蹤與分析 YouTube 財經/Podcast 頻道的工具組。

## 功能

- **fetch_yt_list.py**: 自動抓取指定頻道（如股癌、財報狗等）過去一週發布的影片，並產生 Markdown 報告。
- **get_video_details.py**: 取得特定影片的詳細資訊（標題、描述、章節）。

## 安裝與使用

1. 安裝相依套件：
   ```bash
   pip install -r requirements.txt
   ```

2. 執行抓取腳本：
   ```bash
   python fetch_yt_list.py
   ```
   執行後將產生 `videolist.md` 報告。

## 輸出範例

產生的 `videolist.md` 會包含影片標題、連結與發布日期。
