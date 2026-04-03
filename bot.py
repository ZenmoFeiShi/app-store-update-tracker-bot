import os
import re
import json
import sqlite3
import hashlib
from datetime import datetime
from urllib.parse import urlparse

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.db')
BOT_TOKEN = os.environ['TG_BOT_TOKEN']
DEFAULT_CHAT_ID = os.environ.get('TG_DEFAULT_CHAT_ID', '').strip()
APPLE_LOOKUP = 'https://itunes.apple.com/lookup'
APP_RE = re.compile(r'/id(\d+)')


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.execute('''CREATE TABLE IF NOT EXISTS tracked_apps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        chat_id TEXT NOT NULL,
        app_id TEXT NOT NULL,
        region TEXT NOT NULL,
        app_name TEXT,
        app_url TEXT NOT NULL,
        last_version TEXT,
        last_release_date TEXT,
        last_notes TEXT,
        last_notes_hash TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, app_id, region)
    )''')
    conn.commit()
    conn.close()


def parse_app_url(text: str):
    text = text.strip()
    m = APP_RE.search(text)
    if not m:
        return None
    app_id = m.group(1)
    parsed = urlparse(text)
    parts = [p for p in parsed.path.split('/') if p]
    region = 'cn'
    if len(parts) >= 2 and len(parts[0]) == 2:
        region = parts[0]
    return {'app_id': app_id, 'region': region, 'url': text}


def fetch_app(app_id: str, region: str):
    r = requests.get(APPLE_LOOKUP, params={'id': app_id, 'country': region}, timeout=20)
    r.raise_for_status()
    data = r.json()
    results = data.get('results') or []
    if not results:
        return None
    item = results[0]
    notes = item.get('releaseNotes') or ''
    return {
        'app_name': item.get('trackName') or item.get('artistName') or app_id,
        'version': item.get('version') or '',
        'release_date': item.get('currentVersionReleaseDate') or item.get('releaseDate') or '',
        'notes': notes.strip(),
        'url': item.get('trackViewUrl') or '',
    }


def notes_hash(text: str):
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('发 App Store 链接给我即可开始追踪。\n命令：/list 查看，/canceltrack 取消追踪')


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    conn = db()
    rows = conn.execute('SELECT id, app_name, region, last_version FROM tracked_apps WHERE user_id=? AND is_active=1 ORDER BY id', (uid,)).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text('当前没有追踪中的 App。')
        return
    lines = ['当前追踪列表：']
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. {row['app_name']} [{row['region']}] v{row['last_version'] or '-'}")
    lines.append('发送 /del 编号 进行删除，例如：/del 1')
    await update.message.reply_text('\n'.join(lines))


async def canceltrack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await list_cmd(update, context)


async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    conn = db()
    rows = conn.execute('SELECT id, app_name FROM tracked_apps WHERE user_id=? AND is_active=1 ORDER BY id', (uid,)).fetchall()
    if not context.args:
        conn.close()
        await update.message.reply_text('用法：/del 编号')
        return
    try:
        idx = int(context.args[0])
    except ValueError:
        conn.close()
        await update.message.reply_text('编号不对。')
        return
    if idx < 1 or idx > len(rows):
        conn.close()
        await update.message.reply_text('编号超出范围。')
        return
    row = rows[idx - 1]
    conn.execute('UPDATE tracked_apps SET is_active=0, updated_at=? WHERE id=?', (now_str(), row['id']))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"已取消追踪：{row['app_name']}")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    parsed = parse_app_url(text)
    if not parsed:
        await update.message.reply_text('请直接发 App Store 链接，或用 /list 查看。')
        return
    app = fetch_app(parsed['app_id'], parsed['region'])
    if not app:
        await update.message.reply_text('没查到这个 App，请确认链接。')
        return
    uid = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    conn = db()
    existing = conn.execute('SELECT id, is_active FROM tracked_apps WHERE user_id=? AND app_id=? AND region=?', (uid, parsed['app_id'], parsed['region'])).fetchone()
    ts = now_str()
    nh = notes_hash(app['notes'])
    if existing:
        conn.execute('UPDATE tracked_apps SET is_active=1, chat_id=?, app_name=?, app_url=?, last_version=?, last_release_date=?, last_notes=?, last_notes_hash=?, updated_at=? WHERE id=?', (chat_id, app['app_name'], parsed['url'], app['version'], app['release_date'], app['notes'], nh, ts, existing['id']))
        msg = f"已在追踪中：{app['app_name']}\n当前版本：{app['version']}"
    else:
        conn.execute('INSERT INTO tracked_apps (user_id, chat_id, app_id, region, app_name, app_url, last_version, last_release_date, last_notes, last_notes_hash, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)', (uid, chat_id, parsed['app_id'], parsed['region'], app['app_name'], parsed['url'], app['version'], app['release_date'], app['notes'], nh, ts, ts))
        msg = f"已加入追踪：{app['app_name']}\n当前版本：{app['version']}"
    conn.commit()
    conn.close()
    await update.message.reply_text(msg)


def build_app():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start_cmd))
    app.add_handler(CommandHandler('list', list_cmd))
    app.add_handler(CommandHandler('canceltrack', canceltrack_cmd))
    app.add_handler(CommandHandler('del', del_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    return app


if __name__ == '__main__':
    build_app().run_polling(drop_pending_updates=True)
