# 🤖 App Store Update Tracker Bot

追踪 Apple App Store 应用更新，并通过 Telegram 自动推送通知的轻量机器人。

[![Stars](https://img.shields.io/github/stars/ZenmoFeiShi/app-store-update-tracker-bot?style=flat-square)](https://github.com/ZenmoFeiShi/app-store-update-tracker-bot/stargazers)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker)](./docker-compose.yml)

用户把 App Store 链接发给机器人后，机器人会自动记录该应用，并由定时任务持续检查版本变化；一旦检测到新版本，就把版本号、发布日期、更新说明和应用链接推送到 Telegram。

## ✨ 功能

- 发送 App Store 链接后自动加入追踪
- 自动解析 App ID 和国家/地区
- 同一用户重复添加时自动去重
- 支持查看当前追踪列表
- 支持按编号取消追踪
- 定时检查版本号和更新说明变化
- 检测到更新后自动推送 Telegram 消息
- 使用 SQLite 本地存储，部署简单
- 同时支持本地运行、Docker 部署、systemd 部署

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ZenmoFeiShi/app-store-update-tracker-bot.git
cd app-store-update-tracker-bot
```

### 2. 安装依赖

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

`.env` 示例：

```env
TG_BOT_TOKEN=your_telegram_bot_token
TG_DEFAULT_CHAT_ID=your_telegram_user_or_chat_id
CHECK_INTERVAL_MINUTES=30
```

### 4. 启动机器人

```bash
. venv/bin/activate
export TG_BOT_TOKEN="your_bot_token"
python3 bot.py
```

### 5. 手动执行一次更新检查

```bash
. venv/bin/activate
export TG_BOT_TOKEN="your_bot_token"
python3 check_updates.py
```

## ⚙️ 配置

| 变量名 | 必填 | 说明 |
|---|---|---|
| `TG_BOT_TOKEN` | 是 | Telegram Bot Token |
| `TG_DEFAULT_CHAT_ID` | 否 | 预留变量，当前版本不是强依赖 |
| `CHECK_INTERVAL_MINUTES` | 否 | 检查间隔分钟数，默认示例为 `30` |

> 不要把真实 Token、Chat ID、数据库文件或日志提交到公开仓库。

## 🧩 项目结构

```text
.
├── bot.py                          # Telegram 机器人入口
├── check_updates.py                # 更新检查脚本
├── requirements.txt                # Python 依赖
├── run_bot.sh                      # Bot 启动脚本
├── run_check.sh                    # 检查任务启动脚本
├── appstore-tracker-bot.service    # Bot 的 systemd service
├── appstore-tracker-check.service  # 检查任务 service
├── appstore-tracker-check.timer    # 检查任务 timer
├── .env.example                    # 环境变量示例
├── Dockerfile
├── docker-compose.yml
├── DEPLOYMENT.md                   # 详细部署文档
└── README.md
```

## 📌 使用示例

### 添加追踪

直接把 App Store 链接发给机器人：

```text
https://apps.apple.com/cn/app/qq音乐-听我想听/id414603431
```

### 查看追踪列表

```text
/list
```

### 取消追踪

```text
/canceltrack
/del 1
```

## 🐳 Docker 部署

准备 `.env` 后：

```bash
docker compose up -d
```

更完整的部署说明见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## Author

[@ZenmoFeiShi](https://github.com/ZenmoFeiShi)
