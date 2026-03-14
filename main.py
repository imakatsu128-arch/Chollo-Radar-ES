"""Chollo-Radar-ES - 西班牙深度折扣监控引擎 | 反检测 + Telegram + GitHub Issue"""
import os, random, time, logging, requests
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

def safe_get_text(el, default=""):
    """安全获取元素文本"""
    return el.get_text(strip=True) if el else default

def safe_get_attr(el, attr, default=""):
    """安全获取元素属性"""
    return el.get(attr, default) if el else default

# ==================== 核心爬虫 ====================
def get_chollos():
    """抓取 Amazon ES 折扣，过滤 >=50% 或价格错误"""
    url, session = "https://www.amazon.es/gp/goldbox", requests.Session()
    try:
        random_delay()
        log.info(f"🌐 抓取: {url}")
        res = session.get(url, headers=get_random_headers(), timeout=15)
        if res.status_code in [403, 429]:
            log.error(f"❌ {res.status_code} - 反爬触发，停止执行"); return []
        if res.status_code != 200:
            log.warning(f"⚠️ HTTP {res.status_code}"); return []
        soup = BeautifulSoup(res.text, 'html.parser')
        if not soup.body: log.error("❌ 页面解析失败"); return []
        
        selectors = ['.deal-container', '[data-component-type="s-search-result"]', '.octopus-dlp-asin-section']
        items = next((soup.select(s) for s in selectors if soup.select(s)), [])
        results = []
        for item in items[:10]:
            title = safe_get_text(item.select_one('.deal-title, .a-text-normal'), "未知")
            discount = safe_get_text(item.select_one('.discount-label, .savingsPercentage'), "0%")
            href = safe_get_attr(item.select_one('a[href*="/dp/"]'), 'href')
            if not href: continue
            link = f"https://www.amazon.es{href}" if href.startswith('/') else href
            discount_num = int(''.join(filter(str.isdigit, discount)) or '0')
            is_price_error = 'error' in title.lower() or 'error' in discount.lower()
            if discount_num >= 50 or is_price_error:
                tag = "💥 价格错误!" if is_price_error else f"💥 -{discount_num}%"
                results.append(f"🛒 **{title[:45]}**\n{tag}\n🔗 [捡漏链接]({link})")
                log.info(f"✨ 发现: {title[:25]}... | {tag}")
        log.info(f"🎯 共 {len(results)} 个高价值折扣"); return results[:5]
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        log.error(f"❌ 网络错误: {type(e).__name__}"); return []
    except Exception as e:
        log.error(f"❌ 异常: {e}"); return []
    finally: session.close()

# ==================== Telegram 推送 ====================
def push_alert(msg):
    """发送 Telegram 消息"""
    if not (TG_TOKEN and TG_CHAT_ID and msg): return False
    try:
        random_delay(1, 2)
        res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                            data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        log.info("✅ 推送成功" if res.ok else f"❌ 推送失败: {res.status_code}"); return res.ok
    except Exception as e: log.error(f"❌ 推送异常: {e}"); return False

# ==================== 主入口 ====================
if __name__ == "__main__":
    log.info("🚀 Chollo-Radar-ES 启动")
    chollos = get_chollos()
    if chollos: push_alert("🚀 **Chollo-Radar-ES 捡漏预警**\n\n" + "\n\n".join(chollos))
    else: log.info("📭 暂无高价值折扣")
    log.info("🏁 运行结束")
