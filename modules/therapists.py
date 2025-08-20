"""
Therapist management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
import pandas as pd
import json
from .database import get_db_connection, execute_query
import sqlite3


class Therapist(BaseModel):
    """Therapist model"""
    name: str
    surname: str
    preferred_name: Optional[str] = None
    profession: str
    cellphone: str
    clinic: str
    email: Optional[str] = None
    hpcsa_number: str
    malpractice_number: str
    malpractice_expiry: Optional[str] = None
    hpcsa_expiry: Optional[str] = None
    date_of_birth: Optional[str] = None
    permissions: Optional[List[str]] = []


def get_all_therapists() -> List[Dict[str, Any]]:
    """
    Get all therapists
    
    Returns:
        List of therapist dictionaries
    """
    query = "SELECT * FROM therapists ORDER BY name, surname"
    results = execute_query(query, fetch='all')
    
    therapists = []
    for row in results:
        therapist = dict(row)
        # Parse permissions JSON if it exists
        if therapist.get('permissions'):
            try:
                therapist['permissions'] = json.loads(therapist['permissions'])
            except (json.JSONDecodeError, TypeError):
                therapist['permissions'] = []
        else:
            therapist['permissions'] = []
        therapists.append(therapist)
    
    return therapists


def get_therapist_by_id(therapist_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a therapist by ID
    
    Args:
        therapist_id: The therapist ID
        
    Returns:
        Therapist dictionary or None if not found
    """
    query = "SELECT * FROM therapists WHERE id = ?"
    result = execute_query(query, (therapist_id,), fetch='one')
    
    if result:
        therapist = dict(result)
        # Parse permissions JSON if it exists
        if therapist.get('permissions'):
            try:
                therapist['permissions'] = json.loads(therapist['permissions'])
            except (json.JSONDecodeError, TypeError):
                therapist['permissions'] = []
        else:
            therapist['permissions'] = []
        return therapist
    
    return None


def get_therapist_basic_info(therapist_id: int) -> Optional[Dict[str, Any]]:
    """
    Get basic therapist information (for displays/dropdowns)
    
    Args:
        therapist_id: The therapist ID
        
    Returns:
        Basic therapist info dictionary or None if not found
    """
    query = """
        SELECT id, name, surname, preferred_name, profession
        FROM therapists 
        WHERE id = ?
    """
    result = execute_query(query, (therapist_id,), fetch='one')
    
    if result:
        return {
            "id": result[0],
            "name": result[1],
            "surname": result[2],
            "preferred_name": result[3],
            "profession": result[4]
        }
    
    return None


def create_therapist(therapist: Therapist) -> int:
    """
    Create a new therapist
    
    Args:
        therapist: Therapist object with therapist details
        
    Returns:
        The ID of the created therapist
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO therapists (
                name, surname, preferred_name, profession, cellphone,
                clinic, email, hpcsa_number, malpractice_number,
                malpractice_expiry, hpcsa_expiry, date_of_birth, permissions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            therapist.name,
            therapist.surname,
            therapist.preferred_name,
            therapist.profession,
            therapist.cellphone,
            therapist.clinic,
            therapist.email,
            therapist.hpcsa_number,
            therapist.malpractice_number,
            therapist.malpractice_expiry,
            therapist.hpcsa_expiry,
            therapist.date_of_birth,
            json.dumps(therapist.permissions or [])
        ))
        
        therapist_id = cursor.lastrowid
        conn.commit()
        return therapist_id
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create therapist: {str(e)}")
    finally:
        conn.close()


def update_therapist(therapist_id: int, therapist_data: Dict[str, Any]) -> bool:
    """
    Update an existing therapist
    
    Args:
        therapist_id: The therapist ID to update
        therapist_data: Dictionary containing updated therapist information
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If update fails or therapist not found
    """
    conn = get_db_connection()
    try:
        # Check if therapist exists
        existing = get_therapist_by_id(therapist_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Therapist not found")
        
        # Build update query
        valid_fields = [
            'name', 'surname', 'preferred_name', 'profession', 'cellphone',
            'clinic', 'email', 'hpcsa_number', 'malpractice_number',
            'malpractice_expiry', 'hpcsa_expiry', 'date_of_birth', 'permissions'
        ]
        
        update_fields = [field for field in valid_fields if field in therapist_data]
        if not update_fields:
            return True  # No fields to update
            
        set_clause = ', '.join([f"{field} = ?" for field in update_fields])
        values = []
        
        for field in update_fields:
            if field == 'permissions':
                # Handle permissions as JSON
                permissions = therapist_data[field]
                if isinstance(permissions, list):
                    values.append(json.dumps(permissions))
                else:
                    values.append(permissions)
            else:
                values.append(therapist_data[field])
        
        values.append(therapist_id)
        
        query = f"UPDATE therapists SET {set_clause} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update therapist: {str(e)}")
    finally:
        conn.close()


def delete_therapist(therapist_id: int) -> bool:
    """
    Delete a therapist
    
    Args:
        therapist_id: The therapist ID to delete
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If deletion fails or therapist not found
    """
    conn = get_db_connection()
    try:
        # Check if therapist exists
        existing = get_therapist_by_id(therapist_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Therapist not found")
        
        # Check if therapist has any bookings (optional safety check)
        bookings_check = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE therapist = ?", 
            (therapist_id,)
        ).fetchone()
        
        if bookings_check and bookings_check[0] > 0:
            # You might want to handle this differently - perhaps soft delete
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete therapist with existing bookings"
            )
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM therapists WHERE id = ?", (therapist_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Therapist not found")
            
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete therapist: {str(e)}")
    finally:
        conn.close()


def get_therapists_by_profession(profession: str) -> List[Dict[str, Any]]:
    """
    Get therapists by profession
    
    Args:
        profession: The profession to filter by
        
    Returns:
        List of therapist dictionaries
    """
    query = """
        SELECT id, name, surname, preferred_name, profession, clinic
        FROM therapists 
        WHERE profession = ?
        ORDER BY name, surname
    """
    results = execute_query(query, (profession,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_therapists_by_clinic(clinic: str) -> List[Dict[str, Any]]:
    """
    Get therapists by clinic
    
    Args:
        clinic: The clinic to filter by
        
    Returns:
        List of therapist dictionaries
    """
    query = """
        SELECT id, name, surname, preferred_name, profession, clinic
        FROM therapists 
        WHERE clinic = ?
        ORDER BY name, surname
    """
    results = execute_query(query, (clinic,), fetch='all')
    return [dict(row) for row in results] if results else []


def import_therapists_from_excel(file: UploadFile) -> Dict[str, Any]:
    """
    Import therapists from Excel file
    
    Args:
        file: The uploaded Excel file
        
    Returns:
        Import results summary
        
    Raises:
        HTTPException: If import fails
    """
    try:
        # Read Excel file
        df = pd.read_excel(file.file)
        
        # Validate required columns
        required_columns = ['name', 'surname', 'profession', 'cellphone', 'clinic']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Convert row to dict and handle NaN values
                therapist_data = row.to_dict()
                therapist_data = {k: (v if pd.notna(v) else None) for k, v in therapist_data.items()}
                
                # Handle permissions if present
                if 'permissions' in therapist_data and therapist_data['permissions']:
                    if isinstance(therapist_data['permissions'], str):
                        # Convert comma-separated string to list
                        permissions = [perm.strip() for perm in therapist_data['permissions'].split(',')]
                        therapist_data['permissions'] = permissions
                
                # Create Therapist object and save
                therapist = Therapist(**therapist_data)
                create_therapist(therapist)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return {
            "imported_count": imported_count,
            "total_rows": len(df),
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")


def get_therapist_stats() -> List[Dict[str, Any]]:
    """
    Get statistics for all therapists
    
    Returns:
        List of therapist statistics dictionaries
    """
    # First try the original view if it exists
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT * FROM therapist_stats_view")
        cols = [c[0] for c in cur.description]
        results = [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        return results
    except:
        # Fallback to a simpler query if view doesn't exist
        query = """
            SELECT 
                t.id as therapist_id,
                t.name,
                t.surname,
                t.profession,
                COUNT(DISTINCT b.id) as total_appointments,
                COUNT(DISTINCT CASE WHEN b.date >= date('now', '-30 days') THEN b.id END) as recent_appointments_30d,
                COUNT(DISTINCT CASE WHEN tn.appointment_id IS NOT NULL THEN tn.appointment_id END) as completed_notes,
                COUNT(DISTINCT CASE WHEN tn.appointment_id IS NOT NULL AND b.date >= date('now', '-30 days') THEN tn.appointment_id END) as completed_notes_30d
            FROM therapists t
            LEFT JOIN bookings b ON t.id = b.therapist
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            GROUP BY t.id, t.name, t.surname, t.profession
            ORDER BY t.name, t.surname
        """
        
        results = execute_query(query, fetch='all')
        return [dict(row) for row in results] if results else []


def get_therapist_schedule(therapist_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get therapist schedule for a date range
    
    Args:
        therapist_id: The therapist ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of appointment dictionaries for the therapist
    """
    query = """
        SELECT b.*, p.first_name, p.surname,
               CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END AS has_note
        FROM bookings b
        LEFT JOIN patients p ON b.patient_id = p.id
        LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
        WHERE b.therapist = ? AND b.date >= ? AND b.date <= ?
        ORDER BY b.date, b.time
    """
    
    results = execute_query(query, (therapist_id, start_date, end_date), fetch='all')
    return [dict(row) for row in results] if results else []


def search_therapists(search_term: str) -> List[Dict[str, Any]]:
    """
    Search therapists by name, profession, or clinic
    
    Args:
        search_term: The search term
        
    Returns:
        List of matching therapist dictionaries
    """
    search_pattern = f"%{search_term}%"
    query = """
        SELECT id, name, surname, preferred_name, profession, clinic, email
        FROM therapists
        WHERE 
            name LIKE ? OR 
            surname LIKE ? OR 
            preferred_name LIKE ? OR
            profession LIKE ? OR
            clinic LIKE ?
        ORDER BY name, surname
    """
    
    params = [search_pattern] * 5
    results = execute_query(query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


def get_unique_professions() -> List[str]:
    """
    Get list of unique professions from therapists
    
    Returns:
        List of profession names
    """
    query = "SELECT DISTINCT profession FROM therapists WHERE profession IS NOT NULL ORDER BY profession"
    results = execute_query(query, fetch='all')
    return [row[0] for row in results] if results else []


def get_unique_clinics() -> List[str]:
    """
    Get list of unique clinics from therapists
    
    Returns:
        List of clinic names
    """
    query = "SELECT DISTINCT clinic FROM therapists WHERE clinic IS NOT NULL ORDER BY clinic"
    results = execute_query(query, fetch='all')
    return [row[0] for row in results] if results else []


def get_therapist_workload(therapist_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Get therapist workload statistics for a date range
    
    Args:
        therapist_id: The therapist ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Workload statistics dictionary
    """
    query = """
        SELECT 
            COUNT(*) as total_appointments,
            SUM(b.duration) as total_minutes,
            COUNT(DISTINCT b.date) as working_days,
            COUNT(CASE WHEN tn.appointment_id IS NOT NULL THEN 1 END) as completed_notes,
            COUNT(CASE WHEN b.billing_completed = 1 THEN 1 END) as completed_billing
        FROM bookings b
        LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
        WHERE b.therapist = ? AND b.date >= ? AND b.date <= ?
    """
    
    result = execute_query(query, (therapist_id, start_date, end_date), fetch='one')
    
    if result:
        stats = dict(result)
        # Calculate additional metrics
        if stats['total_appointments'] > 0:
            stats['avg_duration'] = stats['total_minutes'] / stats['total_appointments']
            stats['note_completion_rate'] = stats['completed_notes'] / stats['total_appointments']
            stats['billing_completion_rate'] = stats['completed_billing'] / stats['total_appointments']
        else:
            stats['avg_duration'] = 0
            stats['note_completion_rate'] = 0
            stats['billing_completion_rate'] = 0
            
        if stats['working_days'] > 0:
            stats['avg_appointments_per_day'] = stats['total_appointments'] / stats['working_days']
        else:
            stats['avg_appointments_per_day'] = 0
            
        return stats
    
    return {
        'total_appointments': 0,
        'total_minutes': 0,
        'working_days': 0,
        'completed_notes': 0,
        'completed_billing': 0,
        'avg_duration': 0,
        'note_completion_rate': 0,
        'billing_completion_rate': 0,
        'avg_appointments_per_day': 0
    }