"""
tools/db.py
SQLite database layer for Keystone Growth Partners website.
Manages two tables: subscribers (email capture) and contacts (contact form).
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'keystone.db')


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Called once at server startup."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT NOT NULL UNIQUE,
            source      TEXT DEFAULT 'cta_form',
            created_at  TEXT NOT NULL,
            ip_address  TEXT
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT NOT NULL,
            message     TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            ip_address  TEXT
        );
    """)
    conn.commit()
    conn.close()


def insert_subscriber(email: str, ip_address: str = None, source: str = 'cta_form') -> dict:
    """
    Insert a new email subscriber.
    Returns {'success': True, 'id': int} or {'success': False, 'error': str}
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subscribers (email, source, created_at, ip_address) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), source, datetime.utcnow().isoformat(), ip_address)
        )
        conn.commit()
        return {'success': True, 'id': cursor.lastrowid}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'already_subscribed'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def insert_contact(name: str, email: str, message: str, ip_address: str = None) -> dict:
    """
    Insert a new contact form submission.
    Returns {'success': True, 'id': int} or {'success': False, 'error': str}
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (name, email, message, created_at, ip_address) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), email.lower().strip(), message.strip(), datetime.utcnow().isoformat(), ip_address)
        )
        conn.commit()
        return {'success': True, 'id': cursor.lastrowid}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def get_all_subscribers() -> list:
    """Return all subscribers as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subscribers ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_contacts() -> list:
    """Return all contact submissions as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
