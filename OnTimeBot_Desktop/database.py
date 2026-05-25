import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'subscriptions.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_type TEXT NOT NULL,
            sub_data TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def save_subscription(sub_type, sub_data, time_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO subscriptions (sub_type, sub_data, time)
        VALUES (?, ?, ?)
    ''', (sub_type, json.dumps(sub_data, ensure_ascii=False), time_str))

    conn.commit()
    conn.close()


def delete_subscription(sub_type, time_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM subscriptions WHERE sub_type = ? AND time = ?', (sub_type, time_str))

    conn.commit()
    conn.close()


def get_all_subscriptions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT sub_type, sub_data, time FROM subscriptions')
    rows = cursor.fetchall()

    conn.close()

    result = []
    for sub_type, sub_data, time_str in rows:
        result.append({
            'type': sub_type,
            'time': time_str,
            **json.loads(sub_data)
        })

    return result