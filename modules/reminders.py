"""
Reminders management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Body
from pydantic import BaseModel
from datetime import datetime
from .database import get_db_connection, execute_query
import sqlite3


class Reminder(BaseModel):
    """Reminder model"""
    title: str
    description: Optional[str] = None
    patient_id: Optional[int] = None
    therapist_id: Optional[int] = None
    appointment_id: Optional[str] = None
    due_date: Optional[str] = None
    recurrence: str = "None"
    visibility: str = "private"
    priority: str = "normal"
    colour: str = "#2D6356"
    notify: bool = False
    notify_at: Optional[str] = None


class ReminderUpdate(BaseModel):
    """Reminder update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    patient_id: Optional[int] = None
    therapist_id: Optional[int] = None
    appointment_id: Optional[str] = None
    due_date: Optional[str] = None
    recurrence: Optional[str] = None
    completed: Optional[bool] = None
    visibility: Optional[str] = None
    priority: Optional[str] = None
    colour: Optional[str] = None
    notify: Optional[bool] = None
    notify_at: Optional[str] = None


# ===== REMINDER MANAGEMENT FUNCTIONS =====

def get_all_reminders(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all reminders, optionally filtered by user
    
    Args:
        user_id: Optional user ID to filter by
        
    Returns:
        List of reminder dictionaries
    """
    if user_id:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            WHERE created_by_user_id = ? OR visibility IN ('team', 'patient')
            ORDER BY due_date ASC, timestamp DESC
        """
        results = execute_query(query, (user_id,), fetch='all')
    else:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            ORDER BY due_date ASC, timestamp DESC
        """
        results = execute_query(query, fetch='all')
    
    return [dict(row) for row in results] if results else []


def create_reminder(reminder_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Create a new reminder
    
    Args:
        reminder_data: Dictionary containing reminder information
        user_id: ID of the user creating the reminder
        
    Returns:
        Success response with new ID
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (title, description, created_by_user_id, patient_id, 
                                 therapist_id, appointment_id, due_date, recurrence, 
                                 visibility, priority, colour, notify, notify_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reminder_data.get('title'),
            reminder_data.get('description'),
            user_id,
            reminder_data.get('patient_id'),
            reminder_data.get('therapist_id'),
            reminder_data.get('appointment_id'),
            reminder_data.get('due_date'),
            reminder_data.get('recurrence', 'None'),
            reminder_data.get('visibility', 'private'),
            reminder_data.get('priority', 'normal'),
            reminder_data.get('colour', '#2D6356'),
            reminder_data.get('notify', False),
            reminder_data.get('notify_at')
        ))
        new_id = cursor.lastrowid
        conn.commit()
        return {"id": new_id, "detail": "Reminder created successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create reminder: {str(e)}")
    finally:
        conn.close()


def get_reminder_by_id(reminder_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a reminder by ID
    
    Args:
        reminder_id: The reminder ID
        
    Returns:
        Reminder dictionary or None if not found
    """
    query = """
        SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
               appointment_id, due_date, recurrence, completed, completed_at, 
               visibility, priority, colour, notify, notify_at, timestamp
        FROM reminders WHERE id = ?
    """
    result = execute_query(query, (reminder_id,), fetch='one')
    return dict(result) if result else None


def update_reminder(reminder_id: int, reminder_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Update an existing reminder
    
    Args:
        reminder_id: The reminder ID to update
        reminder_data: Dictionary containing updated information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If update fails or reminder not found
    """
    # Check if reminder exists
    existing = get_reminder_by_id(reminder_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    valid_fields = [
        'title', 'description', 'patient_id', 'therapist_id', 'appointment_id',
        'due_date', 'recurrence', 'completed', 'visibility', 'priority', 
        'colour', 'notify', 'notify_at'
    ]
    
    update_fields = [field for field in valid_fields if field in reminder_data]
    if not update_fields:
        return {"detail": "No fields to update"}
    
    conn = get_db_connection()
    try:
        # Handle completed field - set completed_at if marking as completed
        if 'completed' in reminder_data and reminder_data['completed'] and not existing['completed']:
            update_fields.append('completed_at')
            reminder_data['completed_at'] = datetime.utcnow().isoformat()
        elif 'completed' in reminder_data and not reminder_data['completed']:
            # If uncompleting, clear completed_at
            update_fields.append('completed_at') if 'completed_at' not in update_fields else None
            reminder_data['completed_at'] = None
        
        set_clause = ', '.join([f"{field} = ?" for field in update_fields])
        values = [reminder_data[field] for field in update_fields] + [reminder_id]
        
        query = f"UPDATE reminders SET {set_clause} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return {"detail": "Reminder updated successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update reminder: {str(e)}")
    finally:
        conn.close()


def delete_reminder(reminder_id: int) -> Dict[str, str]:
    """
    Delete a reminder
    
    Args:
        reminder_id: The reminder ID to delete
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If deletion fails or reminder not found
    """
    # Check if reminder exists
    existing = get_reminder_by_id(reminder_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        
        return {"detail": "Reminder deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete reminder: {str(e)}")
    finally:
        conn.close()


def get_reminders_by_patient(patient_id: int) -> List[Dict[str, Any]]:
    """
    Get reminders for a specific patient
    
    Args:
        patient_id: The patient ID
        
    Returns:
        List of reminder dictionaries
    """
    query = """
        SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
               appointment_id, due_date, recurrence, completed, completed_at, 
               visibility, priority, colour, notify, notify_at, timestamp
        FROM reminders 
        WHERE patient_id = ? 
        ORDER BY due_date ASC, timestamp DESC
    """
    results = execute_query(query, (patient_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_reminders_by_therapist(therapist_id: int) -> List[Dict[str, Any]]:
    """
    Get reminders for a specific therapist
    
    Args:
        therapist_id: The therapist ID
        
    Returns:
        List of reminder dictionaries
    """
    query = """
        SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
               appointment_id, due_date, recurrence, completed, completed_at, 
               visibility, priority, colour, notify, notify_at, timestamp
        FROM reminders 
        WHERE therapist_id = ? 
        ORDER BY due_date ASC, timestamp DESC
    """
    results = execute_query(query, (therapist_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_reminders_by_appointment(appointment_id: str) -> List[Dict[str, Any]]:
    """
    Get reminders for a specific appointment
    
    Args:
        appointment_id: The appointment ID
        
    Returns:
        List of reminder dictionaries
    """
    query = """
        SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
               appointment_id, due_date, recurrence, completed, completed_at, 
               visibility, priority, colour, notify, notify_at, timestamp
        FROM reminders 
        WHERE appointment_id = ? 
        ORDER BY due_date ASC, timestamp DESC
    """
    results = execute_query(query, (appointment_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_pending_reminders(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get pending (not completed) reminders
    
    Args:
        user_id: Optional user ID to filter by
        
    Returns:
        List of pending reminder dictionaries
    """
    if user_id:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            WHERE completed = 0 AND (created_by_user_id = ? OR visibility IN ('team', 'patient'))
            ORDER BY due_date ASC, priority DESC, timestamp DESC
        """
        results = execute_query(query, (user_id,), fetch='all')
    else:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            WHERE completed = 0 
            ORDER BY due_date ASC, priority DESC, timestamp DESC
        """
        results = execute_query(query, fetch='all')
    
    return [dict(row) for row in results] if results else []


def get_overdue_reminders(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get overdue reminders (past due date and not completed)
    
    Args:
        user_id: Optional user ID to filter by
        
    Returns:
        List of overdue reminder dictionaries
    """
    current_date = datetime.now().date().isoformat()
    
    if user_id:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            WHERE completed = 0 AND due_date < ? 
            AND (created_by_user_id = ? OR visibility IN ('team', 'patient'))
            ORDER BY due_date ASC
        """
        results = execute_query(query, (current_date, user_id), fetch='all')
    else:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            WHERE completed = 0 AND due_date < ? 
            ORDER BY due_date ASC
        """
        results = execute_query(query, (current_date,), fetch='all')
    
    return [dict(row) for row in results] if results else []


def mark_reminder_completed(reminder_id: int) -> Dict[str, str]:
    """
    Mark a reminder as completed
    
    Args:
        reminder_id: The reminder ID to mark as completed
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If update fails or reminder not found
    """
    return update_reminder(reminder_id, {
        'completed': True,
        'completed_at': datetime.utcnow().isoformat()
    })


def search_reminders(search_term: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Search reminders by title or description
    
    Args:
        search_term: The search term
        user_id: Optional user ID to filter by
        
    Returns:
        List of matching reminder dictionaries
    """
    search_pattern = f"%{search_term}%"
    
    if user_id:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            WHERE (title LIKE ? OR description LIKE ?) 
            AND (created_by_user_id = ? OR visibility IN ('team', 'patient'))
            ORDER BY due_date ASC, timestamp DESC
        """
        params = (search_pattern, search_pattern, user_id)
    else:
        query = """
            SELECT id, title, description, created_by_user_id, patient_id, therapist_id, 
                   appointment_id, due_date, recurrence, completed, completed_at, 
                   visibility, priority, colour, notify, notify_at, timestamp
            FROM reminders 
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY due_date ASC, timestamp DESC
        """
        params = (search_pattern, search_pattern)
    
    results = execute_query(query, params, fetch='all')
    return [dict(row) for row in results] if results else []


def get_reminders_statistics(user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get statistics about reminders
    
    Args:
        user_id: Optional user ID to filter by
        
    Returns:
        Statistics dictionary
    """
    conn = get_db_connection()
    try:
        stats = {}
        
        if user_id:
            # Total reminders for user
            total_result = conn.execute("""
                SELECT COUNT(*) FROM reminders 
                WHERE created_by_user_id = ? OR visibility IN ('team', 'patient')
            """, (user_id,)).fetchone()
            stats['total_reminders'] = total_result[0] if total_result else 0
            
            # Completed reminders
            completed_result = conn.execute("""
                SELECT COUNT(*) FROM reminders 
                WHERE completed = 1 AND (created_by_user_id = ? OR visibility IN ('team', 'patient'))
            """, (user_id,)).fetchone()
            stats['completed_reminders'] = completed_result[0] if completed_result else 0
            
            # Pending reminders
            pending_result = conn.execute("""
                SELECT COUNT(*) FROM reminders 
                WHERE completed = 0 AND (created_by_user_id = ? OR visibility IN ('team', 'patient'))
            """, (user_id,)).fetchone()
            stats['pending_reminders'] = pending_result[0] if pending_result else 0
            
            # Overdue reminders
            current_date = datetime.now().date().isoformat()
            overdue_result = conn.execute("""
                SELECT COUNT(*) FROM reminders 
                WHERE completed = 0 AND due_date < ? 
                AND (created_by_user_id = ? OR visibility IN ('team', 'patient'))
            """, (current_date, user_id)).fetchone()
            stats['overdue_reminders'] = overdue_result[0] if overdue_result else 0
        else:
            # Global statistics
            total_result = conn.execute("SELECT COUNT(*) FROM reminders").fetchone()
            stats['total_reminders'] = total_result[0] if total_result else 0
            
            completed_result = conn.execute("SELECT COUNT(*) FROM reminders WHERE completed = 1").fetchone()
            stats['completed_reminders'] = completed_result[0] if completed_result else 0
            
            pending_result = conn.execute("SELECT COUNT(*) FROM reminders WHERE completed = 0").fetchone()
            stats['pending_reminders'] = pending_result[0] if pending_result else 0
            
            current_date = datetime.now().date().isoformat()
            overdue_result = conn.execute(
                "SELECT COUNT(*) FROM reminders WHERE completed = 0 AND due_date < ?", 
                (current_date,)
            ).fetchone()
            stats['overdue_reminders'] = overdue_result[0] if overdue_result else 0
        
        # Reminders by priority
        if user_id:
            priority_results = conn.execute("""
                SELECT priority, COUNT(*) FROM reminders 
                WHERE created_by_user_id = ? OR visibility IN ('team', 'patient')
                GROUP BY priority
            """, (user_id,)).fetchall()
        else:
            priority_results = conn.execute("""
                SELECT priority, COUNT(*) FROM reminders GROUP BY priority
            """).fetchall()
        
        stats['reminders_by_priority'] = {}
        for priority, count in priority_results:
            stats['reminders_by_priority'][priority] = count
        
        # Reminders by visibility
        if user_id:
            visibility_results = conn.execute("""
                SELECT visibility, COUNT(*) FROM reminders 
                WHERE created_by_user_id = ? OR visibility IN ('team', 'patient')
                GROUP BY visibility
            """, (user_id,)).fetchall()
        else:
            visibility_results = conn.execute("""
                SELECT visibility, COUNT(*) FROM reminders GROUP BY visibility
            """).fetchall()
        
        stats['reminders_by_visibility'] = {}
        for visibility, count in visibility_results:
            stats['reminders_by_visibility'][visibility] = count
        
        return stats
        
    finally:
        conn.close()