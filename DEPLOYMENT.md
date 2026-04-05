# 🚀 Deployment Guide

本文说明如何把 `app-store-update-tracker-bot` 部署到 Linux 服务器，并通过 `systemd` 或 Docker 长期运行。

## 📦 系统要求

推荐环境：

- Debian / Ubuntu
- Python 3.9+
- systemd
- Docker / Docker Compose（如使用容器部署）
- 可访问 Telegram 和 Apple 接口的网络环境

## ⚙️ 环境变量

至少需要配置以下变量：

| 变量名 | 必填 | 说明 |
|---|---|---|
| `TG_BOT_TOKEN` | 是 | Telegram Bot Token |
| `TG_DEFAULT_CHAT_ID` | 否 | 预留变量，当前版本不是强依赖 |
| `CHECK_INTERVAL_MINUTES` | 否 | 检查间隔分钟数，示例默认 `30` |

建议使用单独的环境文件保存配置，不要把真实凭据写进仓库。

## 🐍 本地安装

```bash
git clone https://github.com/ZenmoFeiShi/app-store-update-tracker-bot.git
cd app-store-update-tracker-bot
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
chmod +x run_bot.sh run_check.sh
```

## 🛠 systemd 部署

### 1. 准备环境文件

```bash
sudo mkdir -p /etc/appstore-tracker
sudo nano /etc/appstore-tracker/appstore-tracker.env
```

示例内容：

```env
TG_BOT_TOKEN=your_bot_token
TG_DEFAULT_CHAT_ID=your_chat_id
CHECK_INTERVAL_MINUTES=30
```

设置权限：

```bash
sudo chmod 600 /etc/appstore-tracker/appstore-tracker.env
```

### 2. 推荐的 service 配置

#### `appstore-tracker-bot.service`

```ini
[Unit]
Description=App Store Tracker Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/app-store-update-tracker-bot
EnvironmentFile=/etc/appstore-tracker/appstore-tracker.env
ExecStart=/opt/app-store-update-tracker-bot/run_bot.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### `appstore-tracker-check.service`

```ini
[Unit]
Description=App Store Tracker Update Checker
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/app-store-update-tracker-bot
EnvironmentFile=/etc/appstore-tracker/appstore-tracker.env
ExecStart=/opt/app-store-update-tracker-bot/run_check.sh
```

#### `appstore-tracker-check.timer`

```ini
[Unit]
Description=Run App Store Tracker checker every 30 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=30min
Unit=appstore-tracker-check.service
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. 安装 systemd 单元

假设项目目录为：

```text
/opt/app-store-update-tracker-bot
```

执行：

```bash
sudo cp appstore-tracker-bot.service /etc/systemd/system/
sudo cp appstore-tracker-check.service /etc/systemd/system/
sudo cp appstore-tracker-check.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now appstore-tracker-bot.service
sudo systemctl enable --now appstore-tracker-check.timer
sudo systemctl start appstore-tracker-check.service
```

### 4. 查看状态与日志

```bash
systemctl status appstore-tracker-bot.service
systemctl status appstore-tracker-check.timer
journalctl -u appstore-tracker-bot.service -f
journalctl -u appstore-tracker-check.service -f
```

## 🐳 Docker 部署

### 1. 准备 `.env`

```env
TG_BOT_TOKEN=your_bot_token
TG_DEFAULT_CHAT_ID=your_chat_id
CHECK_INTERVAL_MINUTES=30
```

### 2. 启动容器

```bash
docker compose up -d --build
```

### 3. 查看状态和日志

```bash
docker compose ps
docker compose logs -f appstore-bot
docker compose logs -f appstore-checker
```

### 4. 停止容器

```bash
docker compose down
```

### 5. 数据持久化

数据库默认保存在：

```text
./data/data.db
```

### 6. 虚拟环境说明

Docker 镜像构建时会显式创建：

```text
/app/venv
```

依赖会安装到这个虚拟环境中，`run_bot.sh` 与 `run_check.sh` 会直接激活它。

## 🔄 升级方式

### systemd 方式

```bash
cd /opt/app-store-update-tracker-bot
git pull
. venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart appstore-tracker-bot.service
sudo systemctl start appstore-tracker-check.service
```

### Docker 方式

```bash
git pull
docker compose up -d --build
```

## ❓ 常见问题

### 机器人启动失败

优先检查：

- `TG_BOT_TOKEN` 是否正确配置
- 运行目录是否正确
- 依赖是否已安装
- Bot 是否已在 Telegram 中创建并启用

查看日志：

```bash
journalctl -u appstore-tracker-bot.service -n 100 --no-pager
```

### 更新检查失败

可以先手动执行一次：

```bash
cd /opt/app-store-update-tracker-bot
. venv/bin/activate
export TG_BOT_TOKEN="your_bot_token"
python3 check_updates.py
```

### 没收到 Telegram 消息

排查顺序：

1. 机器人是否已启动
2. 用户是否先与 Bot 对话过一次
3. `chat_id` 是否已正确写入数据库
4. 服务器网络是否可访问 Telegram API

## 🔒 安全建议

- 不要把真实 `.env` 提交到 Git
- 不要把 Token、Chat ID、数据库、日志文件上传到公开仓库
- 建议给环境文件设置 `600` 权限
- 如果 Token 泄露，应立即重置并重启服务
