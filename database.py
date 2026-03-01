import sqlite3
from datetime import datetime, timedelta

DB_NAME = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_seen TEXT,
        last_seen TEXT,
        messages_count INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def add_or_update_user(user_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        cursor.execute("""
            UPDATE users
            SET last_seen = ?, messages_count = messages_count + 1
            WHERE user_id = ?
        """, (now, user_id))
    else:
        cursor.execute("""
            INSERT INTO users (user_id, username, first_seen, last_seen, messages_count)
            VALUES (?, ?, ?, ?, 1)
        """, (user_id, username, now, now))

    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.utcnow().date().isoformat()
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(first_seen) = ?", (today,))
    new_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE last_seen > ?", (yesterday,))
    active_24h = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(messages_count) FROM users")
    total_messages = cursor.fetchone()[0] or 0

    conn.close()

    return total_users, new_today, active_24h, total_messages