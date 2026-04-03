#!/bin/sh
cd "$(dirname "$0")" || exit 1
. venv/bin/activate
[ -n "$TG_BOT_TOKEN" ] || exit 1
exec python3 bot.py
