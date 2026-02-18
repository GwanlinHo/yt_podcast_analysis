import yt_dlp
import datetime
import os
from storage import Storage, Video

# 目標頻道清單 (從 fetch_yt_list.py 遷移)
CHANNELS = [
    {"name": "股癌", "url": "https://www.youtube.com/@Gooaye/videos"},
    {"name": "財報狗", "url": "https://www.youtube.com/@statementdog_official/videos"},
    {"name": "財女珍妮", "url": "https://www.youtube.com/@jcinsight/videos"},
    {"name": "M觀點", "url": "https://www.youtube.com/@miulaviewpoint/videos"}
]

def get_week_start_date() -> datetime.datetime:
    """取得 7 天前的日期，確保覆蓋週末"""
    today = datetime.datetime.now()
    start = today - datetime.timedelta(days=7)
    return start

def main():
    db = Storage()
    
    # 設定日期範圍: 本週一開始到今天
    today = datetime.datetime.now()
    start_date = get_week_start_date()
    start_date_str = start_date.strftime('%Y%m%d')
    
    print(f"🔍 開始更新影片資料庫...")
    print(f"📅 搜尋範圍: {start_date.strftime('%Y-%m-%d')} ({start_date_str}) 起")

    # yt-dlp 設定
    ydl_opts_list = {
        'quiet': True,
        'ignoreerrors': True,
        'playlistend': 10,  # 檢查最近 10 部應該足夠覆蓋一週
        'extract_flat': True,
        'js_runtime': 'node',
    }

    ydl_opts_detail = {
        'quiet': True,
        'ignoreerrors': True,
        'js_runtime': 'node',
    }

    new_videos_count = 0

    for channel in CHANNELS:
        print(f"📺 正在檢查頻道：{channel['name']} ...")
        
        base_url = channel['url'].replace('/videos', '').replace('/streams', '').rstrip('/')
        target_urls = [f"{base_url}/videos", f"{base_url}/streams"]
        
        seen_ids = set()

        for target_url in target_urls:
            try:
                with yt_dlp.YoutubeDL(ydl_opts_list) as ydl:
                    result = ydl.extract_info(target_url, download=False)
                
                if result is None or 'entries' not in result:
                    continue

                entries = list(result['entries'])
                
                for entry in entries:
                    if not entry:
                        continue
                    
                    video_id = entry.get('id')
                    if not video_id or video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)

                    title = entry.get('title', '無標題')
                    url = entry.get('url')
                    if not url or 'youtube.com' not in url:
                        url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    upload_date = entry.get('upload_date')
                    
                    # 若 flat mode 沒抓到日期，嘗試抓詳情 (但通常會有)
                    if not upload_date:
                        try:
                            with yt_dlp.YoutubeDL(ydl_opts_detail) as ydl_detail:
                                info = ydl_detail.extract_info(url, download=False)
                            if info:
                                upload_date = info.get('upload_date')
                                if info.get('title'):
                                    title = info.get('title')
                        except Exception as e:
                            print(f"      ⚠️ 無法讀取詳情 ({title}): {e}")
                            continue

                    # 過濾日期: 只抓本週的影片
                    if upload_date and upload_date >= start_date_str:
                        video = Video(
                            id=video_id,
                            title=title,
                            url=url,
                            date=upload_date,
                            channel=channel['name']
                        )
                        
                        if db.upsert_video(video):
                            print(f"   [New] {title} ({upload_date})")
                            new_videos_count += 1
                        else:
                            # print(f"   [Skip] {title} (Exists)")
                            pass

            except Exception as e:
                print(f"   ❌ 掃描 {target_url} 時發生錯誤: {e}")

    db.save_database()
    print(f"\n✨ 更新完成！新增 {new_videos_count} 部影片。")

    # 這裡未來會觸發 generate_report.py
    # os.system("uv run generate_report.py")

if __name__ == "__main__":
    main()
