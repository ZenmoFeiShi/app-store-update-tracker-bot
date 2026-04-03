import os
import sqlite3
import hashlib
from datetime import datetime

import requests
from telegram import Bot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.db')
BOT_TOKEN = os.environ['TG_BOT_TOKEN']
APPLE_LOOKUP = 'https://itunes.apple.com/lookup'


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


def notes_hash(text: str):
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


def today_str():
    return datetime.now().strftime('%Y-%m-%d')


def fetch_app(app_id: str, region: str):
    r = requests.get(APPLE_LOOKUP, params={'id': app_id, 'country': region}, timeout=20)
    r.raise_for_status()
    data = r.json()
    results = data.get('results') or []
    if not results:
        return None
    item = results[0]
    notes = (item.get('releaseNotes') or '').strip()
    return {
        'app_name': item.get('trackName') or app_id,
        'version': item.get('version') or '',
        'release_date': item.get('currentVersionReleaseDate') or item.get('releaseDate') or '',
        'notes': notes,
        'notes_hash': notes_hash(notes),
        'url': item.get('trackViewUrl') or '',
    }


def main():
    init_db()
    conn = db()
    rows = conn.execute('SELECT * FROM tracked_apps WHERE is_active=1').fetchall()
    bot = Bot(BOT_TOKEN)
    for row in rows:
        app = fetch_app(row['app_id'], row['region'])
        if not app:
            continue
        changed = (app['version'] != (row['last_version'] or '')) or (app['notes_hash'] != (row['last_notes_hash'] or ''))
        if not changed:
            continue
        text = f"{app['app_name']} 有更新\n版本：{app['version']}\n日期：{today_str()}\n更新内容：\n{app['notes'] or '暂无说明'}\n链接：{row['app_url']}"
        bot.send_message(chat_id=row['chat_id'], text=text)
        conn.execute('UPDATE tracked_apps SET app_name=?, last_version=?, last_release_date=?, last_notes=?, last_notes_hash=?, updated_at=? WHERE id=?', (app['app_name'], app['version'], app['release_date'], app['notes'], app['notes_hash'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), row['id']))
        conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
