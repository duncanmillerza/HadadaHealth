"""
Test configuration and fixtures for HadadaHealth tests
"""
import pytest
import sqlite3
import tempfile
import os
from modules.database import get_db_connection


@pytest.fixture
def test_db():
    """
    Create a temporary test database for testing
    """
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Override the database path for testing
    original_db_path = "data/bookings.db"
    
    try:
        # Create test database connection
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        yield conn, db_path
        
        # Cleanup
        conn.close()
    finally:
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture
def appointment_types_table_setup(test_db):
    """
    Set up appointment_types table for testing
    """
    conn, db_path = test_db
    
    # Create appointment_types table
    conn.execute("""
        CREATE TABLE appointment_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            practice_id INTEGER,
            color TEXT DEFAULT '#2D6356',
            duration INTEGER DEFAULT 30,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES appointment_types(id),
            UNIQUE(name, practice_id, parent_id)
        );
    """)
    
    # Create practices table (needed for foreign key)
    conn.execute("""
        CREATE TABLE practices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    yield conn
    

@pytest.fixture
def practice_appointment_types_table_setup(test_db):
    """
    Set up practice_appointment_types table for testing
    """
    conn, db_path = test_db
    
    # Create practice_appointment_types table
    conn.execute("""
        CREATE TABLE practice_appointment_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            practice_id INTEGER NOT NULL,
            appointment_type_id INTEGER NOT NULL,
            default_duration INTEGER,
            default_billing_code TEXT,
            default_notes TEXT,
            is_enabled BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (practice_id) REFERENCES practices(id),
            FOREIGN KEY (appointment_type_id) REFERENCES appointment_types(id),
            UNIQUE(practice_id, appointment_type_id)
        );
    """)
    
    conn.commit()
    yield conn