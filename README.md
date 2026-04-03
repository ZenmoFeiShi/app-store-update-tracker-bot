# appstore-telegram-tracker

一个基于 Telegram Bot 的 App Store 更新追踪器。

功能：
- 发送 App Store 链接后加入追踪
- `/list` 查看已追踪 App
- `/canceltrack` 查看待删除列表
- `/del 1` 按编号取消追踪
- 定时检查版本更新
- 更新后推送：App 名称、版本号、日期、更新内容、链接

## 环境变量

参考 `.env.example`：
- `TG_BOT_TOKEN`
- `TG_DEFAULT_CHAT_ID`
- `CHECK_INTERVAL_MINUTES`

## 本地运行

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
export TG_BOT_TOKEN=xxx
export TG_DEFAULT_CHAT_ID=xxx
python3 bot.py
```

## 定时检查

```bash
. venv/bin/activate
python3 check_updates.py
```

## 部署建议

可用 systemd 分别托管：
- `bot.py`
- `check_updates.py`

## 说明

- 默认使用 Apple iTunes Lookup API 获取应用信息
- 数据库存储为 SQLite
- 提交到公开仓库前不要上传真实 Token、Chat ID、数据库文件
