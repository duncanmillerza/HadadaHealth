"""
Database utilities and connection management for HadadaHealth
"""
import sqlite3
from typing import Dict, Any, List


def get_db_connection():
    """Helper to get DB connection with row_factory as dict"""
    conn = sqlite3.connect("data/bookings.db")
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = True):
    """Execute a database query with error handling"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")


def dict_factory(cursor, row):
    """Convert sqlite3.Row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_dict_connection():
    """Get database connection with dict factory"""
    conn = sqlite3.connect("data/bookings.db")
    conn.row_factory = dict_factory
    return conn