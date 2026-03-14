"""
Chollo-Radar-ES Web UI - 本地折扣监控界面
简洁现代界面，实时显示 GitHub 折扣报告
"""
import os
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# GitHub 配置
GITHUB_REPO = os.getenv("GITHUB_REPO", "imakatsu128-arch/Chollo-Radar-ES")
GITHUB_TOKEN = os.getenv("GH_TOKEN", "")

def fetch_latest_report():
    """获取最新的 Chollo 日报 Issue"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        # 获取所有 Issue
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        issues = response.json()
        
        # 查找最新的 "Chollo 日报" Issue
        for issue in issues:
            if "Chollo 日报" in issue.get("title", "") and issue.get("state") == "open":
                return {
                    "title": issue["title"],
                    "body": issue["body"],
                    "created_at": issue["created_at"],
                    "number": issue["number"],
                    "url": issue["html_url"]
                }
        
        # 如果没有找到开放的日报，找最近关闭的
        for issue in issues:
            if "Chollo 日报" in issue.get("title", ""):
                return {
                    "title": issue["title"],
                    "body": issue["body"],
                    "created_at": issue["created_at"],
                    "number": issue["number"],
                    "url": issue["html_url"],
                    "closed": True
                }
        
        return None
    except Exception as e:
        print(f"❌ 获取报告失败: {e}")
        return None

def parse_report_content(report_body):
    """解析报告内容，提取折扣信息"""
    if not report_body:
        return []
    
    deals = []
    lines = report_body.split('\n')
    current_deal = {}
    
    for line in lines:
        line = line.strip()
        
        # 检测新折扣开始
        if line.startswith('🛒') or line.startswith('📦'):
            if current_deal:
                deals.append(current_deal)
            current_deal = {"title": line, "details": []}
        elif current_deal and line:
            current_deal["details"].append(line)
    
    if current_deal:
        deals.append(current_deal)
    
    return deals

@app.route('/')
def index():
    """主页面"""
    report = fetch_latest_report()
    deals = parse_report_content(report["body"] if report else "") if report else []
    
    return render_template('index.html', 
                         report=report, 
                         deals=deals,
                         repo_url=f"https://github.com/{GITHUB_REPO}")

@app.route('/api/report')
def api_report():
    """API 端点：获取最新报告"""
    report = fetch_latest_report()
    if report:
        deals = parse_report_content(report["body"])
        return jsonify({
            "success": True,
            "report": report,
            "deals": deals,
            "count": len(deals)
        })
    return jsonify({"success": False, "message": "未找到报告"})

@app.route('/api/search')
def api_search():
    """搜索折扣"""
    query = request.args.get('q', '').lower()
    report = fetch_latest_report()
    
    if not report:
        return jsonify({"success": False, "results": []})
    
    deals = parse_report_content(report["body"])
    results = []
    
    for deal in deals:
        title = deal.get("title", "").lower()
        details = " ".join(deal.get("details", [])).lower()
        
        if query in title or query in details:
            results.append(deal)
    
    return jsonify({
        "success": True,
        "query": query,
        "results": results,
        "count": len(results)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)