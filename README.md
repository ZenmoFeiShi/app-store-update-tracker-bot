# App Store Update Tracker Bot

一个用 Telegram Bot 追踪 Apple App Store 应用更新的轻量项目。

用户把 App Store 链接发给机器人后，机器人会自动记录该 App，并由定时任务持续检查版本变化；一旦发现新版本，就把更新内容和日期推送到 Telegram。

## 功能

- 发送 App Store 链接后自动加入追踪
- 自动解析 App ID 和国家/地区
- 同一用户重复添加时自动去重
- `/list` 查看当前追踪列表
- `/canceltrack` 查看可删除列表
- `/del <编号>` 取消追踪指定 App
- 定时检查版本号和更新说明是否变化
- 有更新时自动推送到 Telegram
- SQLite 本地存储，部署简单

## 工作流程

1. 用户发送 App Store 链接给机器人
2. 机器人解析链接里的 `app_id` 和 `region`
3. 调用 Apple iTunes Lookup API 获取当前 App 信息
4. 把追踪信息写入 SQLite
5. 定时任务轮询所有追踪项
6. 如果版本号或更新说明发生变化，就推送 Telegram 消息
7. 推送完成后回写最新版本信息，避免重复通知

## 技术栈

- Python 3
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- requests
- SQLite
- systemd

## 项目结构

```text
.
├── bot.py                          # Telegram 机器人入口
├── check_updates.py                # 更新检查脚本
├── requirements.txt                # Python 依赖
├── run_bot.sh                      # bot 启动脚本
├── run_check.sh                    # 检查任务启动脚本
├── appstore-tracker-bot.service    # bot 的 systemd service
├── appstore-tracker-check.service  # 检查任务 service
├── appstore-tracker-check.timer    # 检查任务 timer
├── .env.example                    # 环境变量示例
├── .gitignore
└── README.md
```

## 环境变量

参考 `.env.example`：

```env
TG_BOT_TOKEN=your_telegram_bot_token
TG_DEFAULT_CHAT_ID=your_telegram_user_or_chat_id
CHECK_INTERVAL_MINUTES=30
```

实际代码当前使用到：

- `TG_BOT_TOKEN`：Telegram Bot Token
- `TG_DEFAULT_CHAT_ID`：预留变量，当前版本不是强依赖

> 不要把真实 Token、Chat ID、数据库文件提交到公开仓库。

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/yourname/appstore-telegram-tracker.git
cd appstore-telegram-tracker
```

### 2. 创建虚拟环境并安装依赖

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

最简单的方式：

```bash
export TG_BOT_TOKEN="your_bot_token"
export TG_DEFAULT_CHAT_ID="your_chat_id"
```

也可以自己写到 `.env`、systemd Environment、或 shell profile 中。

## 本地运行

启动机器人：

```bash
. venv/bin/activate
export TG_BOT_TOKEN="your_bot_token"
python3 bot.py
```

手动执行一次更新检查：

```bash
. venv/bin/activate
export TG_BOT_TOKEN="your_bot_token"
python3 check_updates.py
```

## Telegram 使用方式

### 添加追踪

直接把 App Store 链接发给机器人，例如：

```text
https://apps.apple.com/cn/app/qq音乐-听我想听/id414603431
```

机器人会回复：

```text
已加入追踪：QQ音乐
当前版本：x.x.x
```

### 查看追踪列表

```text
/list
```

### 取消追踪

先看列表：

```text
/canceltrack
```

再删除：

```text
/del 1
```

## 更新通知格式

示例：

```text
QQ音乐 有更新
版本：14.4.0
日期：2026-04-03
更新内容：
修复已知问题，优化播放体验
链接：https://apps.apple.com/...
```

## 数据存储

默认 SQLite 数据库文件：

```text
data.db
```

主要表：`tracked_apps`

核心字段：

- `user_id`
- `chat_id`
- `app_id`
- `region`
- `app_name`
- `app_url`
- `last_version`
- `last_release_date`
- `last_notes`
- `last_notes_hash`
- `is_active`
- `created_at`
- `updated_at`

## Docker 部署

### 1. 准备环境变量

新建 `.env`：

```env
TG_BOT_TOKEN=your_bot_token
TG_DEFAULT_CHAT_ID=your_chat_id
CHECK_INTERVAL_MINUTES=30
```

### 2. 启动

```bash
docker compose up -d --build
```

### 3. 查看日志

```bash
docker compose logs -f appstore-bot
docker compose logs -f appstore-checker
```

### 4. 停止

```bash
docker compose down
```

### 5. 数据持久化

SQLite 数据库会保存在：

```text
./data/data.db
```

## systemd 部署

见单独文档：[`DEPLOYMENT.md`](./DEPLOYMENT.md)

## 当前实现说明

当前版本使用 Apple 的 iTunes Lookup API：

```text
https://itunes.apple.com/lookup?id=<APP_ID>&country=<REGION>
```

更新判定逻辑：

- 版本号变化，或
- 更新说明内容变化

两者任一满足就触发通知。

## 已知限制

- 当前删除逻辑是 `/del <编号>`，还不是对话式删除
- `CHECK_INTERVAL_MINUTES` 目前只在文档中预留，systemd timer 仍使用固定值
- SQLite 更适合单机、小规模使用
- App Store 某些地区返回字段可能不同
- 同一 App 在不同区服的版本信息可能不一致

## 安全建议

- Bot Token 泄露后要立刻重置
- 不要把 `.env`、数据库、日志直接提交到 GitHub
- 如果仓库已误提交敏感信息，除了删除文件，还要立刻轮换密钥

## 后续可扩展

- 支持 PostgreSQL / MySQL
- 支持多用户管理后台
- 支持更自然的删除交互
- 支持自定义检查频率
- 支持 Docker 部署
- 支持 Webhook 模式
- 支持更丰富的通知模板

## License

MIT
