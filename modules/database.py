"""
Database utilities and connection management for HadadaHealth
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union


def get_database_path():
    """
    Get the database path, handling different deployment environments with robust error handling
    """
    # Use environment variable if set (for production deployments like Render)
    db_path = os.environ.get('DATABASE_PATH')
    if db_path and db_path.strip():  # Check for non-empty string
        # Ensure directory exists for specified path
        try:
            db_dir = os.path.dirname(db_path)
            if db_dir:  # Only create if there's a directory component
                os.makedirs(db_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create directory for DATABASE_PATH {db_path}: {e}")
            # Fall through to default logic
        else:
            return db_path
    
    # For local development, use data directory
    if os.path.exists('data') or os.getcwd().endswith('HadadaHealth'):
        db_dir = 'data'
        db_path = os.path.join(db_dir, 'bookings.db')
        
        # Try to create data directory if it doesn't exist
        try:
            os.makedirs(db_dir, exist_ok=True)
            return db_path
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create data directory: {e}")
            # Fall through to /tmp logic
    
    # For production environments with read-only filesystem, use /tmp
    db_dir = '/tmp/hadadahealth'
    db_path = os.path.join(db_dir, 'bookings.db')
    
    # Create directory with robust error handling
    try:
        os.makedirs(db_dir, exist_ok=True)
    except (OSError, PermissionError) as e:
        print(f"Error: Could not create tmp directory {db_dir}: {e}")
        # Last resort - use /tmp directly
        db_path = '/tmp/bookings.db'
        print(f"Falling back to: {db_path}")
    
    # Verify we can write to the directory
    try:
        test_file = os.path.join(os.path.dirname(db_path), '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except (OSError, PermissionError) as e:
        print(f"Warning: Directory {os.path.dirname(db_path)} may not be writable: {e}")
    
    return db_path


def get_db_connection():
    """
    Get database connection with row factory for dict-like access
    Returns: sqlite3.Connection with Row factory
    """
    db_path = get_database_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        print(f"Failed to connect to database at {db_path}: {e}")
        raise RuntimeError(f"Database connection failed: {e}. Path: {db_path}")


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


# Report Writing System Database Helpers

def create_report(patient_id: str, report_type: str, template_id: int, title: str,
                 assigned_therapist_ids: List[str], disciplines: List[str],
                 requested_by_user_id: Optional[str] = None, deadline_date: Optional[str] = None,
                 priority: int = 1) -> int:
    """
    Create a new report entry
    
    Args:
        patient_id: Patient identifier
        report_type: Type of report (progress, discharge, etc.)
        template_id: ID of template to use
        title: Report title
        assigned_therapist_ids: List of therapist user IDs
        disciplines: List of disciplines involved
        requested_by_user_id: User who requested report (None for therapist-initiated)
        deadline_date: ISO date string for deadline
        priority: Priority level (1-3)
    
    Returns:
        ID of created report
    """
    query = """
    INSERT INTO reports (patient_id, report_type, template_id, title, assigned_therapist_ids,
                        disciplines, requested_by_user_id, deadline_date, priority)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (
            patient_id, report_type, template_id, title,
            json.dumps(assigned_therapist_ids), json.dumps(disciplines),
            requested_by_user_id, deadline_date, priority
        ))
        report_id = cursor.lastrowid
        conn.commit()
        return report_id
    finally:
        conn.close()


def get_report_by_id(report_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific report by its ID
    
    Args:
        report_id: ID of the report to retrieve
    
    Returns:
        Report dictionary if found, None otherwise
    """
    query = """
    SELECT r.*, 
           rt.name as template_name,
           rt.template_type
    FROM reports r
    LEFT JOIN report_templates rt ON r.template_id = rt.id
    WHERE r.id = ?
    """
    
    result = execute_query(query, (report_id,), fetch='one')
    return dict(result) if result else None


def get_reports_for_user(user_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get reports assigned to or requested by a user
    
    Args:
        user_id: User ID to filter by
        status: Optional status filter
        limit: Maximum number of reports to return
    
    Returns:
        List of report dictionaries with parsed JSON fields
    """
    base_query = """
    SELECT r.*, rt.name as template_name, rt.template_type
    FROM reports r
    LEFT JOIN report_templates rt ON r.template_id = rt.id
    WHERE (r.assigned_therapist_ids LIKE ? OR r.requested_by_user_id = ?)
    """
    
    params = [f'%"{user_id}"%', user_id]
    
    if status:
        base_query += " AND r.status = ?"
        params.append(status)
    
    base_query += " ORDER BY r.created_at DESC LIMIT ?"
    params.append(limit)
    
    results = execute_query(base_query, tuple(params), fetch='all')
    
    # Parse JSON fields for easier use
    reports = []
    for row in results:
        report = dict(row)
        report['assigned_therapist_ids'] = json.loads(report['assigned_therapist_ids'])
        report['disciplines'] = json.loads(report['disciplines'])
        if report['ai_generated_sections']:
            report['ai_generated_sections'] = json.loads(report['ai_generated_sections'])
        if report['content']:
            report['content'] = json.loads(report['content'])
        reports.append(report)
    
    return reports


def update_report_status(report_id: int, status: str, content: Optional[Dict] = None,
                        user_id: Optional[str] = None) -> bool:
    """
    Update report status and optionally content
    
    Args:
        report_id: ID of report to update
        status: New status
        content: Optional content update
        user_id: User making the update
    
    Returns:
        True if update successful, False otherwise
    """
    if status == 'completed':
        query = """
        UPDATE reports 
        SET status = ?, completed_at = datetime('now'), updated_at = datetime('now')
        WHERE id = ?
        """
        params = (status, report_id)
    else:
        query = """
        UPDATE reports 
        SET status = ?, updated_at = datetime('now')
        WHERE id = ?
        """
        params = (status, report_id)
    
    try:
        execute_query(query, params)
        
        # Update content if provided
        if content:
            content_query = "UPDATE reports SET content = ? WHERE id = ?"
            execute_query(content_query, (json.dumps(content), report_id))
        
        return True
    except Exception:
        return False


def get_report_templates(template_type: Optional[str] = None, practice_id: Optional[str] = None,
                        is_active: bool = True) -> List[Dict[str, Any]]:
    """
    Get available report templates
    
    Args:
        template_type: Filter by template type
        practice_id: Filter by practice (None for system templates)
        is_active: Only return active templates
    
    Returns:
        List of template dictionaries with parsed schemas
    """
    query = "SELECT * FROM report_templates WHERE is_active = ?"
    params = [is_active]
    
    if template_type:
        query += " AND template_type = ?"
        params.append(template_type)
    
    if practice_id:
        query += " AND (practice_id = ? OR practice_id IS NULL)"
        params.append(practice_id)
    
    query += " ORDER BY is_system_default DESC, name ASC"
    
    results = execute_query(query, tuple(params), fetch='all')
    
    # Parse JSON fields
    templates = []
    for row in results:
        template = dict(row)
        template['fields_schema'] = json.loads(template['fields_schema'])
        template['section_order'] = json.loads(template['section_order'])
        templates.append(template)
    
    return templates


def cache_ai_content(patient_id: str, content_type: str, content: str, 
                    discipline: Optional[str] = None, expires_days: int = 7) -> int:
    """
    Cache AI-generated content with expiry
    
    Args:
        patient_id: Patient identifier
        content_type: Type of content (medical_history, treatment_summary, etc.)
        content: The generated content
        discipline: Specific discipline (None for multi-disciplinary)
        expires_days: Days until content expires
    
    Returns:
        ID of cached content
    """
    expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
    source_hash = str(hash(f"{patient_id}_{content_type}_{discipline}"))
    
    query = """
    INSERT INTO ai_content_cache (patient_id, content_type, discipline, content,
                                 source_data_hash, expires_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (patient_id, content_type, discipline, content, source_hash, expires_at))
        cache_id = cursor.lastrowid
        conn.commit()
        return cache_id
    finally:
        conn.close()


def get_cached_ai_content(patient_id: str, content_type: str, 
                         discipline: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached AI content if valid and not expired
    
    Args:
        patient_id: Patient identifier
        content_type: Type of content to retrieve
        discipline: Specific discipline filter
    
    Returns:
        Cached content dictionary or None if not found/expired
    """
    query = """
    SELECT * FROM ai_content_cache 
    WHERE patient_id = ? AND content_type = ? AND is_valid = 1 
    AND expires_at > datetime('now')
    """
    params = [patient_id, content_type]
    
    if discipline:
        query += " AND discipline = ?"
        params.append(discipline)
    else:
        query += " AND discipline IS NULL"
    
    query += " ORDER BY generated_at DESC LIMIT 1"
    
    result = execute_query(query, tuple(params), fetch='one')
    
    if result:
        # Update usage count
        execute_query(
            "UPDATE ai_content_cache SET usage_count = usage_count + 1, last_used_at = datetime('now') WHERE id = ?",
            (result['id'],)
        )
        return dict(result)
    
    return None


def create_report_notification(report_id: int, user_id: str, notification_type: str, 
                             message: str) -> int:
    """
    Create a report notification
    
    Args:
        report_id: ID of related report
        user_id: User to notify
        notification_type: Type of notification
        message: Notification message
    
    Returns:
        ID of created notification
    """
    query = """
    INSERT INTO report_notifications (report_id, user_id, notification_type, message)
    VALUES (?, ?, ?, ?)
    """
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (report_id, user_id, notification_type, message))
        notification_id = cursor.lastrowid
        conn.commit()
        return notification_id
    finally:
        conn.close()


def get_user_notifications(user_id: str, is_read: Optional[bool] = None, 
                          limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get notifications for a user
    
    Args:
        user_id: User ID
        is_read: Filter by read status (None for all)
        limit: Maximum notifications to return
    
    Returns:
        List of notification dictionaries
    """
    query = """
    SELECT n.*, r.title as report_title, r.patient_id
    FROM report_notifications n
    JOIN reports r ON n.report_id = r.id
    WHERE n.user_id = ?
    """
    params = [user_id]
    
    if is_read is not None:
        query += " AND n.is_read = ?"
        params.append(is_read)
    
    query += " ORDER BY n.created_at DESC LIMIT ?"
    params.append(limit)
    
    results = execute_query(query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


def mark_notification_read(notification_id: int) -> bool:
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of notification to mark as read
    
    Returns:
        True if successful, False otherwise
    """
    query = "UPDATE report_notifications SET is_read = 1, read_at = datetime('now') WHERE id = ?"
    
    try:
        execute_query(query, (notification_id,))
        return True
    except Exception:
        return False


def get_patient_disciplines(patient_id: str) -> List[Dict[str, Any]]:
    """
    Get disciplines that have treated a patient (placeholder - would integrate with existing patient data)
    
    Args:
        patient_id: Patient identifier
    
    Returns:
        List of disciplines with treatment info
    """
    # This is a placeholder implementation
    # In a real system, this would query treatment notes, appointments, etc.
    # For now, return sample data structure
    return [
        {
            'discipline': 'physiotherapy',
            'therapist_ids': ['THER001'],
            'last_treatment_date': '2025-08-20',
            'treatment_count': 5
        },
        {
            'discipline': 'occupational_therapy',
            'therapist_ids': ['THER002'],
            'last_treatment_date': '2025-08-18',
            'treatment_count': 3
        }
    ]


def delete_report(report_id: int) -> bool:
    """
    Delete a report and all associated data
    
    Args:
        report_id: ID of report to delete
    
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Delete in correct order due to foreign key constraints
        # 1. Delete report notifications
        cursor.execute("DELETE FROM report_notifications WHERE report_id = ?", (report_id,))
        
        # 2. Delete report content versions
        cursor.execute("DELETE FROM report_content_versions WHERE report_id = ?", (report_id,))
        
        # 3. Skip AI content cache - it's not tied to specific reports
        # (AI content cache is organized by patient_id and content_type, not report_id)
        
        # 4. Finally delete the report itself
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        
        # Check if any rows were affected
        if cursor.rowcount == 0:
            return False
            
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error deleting report {report_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()