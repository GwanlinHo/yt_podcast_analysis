import yt_dlp
import datetime
import os

# 目標頻道清單
CHANNELS = [
    {"name": "股癌", "url": "https://www.youtube.com/@Gooaye/videos"},
    {"name": "財報狗", "url": "https://www.youtube.com/@statementdog_official/videos"},
    {"name": "財女珍妮", "url": "https://www.youtube.com/@jcinsight/videos"},
    {"name": "M觀點", "url": "https://www.youtube.com/@miulaviewpoint/videos"}
]

OUTPUT_FILE = "videolist.md"

def main():
    # 設定日期範圍 (過去 7 天)
    today = datetime.datetime.now()
    start_date = today - datetime.timedelta(days=7)
    start_date_str = start_date.strftime('%Y%m%d')
    
    print(f"🔍 開始搜尋 {start_date.strftime('%Y-%m-%d')} 之後發布的影片...")

    # yt-dlp 設定
    # 拆分兩步：1. 列表 (flat) 2. 詳情
    
    ydl_opts_list_base = {
        'quiet': True,
        'ignoreerrors': True,
        'playlistend': 10,
        'extract_flat': True,
        'js_runtime': 'node',
    }

    ydl_opts_detail_base = {
        'quiet': True,
        'ignoreerrors': True,
        'js_runtime': 'node',
    }

    md_lines = []
    md_lines.append(f"# 最近一週 YouTube 影片清單")
    md_lines.append(f"更新時間：{today.strftime('%Y/%m/%d %H:%M')}")
    md_lines.append(f"統計期間：{start_date.strftime('%Y/%m/%d')} 至 {today.strftime('%Y/%m/%d')}\n")

    for channel in CHANNELS:
        print(f"📺 正在檢查頻道：{channel['name']} ...")
        
        # 準備 URL
        base_url = channel['url'].replace('/videos', '').replace('/streams', '').rstrip('/')
        target_urls = [f"{base_url}/videos", f"{base_url}/streams"]
        
        found_videos = []
        seen_ids = set()

        for target_url in target_urls:
            # print(f"   🔎 掃描: {target_url} ...")
            try:
                # 每次建立新的 instance 以避免狀態干擾
                with yt_dlp.YoutubeDL(ydl_opts_list_base) as ydl_list:
                    result = ydl_list.extract_info(target_url, download=False)
                
                # 修正: 檢查 result 是否為 None
                if result is None or 'entries' not in result:
                    continue

                entries = list(result['entries'])
                
                for i, entry in enumerate(entries):
                    if not entry:
                        continue
                    
                    video_id = entry.get('id')
                    if not video_id:
                        continue

                    if video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)

                    title = entry.get('title', '無標題')
                    url = entry.get('url')
                    
                    if not url or 'youtube.com' not in url:
                        url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    upload_date = entry.get('upload_date')
                    
                    if not upload_date:
                        try:
                            with yt_dlp.YoutubeDL(ydl_opts_detail_base) as ydl_detail:
                                info = ydl_detail.extract_info(url, download=False)
                            if info:
                                upload_date = info.get('upload_date')
                                if info.get('title'):
                                    title = info.get('title')
                        except Exception as e:
                            print(f"      ⚠️ 無法讀取詳情 ({title}): {e}")
                            continue
                    
                    if upload_date and upload_date >= start_date_str:
                        found_videos.append({
                            'date': upload_date,
                            'title': title,
                            'url': url
                        })

            except Exception as e:
                print(f"   ❌ 掃描 {target_url} 時發生錯誤: {e}")

        if found_videos:
            found_videos.sort(key=lambda x: x['date'], reverse=True)
            md_lines.append(f"## {channel['name']}")
            for v in found_videos:
                md_lines.append(f"- [{v['title']}]({v['url']})")
            md_lines.append("") 
            print(f"   🎉 共找到 {len(found_videos)} 部新影片")
        else:
            print(f"   ℹ️ 無新影片")

    # 寫入檔案
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))
        print(f"\n✨ 完成！清單已儲存至：{os.path.abspath(OUTPUT_FILE)}")
    except IOError as e:
        print(f"❌ 寫入檔案失敗: {e}")

if __name__ == "__main__":
    main()
