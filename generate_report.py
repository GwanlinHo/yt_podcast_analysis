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
            --primary-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            --accent-color: #3498db;
            --bg-color: #f4f7f6;
            --card-bg: #ffffff;
            --text-color: #2c3e50;
            --border-color: #dcdde1;
            --bullish-color: #e84118;
            --bearish-color: #44bd32;
            --neutral-color: #7f8c8d;
            --shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        body {
            font-family: 'Segoe UI', Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.7;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 40px 20px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 50px;
            padding: 40px;
            background: var(--primary-gradient);
            color: white;
            border-radius: 12px;
            box-shadow: var(--shadow);
        }
        header h1 { margin: 0; font-size: 2.5em; letter-spacing: 1px; }
        .meta { margin-top: 15px; opacity: 0.9; font-size: 1.1em; }
        
        /* Navigation Bar */
        .nav-bar {
            display: flex;
            gap: 12px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .nav-item {
            background: #fff;
            padding: 8px 18px;
            border-radius: 20px;
            text-decoration: none;
            color: var(--text-color);
            font-weight: 600;
            font-size: 0.9em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s;
            border: 1px solid #eee;
        }
        .nav-item:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Focus Section */
        .focus-section {
            background: #fff;
            border-left: 8px solid #f1c40f;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: var(--shadow);
        }
        .focus-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        .focus-title {
            font-size: 1.5em;
            color: #d35400;
            font-weight: bold;
            margin: 0;
        }
        .search-box {
            padding: 10px 20px;
            border-radius: 25px;
            border: 2px solid #eee;
            font-size: 0.9em;
            width: 300px;
            outline: none;
            transition: border-color 0.3s;
        }
        .search-box:focus { border-color: var(--accent-color); }

        .creator-section {
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 40px;
            padding: 35px;
            border-top: 5px solid var(--accent-color);
            scroll-margin-top: 20px;
        }
        .creator-title {
            margin-top: 0;
            font-size: 1.8em;
            color: var(--accent-color);
            border-bottom: 2px solid #eee;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }
        
        .episode-block {
            margin-bottom: 40px;
            padding: 20px;
            border-radius: 8px;
            background: #fafbfc;
            border: 1px solid #f0f1f2;
        }
        .episode-block:hover { border-color: var(--accent-color); }
        .episode-title {
            font-size: 1.3em;
            margin-bottom: 20px;
        }
        .episode-title a {
            color: #2980b9;
            text-decoration: none;
            font-weight: 700;
        }
        .episode-title a:hover { color: var(--accent-color); text-decoration: underline; }
        
        .section-title {
            font-weight: bold;
            color: #34495e;
            margin-bottom: 12px;
            display: block;
            font-size: 1.1em;
            border-left: 4px solid var(--accent-color);
            padding-left: 10px;
        }
        .quote-box {
            background: #edf2f7;
            padding: 20px;
            border-radius: 8px;
            font-style: italic;
            margin: 20px 0;
            color: #4a5568;
            font-size: 1.05em;
            text-align: center;
        }
        .risk-item { color: #c0392b; font-weight: 600; }
        ul { padding-left: 20px; }
        li { margin-bottom: 8px; }
        
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 15px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid var(--border-color); }
        th { background-color: #f8f9fa; font-weight: 700; color: #7f8c8d; text-transform: uppercase; font-size: 0.85em; }
        
        .view-bull { color: var(--bullish-color); font-weight: 800; }
        .view-bear { color: var(--bearish-color); font-weight: 800; }
        .view-neutral { color: var(--neutral-color); font-weight: 800; }
        
        .disclaimer-section {
            margin-top: 60px;
            padding: 30px;
            background: #fff;
            border-radius: 12px;
            font-size: 0.9em;
            color: #7f8c8d;
            box-shadow: var(--shadow);
            text-align: center;
        }
        
        /* Mobile Responsive */
        @media screen and (max-width: 768px) {
            table, thead, tbody, th, td, tr { display: block; }
            thead tr { position: absolute; top: -9999px; left: -9999px; }
            tr { border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 15px; }
            td { border: none; border-bottom: 1px solid #eee; position: relative; padding-left: 50%; }
            td:before { position: absolute; top: 15px; left: 15px; width: 45%; font-weight: bold; color: #666; }
            td:nth-of-type(1) { padding-left: 15px; background: #f8f9fa; font-weight: bold; }
            td:nth-of-type(1):before { content: ""; }
            td:nth-of-type(2):before { content: "觀點"; }
            td:nth-of-type(3):before { content: "說明"; }
            .search-box { width: 100%; }
        }
    </style>
    <script>
        function filterTargets() {
            const input = document.getElementById('targetSearch');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('focusTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = "";
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
        }
    </script>
    """

def render_nav_bar(channels):
    if not channels: return ""
    html = '<div class="nav-bar">'
    for name in channels.keys():
        html += f'<a href="#{name}" class="nav-item">📍 {name}</a>'
    html += '</div>'
    return html

def render_macro_summary(db, start_str, end_str):
    trends = db.get_macro_outlook_summary(start_str, end_str)
    if not trends: return ""
    html = """
    <div class="focus-section" style="border-left-color: #3498db;">
        <div class="focus-title" style="color: #2980b9;">🌍 本週總經與產業趨勢彙整 (Macro Trends)</div>
        <ul>
    """
    for t in trends:
        html += f"<li>{t}</li>"
    html += "</ul></div>"
    return html

def get_finance_link(code):
    """根據代碼生成 Google Finance 連結"""
    if not code or code == "N/A": return "#"
    if code[0].isdigit():
        return f"https://www.google.com/finance/quote/{code}:TPE"
    else:
        return f"https://www.google.com/finance/quote/{code}:NASDAQ"

def render_focus_summary(db, start_str, end_str):
    """彙整本週提及的所有標的與多空情緒統計"""
    unique_targets = db.get_aggregated_targets(start_str, end_str)
    if not unique_targets: return ""

    bull_count = sum(1 for t in unique_targets if "多" in t.get('view', ''))
    bear_count = sum(1 for t in unique_targets if "空" in t.get('view', ''))

    html = f"""
    <div class="focus-section">
        <div class="focus-header">
            <h2 class="focus-title">
                🚀 本週投資焦點彙整 
                <span style="font-size: 0.6em; color: #7f8c8d; margin-left: 10px; font-weight: normal;">
                    (市場情緒：<span class="view-bull">{bull_count}</span> 多 / <span class="view-bear">{bear_count}</span> 空)
                </span>
            </h2>
            <input type="text" id="targetSearch" onkeyup="filterTargets()" placeholder="搜尋標的名稱或代碼..." class="search-box">
        </div>
        <table id="focusTable">
            <thead>
                <tr>
                    <th style="width: 25%">標的</th>
                    <th style="width: 15%">觀點</th>
                    <th>核心理由摘要</th>
                </tr>
            </thead>
            <tbody>
    """
    for t in unique_targets:
        view_class = "view-neutral"
        view_text = t.get('view', '中性')
        if "多" in view_text: view_class = "view-bull"
        elif "空" in view_text: view_class = "view-bear"
        
        code = t.get('code', 'N/A')
        link = get_finance_link(code)
        
        html += f"""
            <tr>
                <td><strong>{t.get('name', '')}</strong> <a href="{link}" target="_blank" style="font-size: 0.85em; color: #95a5a6; text-decoration: none;">({code} 📈)</a></td>
                <td><span class="{view_class}">{view_text}</span></td>
                <td>{t.get('rationale', '')}</td>
            </tr>
        """
    html += "</tbody></table></div>"
    return html

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
        view_class = "view-neutral"
        view_text = t.get('view', '中性')
        if "多" in view_text: view_class = "view-bull"
        elif "空" in view_text: view_class = "view-bear"
        
        code = t.get('code', 'N/A')
        link = get_finance_link(code)

        html += f"""
            <tr>
                <td>{t.get('name', '')} <a href="{link}" target="_blank" style="font-size: 0.85em; color: #95a5a6; text-decoration: none;">({code} 📈)</a></td>
                <td><span class="{view_class}">{view_text}</span></td>
                <td>{t.get('rationale', '')}</td>
            </tr>
        """
    html += "</tbody></table>"
    return html

def generate_disclaimer():
    return """
    <div class="disclaimer-section">
        <strong>💡 免責聲明與版權說明</strong><br><br>
        本報告內容係透過 AI 萃取各內容創作者之公開分享資訊彙整而成，僅供參考，不代表本系統之立場。投資人應保持獨立思考，審慎評估風險。
        <br><br>
        <strong>支持創作者：</strong>強烈建議點擊報告中的連結，前往創作者的原始頻道觀看完整影片並給予訂閱與支持。
    </div>
    """

def get_content_hash(channels, db):
    content_data = []
    for channel, videos in channels.items():
        for v in videos:
            analysis = db.get_analysis(v.id) if v.status == "analyzed" else None
            content_data.append({"id": v.id, "status": v.status, "analysis": analysis})
    return hashlib.md5(json.dumps(content_data, sort_keys=True).encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    db = Storage()
    start_str, end_str = get_week_range()
    videos = db.get_videos_by_date_range(start_str, end_str)
    
    channels = {}
    for v in videos:
        if v.channel not in channels: channels[v.channel] = []
        channels[v.channel].append(v)

    current_hash = get_content_hash(channels, db)
    hash_file = "data/.report_hash"
    old_hash = ""
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f: old_hash = f.read().strip()

    if current_hash == old_hash and not args.force and not args.weekly:
        print("💡 內容無變動，跳過報表更新。")
        return

    now = datetime.datetime.now()
    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>財經投資週報系統</title>
    {generate_css()}
</head>
<body>
    <div class="container">
        <header>
            <h1>財經投資週報系統</h1>
            <div class="meta">
                📅 統計期間：{start_str} 至 {end_str} | ⏱️ 生成：{now.strftime('%Y/%m/%d %H:%M')}
            </div>
        </header>
        
        {render_nav_bar(channels)}
        {render_macro_summary(db, start_str, end_str)}
        {render_focus_summary(db, start_str, end_str)}
    """

    if not channels:
        html += "<p style='text-align:center'>本週尚未有新影片。</p>"
    
    for channel_name, video_list in channels.items():
        html += f'<div class="creator-section" id="{channel_name}"><h2 class="creator-title">{channel_name}</h2>'
        for v in video_list:
            analysis = db.get_analysis(v.id) if v.status == "analyzed" else None
            html += f"""
            <div class="episode-block">
                <div class="episode-title">
                    <a href="{v.url}" target="_blank">{v.title}</a>
                    {f'<span class="pending-badge">待分析</span>' if v.status == 'pending' else ''}
                </div>
            """
            if analysis:
                if analysis.get('macro_outlook'):
                    html += '<div class="macro-section"><span class="section-title">🌍 總體環境與趨勢觀點</span><ul>'
                    for p in analysis.get('macro_outlook', []): html += f"<li>{p}</li>"
                    html += "</ul></div>"
                html += '<div class="summary-section"><span class="section-title">📝 重點議題摘要</span><ul>'
                for p in analysis.get('key_points', []): html += f"<li>{p}</li>"
                html += "</ul></div>"
                html += '<div class="targets-section"><span class="section-title">📊 提及標的</span>'
                html += render_targets_table(analysis.get('targets', []))
                html += "</div>"
                if analysis.get('risk_factors'):
                    html += '<div class="risk-section"><span class="section-title">⚠️ 風險警示與觀察指標</span><ul>'
                    for r in analysis.get('risk_factors', []): html += f'<li class="risk-item">{r}</li>'
                    html += "</ul></div>"
                if analysis.get('quotes'):
                    html += f'<div class="quote-box">「{analysis.get("quotes")}」</div>'
            else:
                html += '<div class="summary-section"><p style="color:#999; font-style:italic;">尚未分析。</p></div>'
            html += "</div>"
        html += "</div>"
        
    html += generate_disclaimer() + "</div></body></html>"

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f: f.write(html)
    with open("index.html", 'w', encoding='utf-8') as f: f.write(html)
    with open(hash_file, 'w') as f: f.write(current_hash)
    
    print(f"✨ 報告已更新：{OUTPUT_FILE}")
    try:
        subprocess.run(["bash", "sync.sh"], check=True)
        print("✅ GitHub 同步完成。")
    except Exception as e:
        print(f"⚠️ 同步失敗: {e}")

    if args.weekly:
        dated_file = f"report/history/weekly_finance_report_{now.strftime('%Y-%m-%d')}.html"
        with open(dated_file, 'w', encoding='utf-8') as f: f.write(html)
        print(f"📜 週報存檔已儲存：{dated_file}")

if __name__ == "__main__":
    main()
