"""PostgreSQL katmanı: kullanıcılar, oturumlar ve iş kayıtları."""
import os
from datetime import datetime, date

import psycopg2
import psycopg2.pool
import psycopg2.extras

DATABASE_URL = os.environ["DATABASE_URL"]

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
        )
    return _pool


def _to_str(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


class _CursorWrapper:
    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        row = self._cur.fetchone()
        return {k: _to_str(v) for k, v in row.items()} if row else None

    def fetchall(self):
        return [{k: _to_str(v) for k, v in row.items()} for row in self._cur.fetchall()]

    @property
    def rowcount(self):
        return self._cur.rowcount


class _ConnWrapper:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        return _CursorWrapper(cur)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()


class _ConnCtx:
    def __enter__(self):
        self._conn = _get_pool().getconn()
        return _ConnWrapper(self._conn)

    def __exit__(self, exc_type, *_):
        if exc_type:
            self._conn.rollback()
        _get_pool().putconn(self._conn)


def get_conn():
    return _ConnCtx()


def init_db():
    create_stmts = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plan TEXT NOT NULL DEFAULT 'ucretsiz',
            display_name TEXT,
            avatar TEXT,
            email_verified INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS email_verifications (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS password_resets (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            filename TEXT,
            status TEXT NOT NULL DEFAULT 'queued',
            error TEXT,
            clips_json TEXT,
            style TEXT,
            remove_fillers INTEGER DEFAULT 1,
            smart_crop INTEGER DEFAULT 1,
            auto_zoom INTEGER DEFAULT 1,
            words_json TEXT,
            language TEXT,
            subtitle_color TEXT,
            subtitle_position TEXT,
            aspect TEXT,
            credit_cost INTEGER DEFAULT 0,
            org_id TEXT,
            subtitle_animation TEXT,
            highlight_color TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS org_members (
            org_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (org_id, user_id),
            FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS org_invites (
            token TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
        """,
    ]

    with get_conn() as conn:
        for stmt in create_stmts:
            conn.execute(stmt)
        conn.commit()

    # Eski veritabanlarinda eksik olabilecek kolonlar - varsa sessizce atla.
    alter_stmts = [
        "ALTER TABLE users ADD COLUMN display_name TEXT",
        "ALTER TABLE users ADD COLUMN avatar TEXT",
        "ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE sessions ADD COLUMN expires_at TEXT",
        "ALTER TABLE jobs ADD COLUMN words_json TEXT",
        "ALTER TABLE jobs ADD COLUMN language TEXT",
        "ALTER TABLE jobs ADD COLUMN subtitle_color TEXT",
        "ALTER TABLE jobs ADD COLUMN subtitle_position TEXT",
        "ALTER TABLE jobs ADD COLUMN aspect TEXT",
        "ALTER TABLE jobs ADD COLUMN credit_cost INTEGER DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN org_id TEXT",
        "ALTER TABLE jobs ADD COLUMN subtitle_animation TEXT",
        "ALTER TABLE jobs ADD COLUMN highlight_color TEXT",
        "ALTER TABLE jobs ADD COLUMN smart_crop INTEGER DEFAULT 1",
        "ALTER TABLE jobs ADD COLUMN auto_zoom INTEGER DEFAULT 1",
    ]
    for stmt in alter_stmts:
        try:
            with get_conn() as conn:
                conn.execute(stmt)
                conn.commit()
        except Exception:
            pass


CUSTOMIZABLE_CLIP_PLANS = {"yaratici", "ajans"}

AVATAR_OPTIONS = [
    "bolt", "flame", "spark", "comet", "clip", "wave",
    "gem", "crown", "rocket", "shield", "infinity", "moon",
    "sun", "target", "pulse", "orbit",
]
