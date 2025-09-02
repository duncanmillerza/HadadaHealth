"""
Database migration runner for HadadaHealth

Handles applying and tracking database schema migrations.
"""
import os
import sys
import sqlite3
from typing import List, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.database import get_db_connection


def get_migration_files() -> List[str]:
    """
    Get list of migration SQL files in order
    
    Returns:
        List of migration file paths in execution order
    """
    migration_dir = os.path.dirname(__file__)
    files = []
    
    for filename in sorted(os.listdir(migration_dir)):
        if filename.endswith('.sql') and filename[0].isdigit():
            files.append(os.path.join(migration_dir, filename))
    
    return files


def create_migration_table():
    """
    Create migrations tracking table if it doesn't exist
    """
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_applied_migrations() -> List[str]:
    """
    Get list of already applied migrations
    
    Returns:
        List of applied migration filenames
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT filename FROM schema_migrations ORDER BY filename")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return []
    finally:
        conn.close()


def apply_migration(filepath: str) -> bool:
    """
    Apply a single migration file
    
    Args:
        filepath: Path to migration SQL file
        
    Returns:
        True if migration was applied successfully, False otherwise
    """
    filename = os.path.basename(filepath)
    
    try:
        # Read migration SQL
        with open(filepath, 'r') as f:
            migration_sql = f.read()
        
        # Apply migration
        conn = get_db_connection()
        try:
            # Execute migration SQL
            conn.executescript(migration_sql)
            
            # Record migration as applied
            conn.execute("""
                INSERT INTO schema_migrations (filename) VALUES (?)
            """, (filename,))
            
            conn.commit()
            print(f"✅ Applied migration: {filename}")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Failed to apply migration {filename}: {e}")
            return False
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Error reading migration file {filepath}: {e}")
        return False


def run_migrations() -> bool:
    """
    Run all pending migrations
    
    Returns:
        True if all migrations applied successfully, False otherwise
    """
    print("🚀 Starting database migrations...")
    
    # Create migration tracking table
    create_migration_table()
    
    # Get migration files and applied migrations
    migration_files = get_migration_files()
    applied_migrations = get_applied_migrations()
    
    if not migration_files:
        print("📋 No migration files found")
        return True
    
    # Apply pending migrations
    applied_count = 0
    for filepath in migration_files:
        filename = os.path.basename(filepath)
        
        if filename not in applied_migrations:
            if apply_migration(filepath):
                applied_count += 1
            else:
                return False
        else:
            print(f"⏭️  Skipping already applied migration: {filename}")
    
    if applied_count > 0:
        print(f"✅ Applied {applied_count} new migration(s)")
    else:
        print("✅ All migrations are up to date")
    
    return True


def rollback_migration(filename: str) -> bool:
    """
    Remove a migration from the applied migrations table
    Note: This doesn't reverse the SQL changes, only removes tracking
    
    Args:
        filename: Migration filename to remove from tracking
        
    Returns:
        True if rollback successful, False otherwise
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            DELETE FROM schema_migrations WHERE filename = ?
        """, (filename,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Rolled back migration tracking: {filename}")
            return True
        else:
            print(f"❌ Migration not found: {filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error rolling back migration {filename}: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # Run migrations when script is executed directly
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        if len(sys.argv) > 2:
            rollback_migration(sys.argv[2])
        else:
            print("Usage: python migration_runner.py rollback <filename>")
    else:
        run_migrations()