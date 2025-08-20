"""
Database utilities and connection management for HadadaHealth
"""
import sqlite3
from typing import Optional, List, Dict, Any


def get_db_connection():
    """
    Get database connection with row factory for dict-like access
    Returns: sqlite3.Connection with Row factory
    """
    conn = sqlite3.connect("data/bookings.db")
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query: str, params: tuple = (), fetch: str = None):
    """
    Execute a database query safely
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch: 'one', 'all', or None for no fetch
    
    Returns:
        Query results based on fetch parameter
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch == 'one':
            result = cursor.fetchone()
        elif fetch == 'all':
            result = cursor.fetchall()
        else:
            result = None
            
        conn.commit()
        return result
    finally:
        conn.close()


def execute_many(query: str, param_list: List[tuple]):
    """
    Execute query with multiple parameter sets
    
    Args:
        query: SQL query string
        param_list: List of parameter tuples
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(query, param_list)
        conn.commit()
    finally:
        conn.close()


def get_table_columns(table_name: str) -> List[str]:
    """
    Get column names for a table
    
    Args:
        table_name: Name of the database table
        
    Returns:
        List of column names
    """
    query = f"PRAGMA table_info({table_name})"
    result = execute_query(query, fetch='all')
    return [row[1] for row in result] if result else []


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        True if table exists, False otherwise
    """
    query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """
    result = execute_query(query, (table_name,), fetch='one')
    return result is not None