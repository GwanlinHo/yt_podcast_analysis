import os
import json
import datetime
import argparse
import hashlib
import subprocess
from storage import Storage, Video

OUTPUT_FILE = "report/latest_report.html"

def get_week_range():
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
            --shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #1a1a1a;
                --card-bg: #2d2d2d;
                --text-color: #e0e0e0;
                --border-color: #404040;
                --shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            body { background-color: var(--bg-color); color: var(--text-color); }
            .episode-block { background: #363636 !important; border-color: #444 !important; }
            .quote-box { background: #3d3d3d !important; color: #ccc !important; }
            .nav-item { background: #333 !important; color: #ddd !important; border-color: #555 !important; }
            th { background-color: #3d3d3d !important; color: #bbb !important; }
            td { border-bottom-color: #444 !important; }
            .focus-section, .disclaimer-section { background: #2d2d2d !important; }
            .search-box { background: #333 !important; border-color: #555 !important; color: #fff !important; }
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            line-height: 1.7;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 40px 20px;
            transition: background 0.3s;
        }
        .container { max-width: 1150px; margin: 0 auto; }
        
        header {
            text-align: center;
            margin-bottom: 50px;
            padding: 60px 40px;
            background: var(--primary-gradient);
            color: white;
            border-radius: 20px;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }
        header h1 { margin: 0; font-size: 2.8em; font-weight: 800; }
        .meta { margin-top: 15px; opacity: 0.85; font-size: 1.1em; letter-spacing: 0.5px; }
        
        .nav-bar { display: flex; gap: 10px; margin-bottom: 40px; flex-wrap: wrap; justify-content: center; }
        .nav-item {
            background: #fff; padding: 10px 22px; border-radius: 30px; text-decoration: none;
            color: var(--text-color); font-weight: 600; font-size: 0.95em;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid #eee;
        }
        .nav-item:hover {
            border-color: var(--accent-color); color: var(--accent-color);
            transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }

        .focus-section {
            background: #fff; border-left: 10px solid #f1c40f; border-radius: 15px;
            padding: 35px; margin-bottom: 50px; box-shadow: var(--shadow);
        }
        .focus-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; flex-wrap: wrap; gap: 20px; }
        .focus-title { font-size: 1.7em; color: #d35400; font-weight: 800; margin: 0; }
        
        /* Sentiment Chart Bar */
        .sentiment-container { margin-top: 15px; width: 100%; height: 12px; background: #eee; border-radius: 6px; overflow: hidden; display: flex; }
        .sentiment-bar-bull { background: var(--bullish-color); height: 100%; transition: width 1s ease-out; }
        .sentiment-bar-bear { background: var(--bearish-color); height: 100%; transition: width 1s ease-out; }
        .sentiment-legend { display: flex; justify-content: center; gap: 20px; margin-top: 8px; font-size: 0.9em; font-weight: 600; }

        .search-box { padding: 12px 25px; border-radius: 30px; border: 2px solid #eee; font-size: 0.95em; width: 320px; outline: none; transition: all 0.3s; }
        .search-box:focus { border-color: var(--accent-color); box-shadow: 0 0 0 4px rgba(52, 152, 219, 0.1); }

        .creator-section {
            background: var(--card-bg); border-radius: 20px; box-shadow: var(--shadow);
            margin-bottom: 50px; padding: 45px; border-top: 8px solid var(--accent-color); scroll-margin-top: 30px;
        }
        .creator-title { margin-top: 0; font-size: 2.1em; color: var(--accent-color); border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; font-weight: 800; }
        
        .episode-block { margin-bottom: 45px; padding: 30px; border-radius: 15px; background: #fafbfc; border: 1px solid #f0f1f2; transition: transform 0.3s; }
        .episode-block:hover { border-color: var(--accent-color); transform: scale(1.005); }
        
        .episode-title { font-size: 1.5em; margin-bottom: 25px; line-height: 1.4; }
        .episode-title a { color: #2980b9; text-decoration: none; font-weight: 800; }
        
        .section-title { font-weight: 800; color: #34495e; margin-bottom: 15px; display: block; font-size: 1.15em; border-left: 5px solid var(--accent-color); padding-left: 15px; }
        .quote-box { background: #f1f5f9; padding: 25px; border-radius: 12px; font-style: italic; margin: 30px 0; color: #475569; font-size: 1.1em; text-align: center; font-weight: 500; }
        
        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 20px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color); }
        th, td { padding: 18px; text-align: left; border-bottom: 1px solid var(--border-color); }
        th { background-color: #f8f9fa; font-weight: 800; color: #64748b; text-transform: uppercase; font-size: 0.85em; letter-spacing: 1px; }
        
        .view-bull { color: var(--bullish-color); font-weight: 800; }
        .view-bear { color: var(--bearish-color); font-weight: 800; }
        .view-neutral { color: var(--neutral-color); font-weight: 800; }
        
        .disclaimer-section { margin-top: 80px; padding: 40px; background: #fff; border-radius: 20px; font-size: 0.95em; color: #64748b; box-shadow: var(--shadow); text-align: center; line-height: 2; }
        
        @media screen and (max-width: 768px) {
            header { padding: 40px 20px; border-radius: 0; }
            header h1 { font-size: 1.8em; }
            .creator-section { padding: 25px; }
            table, thead, tbody, th, td, tr { display: block; }
            thead tr { position: absolute; top: -9999px; left: -9999px; }
            tr { border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 20px; }
            td { border: none; border-bottom: 1px solid #eee; position: relative; padding-left: 45%; }
            td:before { position: absolute; top: 18px; left: 15px; width: 40%; font-weight: bold; color: #94a3b8; font-size: 0.8em; }
            td:nth-of-type(1) { padding-left: 15px; background: #f8f9fa; font-weight: bold; font-size: 1.1em; }
            td:nth-of-type(1):before { content: ""; }
            td:nth-of-type(2):before { content: "共識"; }
            td:nth-of-type(3):before { content: "觀點"; }
            td:nth-of-type(4):before { content: "說明"; }
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
                    tr[i].style.display = txtValue.toUpperCase().indexOf(filter) > -1 ? "" : "none";
                }
            }
        }
    </script>
    """

def generate_search_index(db):
    """產生全文檢索索引檔案"""
    index_data = []
    for v in db.videos.values():
        if v.status == "analyzed":
            analysis = db.get_analysis(v.id)
            if analysis:
                content_text = f"{v.title} {' '.join(analysis.get('key_points', []))} {' '.join(analysis.get('macro_outlook', []))}"
                index_data.append({
                    "id": v.id,
                    "title": v.title,
                    "url": v.url,
                    "date": v.date,
                    "channel": v.channel,
                    "text": content_text.lower()
                })
    
    index_path = "data/search_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False)
    print(f"🔍 全文檢索索引已更新: {index_path}")

def generate_archives(db):
    """產生包含所有歷史影片的搜尋頁面與全文檢索介面"""
    all_videos = sorted(db.videos.values(), key=lambda x: x.date, reverse=True)
    stats = db.get_global_stats()
    
    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>財經影片全文檢索中心</title>
    {generate_css()}
    <style>
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .stat-card {{ background: var(--card-bg); padding: 25px; border-radius: 15px; box-shadow: var(--shadow); text-align: center; border-bottom: 5px solid var(--accent-color); }}
        .stat-value {{ font-size: 2em; font-weight: 800; color: var(--accent-color); }}
        .stat-label {{ font-size: 0.9em; color: #7f8c8d; margin-top: 5px; font-weight: 600; }}
        .top-targets-list {{ text-align: left; margin-top: 15px; padding: 0; list-style: none; }}
        .top-targets-list li {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-color); font-size: 0.9em; }}
        .search-mode-toggle {{ margin-bottom: 20px; text-align: center; }}
        .highlight {{ background: #fff3cd; padding: 0 2px; border-radius: 3px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>全量財經知識檢索中心</h1>
            <div class="meta">大數據洞察：系統已自動處理 {stats['total_analyzed']} 份深度分析報告</div>
        </header>
        <div class="nav-bar">
            <a href="index.html" class="nav-item">🏠 返回本週週報</a>
            <a href="data/all_analysis.csv" class="nav-item">📥 匯出 CSV 數據</a>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_videos']}</div>
                <div class="stat-label">收錄影片總數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{int((stats['total_analyzed']/stats['total_videos'])*100)}%</div>
                <div class="stat-label">AI 分析完成率</div>
            </div>
            <div class="stat-card" style="grid-row: span 2;">
                <div class="stat-label" style="font-size: 1.1em; color: var(--text-color); margin-bottom: 10px;">🔥 歷史熱門標的 (Top 10)</div>
                <ul class="top-targets-list">
    """
    for name, count in stats['top_targets']:
        html += f'<li><span>{name}</span><span style="color: var(--bullish-color); font-weight:bold;">{count}x</span></li>'
    
    html += f"""
                </ul>
            </div>
            <div class="stat-card">
                <div class="stat-label" style="margin-bottom: 10px;">📊 來源頻道產量</div>
                <div style="font-size: 0.85em; text-align: left;">
    """
    for ch, count in sorted(stats['channel_distribution'].items(), key=lambda x: x[1], reverse=True):
        html += f'<div style="margin-bottom: 5px;">{ch}: <span style="float:right; font-weight:bold;">{count}</span></div>'

    html += """
                </div>
            </div>
        </div>
        
        <div class="focus-section">
            <div class="focus-header">
                <h2 class="focus-title">🔍 全文知識檢索</h2>
                <input type="text" id="archiveSearch" onkeyup="handleSearch()" placeholder="搜尋關鍵字（含分析內容）..." class="search-box">
            </div>
            <div id="searchInfo" style="margin-bottom: 15px; font-size: 0.9em; color: #7f8c8d;"></div>
            <table id="archiveTable">
                <thead>
                    <tr>
                        <th style="width: 15%">日期</th>
                        <th style="width: 15%">頻道</th>
                        <th>影片標題</th>
                        <th style="width: 10%">狀態</th>
                    </tr>
                </thead>
                <tbody id="archiveBody">
    """
    for v in all_videos:
        status_tag = '<span class="view-bear">待分析</span>' if v.status == 'pending' else '<span style="color: var(--bearish-color); font-weight:bold;">已完成</span>'
        html += f"""
            <tr>
                <td>{v.date}</td>
                <td>{v.channel}</td>
                <td><a href="{v.url}" target="_blank" style="text-decoration:none; color: var(--text-color); font-weight: 600;">{v.title}</a></td>
                <td>{status_tag}</td>
            </tr>
        """
    html += """
                </tbody>
            </table>
        </div>
    </div>
    <script>
        let searchIndex = [];
        
        // 載入索引檔
        fetch('data/search_index.json')
            .then(response => response.json())
            .then(data => { searchIndex = data; })
            .catch(err => console.error("無法載入檢索索引:", err));

        function handleSearch() {
            const query = document.getElementById('archiveSearch').value.toLowerCase().trim();
            const body = document.getElementById('archiveBody');
            const info = document.getElementById('searchInfo');
            
            if (query === "") {
                location.reload(); // 恢復原始列表
                return;
            }

            const results = searchIndex.filter(item => item.text.includes(query));
            info.innerText = `找到 ${results.length} 筆相關分析結果`;
            
            let html = "";
            results.sort((a, b) => b.date.localeCompare(a.date)).forEach(item => {
                html += `<tr>
                    <td>${item.date}</td>
                    <td>${item.channel}</td>
                    <td><a href="${item.url}" target="_blank" style="text-decoration:none; color: var(--text-color); font-weight: 600;">${item.title}</a></td>
                    <td><span style="color: var(--bearish-color); font-weight:bold;">已完成</span></td>
                </tr>`;
            });
            body.innerHTML = html || "<tr><td colspan='4' style='text-align:center'>無匹配結果</td></tr>";
        }
    </script>
</body>
</html>
    """
    with open("archives.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print("📚 全文檢索知識庫頁面已更新: archives.html")

def render_nav_bar(channels):
    if not channels: return ""
    html = '<div class="nav-bar">'
    html += '<a href="archives.html" class="nav-item" style="background: var(--accent-color); color: white;">🏛️ 全量知識庫</a>'
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
        <ul style="margin-top: 20px;">
    """
    for t in trends: html += f"<li>{t}</li>"
    html += "</ul></div>"
    return html

def get_finance_link(code):
    if not code or code == "N/A": return "#"
    if code[0].isdigit(): return f"https://www.google.com/finance/quote/{code}:TPE"
    else: return f"https://www.google.com/finance/quote/{code}:NASDAQ"

def render_focus_summary(db, start_str, end_str):
    unique_targets = db.get_aggregated_targets(start_str, end_str)
    if not unique_targets: return ""
    bull = sum(1 for t in unique_targets if "多" in t.get('view', ''))
    bear = sum(1 for t in unique_targets if "空" in t.get('view', ''))
    total = bull + bear if (bull + bear) > 0 else 1
    bull_pct = (bull / total) * 100
    bear_pct = (bear / total) * 100

    html = f'<div class="focus-section"><div class="focus-header"><h2 class="focus-title">🚀 本週投資焦點彙整 (Consensus)</h2><input type="text" id="targetSearch" onkeyup="filterTargets()" placeholder="快速搜尋標的..." class="search-box"></div>'
    html += f'<div class="sentiment-container"><div class="sentiment-bar-bull" style="width: {bull_pct}%"></div><div class="sentiment-bar-bear" style="width: {bear_pct}%"></div></div>'
    html += f'<div class="sentiment-legend"><span class="view-bull">▲ 多頭力道: {bull}</span> <span class="view-bear">▼ 空頭力道: {bear}</span></div>'
    html += '<table id="focusTable"><thead><tr><th style="width: 20%">標的</th><th style="width: 10%; text-align: center;">共識</th><th style="width: 15%">觀點</th><th>核心理由摘要</th></tr></thead><tbody>'
    for t in unique_targets:
        view_class = "view-neutral"
        view_text = t.get('view', '中性')
        if "多" in view_text: view_class = "view-bull"
        elif "空" in view_text: view_class = "view-bear"
        code = t.get('code', 'N/A')
        link = get_finance_link(code)
        mentions = t.get('mentions', 1)
        m_style = 'style="font-weight: 800; color: #d35400;"' if mentions > 1 else ""
        html += f'<tr><td><strong>{t.get("name", "")}</strong> <a href="{link}" target="_blank" style="font-size: 0.85em; color: #95a5a6; text-decoration: none;">({code} 📈)</a></td><td style="text-align: center;"><span {m_style}>{mentions}x</span></td><td><span class="{view_class}">{view_text}</span></td><td>{t.get("rationale", "")}</td></tr>'
    html += "</tbody></table></div>"
    return html

def render_targets_table(targets):
    if not targets: return "<p>本集未特別提及具體投資標的。</p>"
    html = '<table><thead><tr><th style="width: 25%">標的</th><th style="width: 15%">觀點</th><th>情境說明</th></tr></thead><tbody>'
    for t in targets:
        v_class = "view-neutral"
        v_text = t.get('view', '中性')
        if "多" in v_text: v_class = "view-bull"
        elif "空" in v_text: v_class = "view-bear"
        code = t.get('code', 'N/A')
        link = get_finance_link(code)
        html += f'<tr><td>{t.get("name", "")} <a href="{link}" target="_blank" style="font-size: 0.85em; color: #95a5a6; text-decoration: none;">({code} 📈)</a></td><td><span class="{v_class}">{v_text}</span></td><td>{t.get("rationale", "")}</td></tr>'
    return html + "</tbody></table>"

def generate_disclaimer():
    return '<div class="disclaimer-section"><strong>💡 免責聲明與版權說明</strong><br><br>本報告內容係透過 AI 萃取各內容創作者之公開分享資訊彙整而成，僅供參考，不代表本系統之立場。投資人應保持獨立思考，審慎評估風險。<br><br><strong>支持創作者：</strong>強烈建議點擊報告中的連結，前往創作者的原始頻道觀看完整影片並給予訂閱與支持。</div>'

def render_history_links():
    h_dir = "report/history"
    if not os.path.exists(h_dir): return ""
    files = sorted([f for f in os.listdir(h_dir) if f.startswith("weekly_finance_report_") and f.endswith(".html")], reverse=True)
    if not files: return ""
    html = '<div class="disclaimer-section" style="text-align: left; margin-top: 30px;"><span class="section-title" style="border-left-color: #7f8c8d; color: #7f8c8d;">📚 歷史報表存檔 (Archives)</span><div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; justify-content: center;">'
    for f in files:
        d = f.replace("weekly_finance_report_", "").replace(".html", "")
        html += f'<a href="report/history/{f}" class="nav-item" style="font-size: 0.85em; padding: 8px 18px; background: #f8f9fa;">📅 {d}</a>'
    return html + "</div></div>"

def get_content_hash(channels, db):
    data = []
    for videos in channels.values():
        for v in videos: data.append({"id": v.id, "status": v.status, "analysis": db.get_analysis(v.id) if v.status == "analyzed" else None})
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

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
    curr_hash = get_content_hash(channels, db)
    hash_file = "data/.report_hash"
    old_hash = open(hash_file, 'r').read().strip() if os.path.exists(hash_file) else ""
    if curr_hash == old_hash and not args.force and not args.weekly:
        print("💡 內容無變動，跳過更新。")
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
            <div class="meta">📅 統計期間：{start_str} 至 {end_str} | ⏱️ 生成：{now.strftime('%Y/%m/%d %H:%M')}</div>
        </header>
        {render_nav_bar(channels)}
        {render_macro_summary(db, start_str, end_str)}
        {render_focus_summary(db, start_str, end_str)}
    """
    if not channels: html += "<p style='text-align:center'>本週尚未有新影片。</p>"
    for ch_name, v_list in channels.items():
        html += f'<div class="creator-section" id="{ch_name}"><h2 class="creator-title">{ch_name}</h2>'
        for v in v_list:
            analysis = db.get_analysis(v.id) if v.status == "analyzed" else None
            html += f'<div class="episode-block"><div class="episode-title"><a href="{v.url}" target="_blank">{v.title}</a>{f"<span class=\"pending-badge\">待分析</span>" if v.status == "pending" else ""}</div>'
            if analysis:
                if analysis.get('macro_outlook'):
                    html += '<div class="macro-section"><span class="section-title">🌍 總體環境與趨勢觀點</span><ul>'
                    for p in analysis.get('macro_outlook', []): html += f"<li>{p}</li>"
                    html += "</ul></div>"
                html += '<div class="summary-section"><span class="section-title">📝 重點議題摘要</span><ul>'
                for p in analysis.get('key_points', []): html += f"<li>{p}</li>"
                html += "</ul></div>"
                html += '<div class="targets-section"><span class="section-title">📊 提及標的</span>' + render_targets_table(analysis.get('targets', [])) + '</div>'
                if analysis.get('risk_factors'):
                    html += '<div class="risk-section"><span class="section-title">⚠️ 風險警示與觀察指標</span><ul>'
                    for r in analysis.get('risk_factors', []): html += f'<li class="risk-item">{r}</li>'
                    html += "</ul></div>"
                if analysis.get('quotes'): html += f'<div class="quote-box">「{analysis.get("quotes")}」</div>'
            else: html += '<div class="summary-section"><p style="color:#999; font-style:italic;">尚未分析。</p></div>'
            html += "</div>"
        html += "</div>"
    html += generate_disclaimer() + render_history_links() + "</div></body></html>"
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f: f.write(html)
    with open("index.html", 'w', encoding='utf-8') as f: f.write(html)
    with open(hash_file, 'w') as f: f.write(curr_hash)
    # 執行數據匯出與全量知識庫生成
    db.export_to_csv()
    generate_search_index(db)
    generate_archives(db)

    print(f"✨ 報告已更新：{OUTPUT_FILE}")
    try:
        subprocess.run(["bash", "sync.sh"], check=True)
        print("✅ GitHub 同步完成。")
    except Exception as e: print(f"⚠️ 同步失敗: {e}")
    if args.weekly:
        dated_file = f"report/history/weekly_finance_report_{now.strftime('%Y-%m-%d')}.html"
        with open(dated_file, 'w', encoding='utf-8') as f: f.write(html)
        print(f"📜 週報存檔已儲存：{dated_file}")

if __name__ == "__main__":
    main()
