import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).with_name("docucheck.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_type TEXT NOT NULL,
                record_key TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(record_type, record_key)
            )
        """)


def save_record(record_type, record_key, data):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO records (record_type, record_key, data)
            VALUES (?, ?, ?)
            ON CONFLICT(record_type, record_key)
            DO UPDATE SET
                data = excluded.data,
                updated_at = CURRENT_TIMESTAMP
        """, (
            record_type,
            str(record_key),
            json.dumps(data, ensure_ascii=False)
        ))


def load_records(record_type):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT record_key, data
            FROM records
            WHERE record_type = ?
            ORDER BY id
        """, (record_type,)).fetchall()

    return [
        {"key": key, "data": json.loads(data)}
        for key, data in rows
    ]