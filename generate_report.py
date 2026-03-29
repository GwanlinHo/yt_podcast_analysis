import os
import json
import datetime
import argparse
import hashlib
import subprocess
from storage import Storage, Video

OUTPUT_FILE = "report/latest_report.html"

def get_week_range():
    """取得 7 天前與今天的日期字串 (YYYYMMDD)"""
    today = datetime.datetime.now()
    start = today - datetime.timedelta(days=7)
    return start.strftime('%Y%m%d'), today.strftime('%Y%m%d')

def generate_css():
    return """
    <style>
        :root {
            --primary-color: #2c3e50;
            --accent-color: #3498db;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333;
            --border-color: #e9ecef;
            --bullish-color: #e74c3c;
            --bearish-color: #27ae60;
            --neutral-color: #7f8c8d;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
        }
        h1 { margin-bottom: 10px; color: var(--primary-color); }
        .meta { color: #666; font-size: 0.9em; }
        
        .creator-section {
            background: var(--card-bg);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 30px;
            padding: 25px;
            border-top: 4px solid var(--accent-color);
        }
        .creator-title {
            margin-top: 0;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .episode-block {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px dashed var(--border-color);
        }
        .episode-block:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .episode-title {
            font-size: 1.2em;
            margin-bottom: 15px;
        }
        .episode-title a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: bold;
        }
        .episode-title a:hover {
            color: var(--accent-color);
            text-decoration: underline;
        }
        .pending-badge {
            display: inline-block;
            background: #ffeeba;
            color: #856404;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 10px;
            vertical-align: middle;
        }
        
        .summary-section, .targets-section, .macro-section, .risk-section {
            margin-top: 15px;
        }
        .section-title {
            font-weight: bold;
            color: var(--accent-color);
            margin-bottom: 10px;
            display: block;
        }
        .quote-box {
            background: #f1f3f5;
            padding: 15px;
            border-left: 4px solid var(--primary-color);
            font-style: italic;
            margin: 15px 0;
            color: #555;
        }
        .risk-item {
            color: #d63301;
            font-weight: 500;
        }
        ul { padding-left: 20px; }
        li { margin-bottom: 8px; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.95em;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        th {
            background-color: #f1f3f5;
            font-weight: 600;
        }
        
        .view-bull { color: var(--bullish-color); font-weight: bold; }
        .view-bear { color: var(--bearish-color); font-weight: bold; }
        .view-neutral { color: var(--neutral-color); font-weight: bold; }
        
        .disclaimer-section {
            margin-top: 50px;
            padding: 20px;
            background: #fff;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.85em;
            color: #666;
            line-height: 1.8;
        }
        .disclaimer-title {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 10px;
            display: block;
            text-align: center;
            font-size: 1.1em;
        }
        
        /* Mobile Responsive Table to Card */
        @media screen and (max-width: 768px) {
            table, thead, tbody, th, td, tr {
                display: block;
            }
            thead tr {
                position: absolute;
                top: -9999px;
                left: -9999px;
            }
            tr {
                border: 1px solid var(--border-color);
                border-radius: 8px;
                margin-bottom: 15px;
                padding: 10px;
                background: #fff;
            }
            td {
                border: none;
                border-bottom: 1px solid #eee;
                position: relative;
                padding-left: 50%;
                padding-top: 8px;
                padding-bottom: 8px;
            }
            td:last-child { border-bottom: none; }
            
            td:before {
                position: absolute;
                top: 8px;
                left: 10px;
                width: 45%;
                padding-right: 10px;
                white-space: nowrap;
                font-weight: bold;
                color: #666;
            }
            
            /* Specific labels for each column */
            td:nth-of-type(1) { /* Name/Code */
                padding-left: 10px;
                font-size: 1.1em;
                font-weight: bold;
                color: var(--primary-color);
                background: #f8f9fa;
                margin: -10px -10px 10px -10px;
                border-bottom: 1px solid var(--border-color);
                border-radius: 8px 8px 0 0;
            }
            td:nth-of-type(1):before { content: ""; }
            
            td:nth-of-type(2):before { content: "觀點"; }
            td:nth-of-type(3):before { content: "說明"; }
        }
    </style>
    """

def render_targets_table(targets):
    if not targets:
        return "<p>本集未特別提及具體投資標的。</p>"
    
    html = """
    <table>
        <thead>
            <tr>
                <th style="width: 25%">標的</th>
                <th style="width: 15%">觀點</th>
                <th>情境說明</th>
            </tr>
        </thead>
        <tbody>
    """
    for t in targets:
        # Determine view class
        view_class = "view-neutral"
        view_text = t.get('view', '中性')
        if "多" in view_text: view_class = "view-bull"
        elif "空" in view_text: view_class = "view-bear"
        
        html += f"""
            <tr>
                <td>{t.get('name', '')} ({t.get('code', '')})</td>
                <td><span class="{view_class}">{view_text}</span></td>
                <td>{t.get('rationale', '')}</td>
            </tr>
        """
    html += "</tbody></table>"
    return html

def generate_disclaimer():
    return """
    <div class="disclaimer-section">
        <span class="disclaimer-title">💡 免責聲明與版權說明</span>
        本報告內容係透過 AI 萃取各內容創作者之公開分享資訊彙整而成，僅供參考，不代表本系統之立場，亦不構成任何投資建議。投資人應保持獨立思考，審慎評估風險，並對其投資行為自負盈虧。
        <br><br>
        本系統旨在協助使用者快速掌握資訊趨勢，並非取代原創作者之影片。創作者的每一份支持都是其持續產出優質內容的動力，<strong>強烈建議使用者點擊報告中的連結，前往創作者的原始頻道觀看完整影片並給予訂閱與支持。</strong>
    </div>
    """

def get_content_hash(channels, db):
    """計算影片內容的雜湊值，用於判斷內容是否變動"""
    content_data = []
    for channel, videos in channels.items():
        for v in videos:
            analysis = db.get_analysis(v.id) if v.status == "analyzed" else None
            content_data.append({
                "id": v.id,
                "status": v.status,
                "analysis": analysis
            })
    return hashlib.md5(json.dumps(content_data, sort_keys=True).encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="產生財經影片重點彙整報表")
    parser.add_argument("--weekly", action="store_true", help="產生帶日期的週報存檔 (weekly_finance_report_YYYY-MM-DD.html)")
    parser.add_argument("--force", action="store_true", help="強制更新 latest_report.html，不論內容是否變動")
    args = parser.parse_args()

    db = Storage()
    start_str, end_str = get_week_range()
    
    # Get videos for this week
    videos = db.get_videos_by_date_range(start_str, end_str)
    
    # Group by channel
    channels = {}
    for v in videos:
        if v.channel not in channels:
            channels[v.channel] = []
        channels[v.channel].append(v)

    # 條件式檢查：內容是否有變動
    current_hash = get_content_hash(channels, db)
    hash_file = "data/.report_hash"
    old_hash = ""
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            old_hash = f.read().strip()

    if current_hash == old_hash and not args.force and not args.weekly:
        print("💡 內容無變動，跳過報表更新。")
        return

    # Start HTML
    now = datetime.datetime.now()
    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>財經 YouTube 影片重點彙整</title>
    {generate_css()}
</head>
<body>
    <div class="container">
        <header>
            <h1>財經 YouTube 影片重點彙整</h1>
            <div class="meta">
                統計期間：{start_str} 至 {end_str}<br>
                生成時間：{now.strftime('%Y/%m/%d %H:%M')}
            </div>
        </header>
    """

    if not channels:
        html += "<p style='text-align:center'>本週尚未有新影片。</p>"
    
    for channel_name, video_list in channels.items():
        html += f"""
        <div class="creator-section">
            <h2 class="creator-title">{channel_name}</h2>
        """
        
        for v in video_list:
            analysis = None
            if v.status == "analyzed":
                analysis = db.get_analysis(v.id)
            
            html += f"""
            <div class="episode-block">
                <div class="episode-title">
                    <a href="{v.url}" target="_blank">{v.title}</a>
                    {f'<span class="pending-badge">待分析</span>' if v.status == 'pending' else ''}
                </div>
            """
            
            if analysis:
                # Render Macro Outlook (New)
                if analysis.get('macro_outlook'):
                    html += """<div class="macro-section"><span class="section-title">🌍 總體環境與趨勢觀點</span><ul>"""
                    for point in analysis.get('macro_outlook', []):
                        html += f"<li>{point}</li>"
                    html += "</ul></div>"

                # Render Summary
                html += """<div class="summary-section"><span class="section-title">📝 重點議題摘要</span><ul>"""
                for point in analysis.get('key_points', []):
                    html += f"<li>{point}</li>"
                html += "</ul></div>"
                
                # Render Targets
                html += """<div class="targets-section"><span class="section-title">📊 提及標的</span>"""
                html += render_targets_table(analysis.get('targets', []))
                html += "</div>"

                # Render Risks (New)
                if analysis.get('risk_factors'):
                    html += """<div class="risk-section"><span class="section-title">⚠️ 風險警示與觀察指標</span><ul>"""
                    for risk in analysis.get('risk_factors', []):
                        html += f'<li class="risk-item">{risk}</li>'
                    html += "</ul></div>"

                # Render Quote (New)
                if analysis.get('quotes'):
                    html += f'<div class="quote-box">「{analysis.get("quotes")}」</div>'
            else:
                html += """<div class="summary-section"><p style="color:#999; font-style:italic;">系統尚未分析此影片內容。</p></div>"""
                
            html += "</div>" # End episode-block
            
        html += "</div>" # End creator-section
        
    html += generate_disclaimer()
    html += """
    </div>
</body>
</html>
    """

    # Write to latest_report.html
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # 同時寫入根目錄的 index.html 以支援 GitHub Pages
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    
    # 儲存雜湊值
    with open(hash_file, 'w') as f:
        f.write(current_hash)
    
    print(f"✨ 報告已更新：{OUTPUT_FILE}")
    print(f"🌐 靜態網頁已同步：index.html")

    # 自動同步到 GitHub (Auto-sync to GitHub)
    try:
        print("🚀 正在啟動自動同步 (Triggering auto-sync)...")
        # 呼叫現有的 sync.sh 進行 Git 操作
        subprocess.run(["bash", "sync.sh"], check=True)
        print("✅ GitHub 同步完成。")
    except Exception as e:
        print(f"⚠️ 自動同步發生錯誤 (Sync failed): {e}")

    # 只有在 --weekly 模式下才產生帶日期的存檔
    if args.weekly:
        today_str = now.strftime('%Y-%m-%d')
        dated_file = f"report/weekly_finance_report_{today_str}.html"
        with open(dated_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"📜 週報存檔已儲存：{dated_file}")

if __name__ == "__main__":
    main()
