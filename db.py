"""
db.py – MySQL connection pool helper for CampusSkill.
"""
import mysql.connector
from mysql.connector import pooling, Error
from config import Config

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="campusskill_pool",
            pool_size=5,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=False,
        )
    return _pool


def get_db():
    """Return a connection from the pool."""
    return get_pool().get_connection()


def query_one(sql, params=()):
    """Execute SELECT and return first row as dict, or None."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def query_all(sql, params=()):
    """Execute SELECT and return all rows as list of dicts."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def execute(sql, params=(), lastrowid=False):
    """Execute INSERT / UPDATE / DELETE and commit. Returns lastrowid if requested."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid if lastrowid else cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def execute_many(statements):
    """
    Execute a list of (sql, params) tuples in one transaction.
    statements = [(sql1, params1), (sql2, params2), ...]
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        for sql, params in statements:
            cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
