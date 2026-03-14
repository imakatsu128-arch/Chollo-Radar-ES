# 🛒 Chollo-Radar-ES

**西班牙深度折扣监控雷达** - 独立、轻量、高频的西班牙大牌折扣监控系统。

## ✨ 功能特点

- 🔍 自动抓取 Amazon ES 每日优惠
- 📊 智能过滤 50% 以上折扣商品
- 📲 实时 Telegram 推送预警
- ⏰ 每 30 分钟自动运行（GitHub Actions）
- 🚀 零成本部署，无需服务器

## 📁 项目结构

```
Chollo-Radar-ES/
├── main.py                          # 核心监控代码
├── requirements.txt                 # Python 依赖
├── .github/
│   └── workflows/
│       └── radar_cron.yml          # GitHub Actions 自动化
└── README.md
```

## 🚀 快速部署

### 1. Fork 本项目

### 2. 配置 GitHub Secrets

在仓库的 `Settings` → `Secrets and variables` → `Actions` 中添加：

| Secret 名称 | 说明 |
|------------|------|
| `TG_TOKEN` | Telegram Bot Token（从 @BotFather 获取） |
| `TG_CHAT_ID` | 接收消息的 Chat ID |

### 3. 启用 GitHub Actions

项目会自动每 30 分钟运行一次，也可在 Actions 页面手动触发。

## 🔧 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export TG_TOKEN="your_bot_token"
export TG_CHAT_ID="your_chat_id"

# 运行
python main.py
```

## 💰 盈利模式

通过链接挂载 Affiliate ID（如 `tag=xxx-21`）赚取佣金，无需收会员费。

## 📋 开发计划

- [ ] 支持更多电商平台（MediaMarkt, PcComponentes 等）
- [ ] 添加关键词过滤功能
- [ ] 优化折扣计算逻辑
- [ ] 添加历史价格追踪

## 📄 许可证

MIT License
