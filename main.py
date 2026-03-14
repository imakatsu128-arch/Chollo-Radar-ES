"""Chollo-Radar-ES - 双数据源折扣监控 | 爬虫 + 卖家提交"""
import os, random, time, logging, requests, json
from bs4 import BeautifulSoup

# ==================== 配置 ====================
TG_TOKEN, TG_CHAT_ID = os.getenv("TG_TOKEN"), os.getenv("TG_CHAT_ID")
GH_TOKEN, GH_REPO = os.getenv("GH_TOKEN"), os.getenv("GITHUB_REPOSITORY")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# ==================== 反检测模块 ====================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0.0.0",
]

def get_random_headers():
    """生成随机浏览器请求头"""
    return {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "es-ES,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml", "Cache-Control": "no-cache"}

def random_delay(min_s=2, max_s=5):
    """随机延迟，模拟人类行为"""
    time.sleep(random.uniform(min_s, max_s))

# ==================== 数据源 A：自动爬取 ====================
def scrape_amazon():
    """爬取 Amazon ES 折扣"""
    url, session = "https://www.amazon.es/gp/goldbox", requests.Session()
    try:
        random_delay()
        log.info(f"🌐 爬取 Amazon: {url}")
        res = session.get(url, headers=get_random_headers(), timeout=15)
        if res.status_code != 200: return []
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.deal-container, [data-component-type="s-search-result"]')[:5]
        results = []
        for item in items:
            title = item.select_one('.deal-title, .a-text-normal')
            discount = item.select_one('.discount-label, .savingsPercentage')
            link = item.select_one('a[href*="/dp/"]')
            if title and discount and link:
                title_text = title.get_text(strip=True)[:45]
                discount_text = discount.get_text(strip=True)
                link_href = link['href']
                if link_href.startswith('/'): link_href = f"https://www.amazon.es{link_href}"
                discount_num = int(''.join(filter(str.isdigit, discount_text)) or '0')
                if discount_num >= 50:
                    results.append(f"🛒 **{title_text}**\n💥 -{discount_num}%\n🔗 [Amazon链接]({link_href})")
        log.info(f"✅ Amazon 发现 {len(results)} 个折扣")
        return results
    except Exception as e:
        log.error(f"❌ Amazon 爬取失败: {e}")
        return []

# ==================== 数据源 B：卖家提交 ====================
def fetch_seller_submissions():
    """获取 GitHub Issues 中的卖家提交"""
    if not (GH_TOKEN and GH_REPO): return []
    try:
        url = f"https://api.github.com/repos/{GH_REPO}/issues?state=open&labels=折扣提交"
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200: return []
        issues = res.json()
        results, issue_ids = [], []
        for issue in issues:
            body = issue.get('body', '')
            lines = [l.strip() for l in body.split('\n') if ':' in l]
            data = {l.split(':', 1)[0].strip(): l.split(':', 1)[1].strip() for l in lines if len(l.split(':', 1)) == 2}
            product = data.get('product_name', '未知商品')
            discount = data.get('discount_percent', '0')
            link = data.get('product_link', '')
            store = data.get('store', '未知店铺')
            if product and link:
                results.append(f"📦 **{product[:45]}**\n🏪 {store} | 💰 -{discount}%\n🔗 [卖家链接]({link})")
                issue_ids.append(issue['number'])
        log.info(f"✅ 卖家提交 {len(results)} 个折扣")
        return results, issue_ids
    except Exception as e:
        log.error(f"❌ 获取卖家提交失败: {e}")
        return [], []

def close_issues(issue_ids):
    """关闭已处理的 Issues"""
    if not (GH_TOKEN and GH_REPO and issue_ids): return
    for issue_id in issue_ids:
        try:
            url = f"https://api.github.com/repos/{GH_REPO}/issues/{issue_id}"
            headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
            requests.patch(url, json={"state": "closed"}, headers=headers, timeout=5)
            log.info(f"✅ 关闭 Issue #{issue_id}")
        except Exception as e:
            log.error(f"❌ 关闭 Issue #{issue_id} 失败: {e}")

# ==================== 报告生成 ====================
def create_daily_report(amazon_deals, seller_deals):
    """创建每日折扣报告"""
    if not (amazon_deals or seller_deals): return None
    date = time.strftime('%Y-%m-%d')
    report = f"# 📊 Chollo 日报 {date}\n\n"
    if amazon_deals:
        report += f"## 🤖 自动监控 ({len(amazon_deals)})\n" + "\n\n".join(amazon_deals) + "\n\n"
    if seller_deals:
        report += f"## 👥 卖家提交 ({len(seller_deals)})\n" + "\n\n".join(seller_deals) + "\n\n"
    report += f"---\n📅 报告生成时间: {time.strftime('%H:%M:%S')}"
    return report

def publish_report(report):
    """发布报告到 GitHub Issue"""
    if not (GH_TOKEN and GH_REPO and report): return False
    try:
        url = f"https://api.github.com/repos/{GH_REPO}/issues"
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        title = f"📊 Chollo 日报 {time.strftime('%Y-%m-%d')}"
        res = requests.post(url, json={"title": title, "body": report, "labels": ["chollo", "日报"]}, headers=headers, timeout=10)
        log.info("✅ 日报发布成功" if res.ok else f"❌ 日报发布失败: {res.status_code}")
        return res.ok
    except Exception as e:
        log.error(f"❌ 日报发布异常: {e}")
        return False

# ==================== 主入口 ====================
if __name__ == "__main__":
    log.info("🚀 Chollo-Radar-ES 双数据源启动")
    amazon_deals = scrape_amazon()
    seller_deals, issue_ids = fetch_seller_submissions()
    report = create_daily_report(amazon_deals, seller_deals)
    if report:
        publish_report(report)
        close_issues(issue_ids)
        if TG_TOKEN and TG_CHAT_ID:
            summary = f"🚀 **Chollo 日报已生成**\n🤖 自动监控: {len(amazon_deals)} 个\n👥 卖家提交: {len(seller_deals)} 个\n📝 查看完整报告: https://github.com/{GH_REPO}/issues"
            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                          data={"chat_id": TG_CHAT_ID, "text": summary, "parse_mode": "Markdown"}, timeout=10)
    else:
        log.info("📭 今日无折扣信息")
    log.info("🏁 运行结束")
