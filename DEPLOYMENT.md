# Deployment Guide

这份文档说明如何把 `appstore-telegram-tracker` 部署到 Linux 服务器，并用 `systemd` 常驻运行。

## 1. 系统要求

推荐环境：

- Debian / Ubuntu
- Python 3.9+
- systemd
- 可访问 Telegram 和 Apple 接口的网络环境

## 2. 安装项目

```bash
git clone https://github.com/yourname/appstore-telegram-tracker.git
cd appstore-telegram-tracker
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## 3. 配置环境变量

你至少需要设置：

- `TG_BOT_TOKEN`
- `TG_DEFAULT_CHAT_ID`（可选）

### 方式 A：当前 shell 临时设置

```bash
export TG_BOT_TOKEN="your_bot_token"
export TG_DEFAULT_CHAT_ID="your_chat_id"
```

### 方式 B：写入 systemd Environment 文件

新建：

```bash
sudo mkdir -p /etc/appstore-tracker
sudo nano /etc/appstore-tracker/appstore-tracker.env
```

内容示例：

```env
TG_BOT_TOKEN=your_bot_token
TG_DEFAULT_CHAT_ID=your_chat_id
```

权限建议：

```bash
sudo chmod 600 /etc/appstore-tracker/appstore-tracker.env
```

## 4. 配置启动脚本

给脚本执行权限：

```bash
chmod +x run_bot.sh run_check.sh
```

如果你采用 systemd Environment 文件方式，建议把 service 文件改成这样：

### appstore-tracker-bot.service

```ini
[Unit]
Description=App Store Tracker Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/appstore-telegram-tracker
EnvironmentFile=/etc/appstore-tracker/appstore-tracker.env
ExecStart=/opt/appstore-telegram-tracker/run_bot.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### appstore-tracker-check.service

```ini
[Unit]
Description=App Store Tracker Update Checker
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/appstore-telegram-tracker
EnvironmentFile=/etc/appstore-tracker/appstore-tracker.env
ExecStart=/opt/appstore-telegram-tracker/run_check.sh
```

### appstore-tracker-check.timer

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

## 5. 安装 systemd 单元

假设项目目录是：

```text
/opt/appstore-telegram-tracker
```

复制 unit 文件：

```bash
sudo cp appstore-tracker-bot.service /etc/systemd/system/
sudo cp appstore-tracker-check.service /etc/systemd/system/
sudo cp appstore-tracker-check.timer /etc/systemd/system/
```

然后重载并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now appstore-tracker-bot.service
sudo systemctl enable --now appstore-tracker-check.timer
sudo systemctl start appstore-tracker-check.service
```

## 6. 检查运行状态

查看 bot：

```bash
systemctl status appstore-tracker-bot.service
```

查看 timer：

```bash
systemctl status appstore-tracker-check.timer
```

查看日志：

```bash
journalctl -u appstore-tracker-bot.service -f
journalctl -u appstore-tracker-check.service -f
```

## 7. 升级项目

```bash
cd /opt/appstore-telegram-tracker
git pull
. venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart appstore-tracker-bot.service
sudo systemctl start appstore-tracker-check.service
```

## 8. 常见问题

### 机器人启动失败

先检查环境变量是否存在：

```bash
grep TG_BOT_TOKEN /etc/appstore-tracker/appstore-tracker.env
```

再看日志：

```bash
journalctl -u appstore-tracker-bot.service -n 100 --no-pager
```

### 更新检查失败

先手动跑一遍：

```bash
cd /opt/appstore-telegram-tracker
. venv/bin/activate
export TG_BOT_TOKEN="your_bot_token"
python3 check_updates.py
```

### 没收到 Telegram 消息

排查顺序：

1. 机器人是否已启动
2. 用户是否先和 Bot 对话过一次
3. `chat_id` 是否正确写入数据库
4. 服务器网络是否可访问 Telegram API

## 9. 安全建议

- 不要把真实 Token 写进仓库
- 不要把 `.env` 提交到 Git
- 对环境文件设置 `600` 权限
- 如果 Token 泄露，立刻重置并重启服务

## 10. 生产建议

如果你准备长期使用，建议再补：

- 自动备份 SQLite
- 日志轮转
- 更细的异常处理
- 健康检查
- Dockerfile / docker-compose
- 多用户权限控制
