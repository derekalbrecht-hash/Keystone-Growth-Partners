"""
tools/db.py
PostgreSQL database layer for Keystone Growth Partners website.
Manages two tables: subscribers (email capture) and contacts (contact form).
"""

import os
import logging
import psycopg2
import psycopg2.extras
import psycopg2.errorcodes
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', '')


def get_connection():
    url = DATABASE_URL
    # psycopg2 requires postgresql:// not postgres://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return psycopg2.connect(url, sslmode='require')


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS subscribers (
                        id         SERIAL PRIMARY KEY,
                        email      TEXT NOT NULL UNIQUE,
                        source     TEXT DEFAULT 'cta_form',
                        created_at TEXT NOT NULL,
                        ip_address TEXT
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS contacts (
                        id         SERIAL PRIMARY KEY,
                        name       TEXT NOT NULL,
                        email      TEXT NOT NULL,
                        message    TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        ip_address TEXT
                    );
                """)
        logger.info('Database initialized.')
    except Exception as e:
        logger.error(f'DB init error: {e}')


def insert_subscriber(email: str, ip_address: str = None, source: str = 'cta_form') -> dict:
    """
    Insert a new email subscriber.
    Returns {'success': True, 'id': int} or {'success': False, 'error': str}
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO subscribers (email, source, created_at, ip_address) VALUES (%s, %s, %s, %s) RETURNING id",
                    (email.lower().strip(), source, datetime.now(timezone.utc).isoformat(), ip_address)
                )
                row = cur.fetchone()
                return {'success': True, 'id': row[0]}
    except psycopg2.errors.UniqueViolation:
        return {'success': False, 'error': 'already_subscribed'}
    except Exception as e:
        logger.error(f'insert_subscriber error: {e}')
        return {'success': False, 'error': str(e)}


def insert_contact(name: str, email: str, message: str, ip_address: str = None) -> dict:
    """
    Insert a new contact form submission.
    Returns {'success': True, 'id': int} or {'success': False, 'error': str}
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO contacts (name, email, message, created_at, ip_address) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (name.strip(), email.lower().strip(), message.strip(), datetime.now(timezone.utc).isoformat(), ip_address)
                )
                row = cur.fetchone()
                return {'success': True, 'id': row[0]}
    except Exception as e:
        logger.error(f'insert_contact error: {e}')
        return {'success': False, 'error': str(e)}


def get_all_subscribers() -> list:
    """Return all subscribers as a list of dicts."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM subscribers ORDER BY created_at DESC")
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f'get_all_subscribers error: {e}')
        return []


def get_all_contacts() -> list:
    """Return all contact submissions as a list of dicts."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM contacts ORDER BY created_at DESC")
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f'get_all_contacts error: {e}')
        return []
