"""
Profession and clinic management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Body
from pydantic import BaseModel
from .database import get_db_connection, execute_query
import sqlite3


class Profession(BaseModel):
    """Profession model"""
    profession_name: str
    practice_name: Optional[str] = None
    practice_owner: Optional[str] = None
    practice_number: Optional[str] = None
    practice_email: Optional[str] = None
    clinics: Optional[str] = None


class Clinic(BaseModel):
    """Clinic model"""
    clinic_name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


# ===== PROFESSION MANAGEMENT FUNCTIONS =====

def get_all_professions() -> List[Dict[str, Any]]:
    """
    Get all professions
    
    Returns:
        List of profession dictionaries
    """
    query = """
        SELECT id, profession_name, practice_name, practice_owner, 
               practice_number, practice_email, clinics
        FROM professions
        ORDER BY profession_name
    """
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def create_profession(profession_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create a new profession
    
    Args:
        profession_data: Dictionary containing profession information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO professions (profession_name, practice_name, practice_owner, 
                                   practice_number, practice_email, clinics)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            profession_data.get('profession_name'),
            profession_data.get('practice_name'),
            profession_data.get('practice_owner'),
            profession_data.get('practice_number'),
            profession_data.get('practice_email'),
            profession_data.get('clinics')
        ))
        conn.commit()
        return {"detail": "Profession added successfully"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Profession already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create profession: {str(e)}")
    finally:
        conn.close()


def update_profession(profession_id: int, profession_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Update an existing profession
    
    Args:
        profession_id: The profession ID to update
        profession_data: Dictionary containing updated profession information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If profession not found or update fails
    """
    # Check if profession exists
    existing = get_profession_by_id(profession_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Profession not found")
    
    # Build update query
    valid_fields = [
        'profession_name', 'practice_name', 'practice_owner',
        'practice_number', 'practice_email', 'clinics'
    ]
    
    update_fields = [field for field in valid_fields if field in profession_data]
    if not update_fields:
        return {"detail": "No fields to update"}
    
    conn = get_db_connection()
    try:
        set_clause = ', '.join([f"{field} = ?" for field in update_fields])
        values = [profession_data[field] for field in update_fields] + [profession_id]
        
        query = f"UPDATE professions SET {set_clause} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return {"detail": "Profession updated successfully"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Profession name already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profession: {str(e)}")
    finally:
        conn.close()


def delete_profession(profession_id: int) -> Dict[str, str]:
    """
    Delete a profession
    
    Args:
        profession_id: The profession ID to delete
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If profession not found or deletion fails
    """
    # Check if profession exists
    existing = get_profession_by_id(profession_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Profession not found")
    
    conn = get_db_connection()
    try:
        # Check if profession is being used by therapists
        therapists_check = conn.execute(
            "SELECT COUNT(*) FROM therapists WHERE profession = ?", 
            (existing['profession_name'],)
        ).fetchone()
        
        if therapists_check and therapists_check[0] > 0:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete profession with associated therapists"
            )
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM professions WHERE id = ?", (profession_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Profession not found")
            
        return {"detail": "Profession deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete profession: {str(e)}")
    finally:
        conn.close()


def get_profession_by_id(profession_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a profession by ID
    
    Args:
        profession_id: The profession ID
        
    Returns:
        Profession dictionary or None if not found
    """
    query = """
        SELECT id, profession_name, practice_name, practice_owner, 
               practice_number, practice_email, clinics
        FROM professions WHERE id = ?
    """
    result = execute_query(query, (profession_id,), fetch='one')
    return dict(result) if result else None


def get_profession_by_name(profession_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a profession by name
    
    Args:
        profession_name: The profession name
        
    Returns:
        Profession dictionary or None if not found
    """
    query = """
        SELECT id, profession_name, practice_name, practice_owner, 
               practice_number, practice_email, clinics
        FROM professions WHERE profession_name = ?
    """
    result = execute_query(query, (profession_name,), fetch='one')
    return dict(result) if result else None


def search_professions(search_term: str) -> List[Dict[str, Any]]:
    """
    Search professions by name or practice details
    
    Args:
        search_term: The search term
        
    Returns:
        List of matching profession dictionaries
    """
    search_pattern = f"%{search_term}%"
    query = """
        SELECT id, profession_name, practice_name, practice_owner, 
               practice_number, practice_email, clinics
        FROM professions
        WHERE 
            profession_name LIKE ? OR 
            practice_name LIKE ? OR
            practice_owner LIKE ?
        ORDER BY profession_name
    """
    
    params = [search_pattern] * 3
    results = execute_query(query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


# ===== CLINIC MANAGEMENT FUNCTIONS =====

def get_all_clinics() -> List[Dict[str, Any]]:
    """
    Get all clinics
    
    Returns:
        List of clinic dictionaries
    """
    query = """
        SELECT id, clinic_name, address, email, phone
        FROM clinics
        ORDER BY clinic_name
    """
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def create_clinic(clinic_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create a new clinic
    
    Args:
        clinic_data: Dictionary containing clinic information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clinics (clinic_name, address, email, phone)
            VALUES (?, ?, ?, ?)
        """, (
            clinic_data.get('clinic_name'),
            clinic_data.get('address'),
            clinic_data.get('email'),
            clinic_data.get('phone')
        ))
        conn.commit()
        return {"detail": "Clinic added successfully"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Clinic already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create clinic: {str(e)}")
    finally:
        conn.close()


def update_clinic(clinic_id: int, clinic_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Update an existing clinic
    
    Args:
        clinic_id: The clinic ID to update
        clinic_data: Dictionary containing updated clinic information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If clinic not found or update fails
    """
    # Check if clinic exists
    existing = get_clinic_by_id(clinic_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    # Build update query
    valid_fields = ['clinic_name', 'address', 'email', 'phone']
    update_fields = [field for field in valid_fields if field in clinic_data]
    
    if not update_fields:
        return {"detail": "No fields to update"}
    
    conn = get_db_connection()
    try:
        set_clause = ', '.join([f"{field} = ?" for field in update_fields])
        values = [clinic_data[field] for field in update_fields] + [clinic_id]
        
        query = f"UPDATE clinics SET {set_clause} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return {"detail": "Clinic updated successfully"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Clinic name already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update clinic: {str(e)}")
    finally:
        conn.close()


def delete_clinic(clinic_id: int) -> Dict[str, str]:
    """
    Delete a clinic
    
    Args:
        clinic_id: The clinic ID to delete
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If clinic not found or deletion fails
    """
    # Check if clinic exists
    existing = get_clinic_by_id(clinic_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    conn = get_db_connection()
    try:
        # Check if clinic is being used by therapists
        therapists_check = conn.execute(
            "SELECT COUNT(*) FROM therapists WHERE clinic = ?", 
            (existing['clinic_name'],)
        ).fetchone()
        
        if therapists_check and therapists_check[0] > 0:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete clinic with associated therapists"
            )
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clinics WHERE id = ?", (clinic_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Clinic not found")
            
        return {"detail": "Clinic deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete clinic: {str(e)}")
    finally:
        conn.close()


def get_clinic_by_id(clinic_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a clinic by ID
    
    Args:
        clinic_id: The clinic ID
        
    Returns:
        Clinic dictionary or None if not found
    """
    query = """
        SELECT id, clinic_name, address, email, phone
        FROM clinics WHERE id = ?
    """
    result = execute_query(query, (clinic_id,), fetch='one')
    return dict(result) if result else None


def get_clinic_by_name(clinic_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a clinic by name
    
    Args:
        clinic_name: The clinic name
        
    Returns:
        Clinic dictionary or None if not found
    """
    query = """
        SELECT id, clinic_name, address, email, phone
        FROM clinics WHERE clinic_name = ?
    """
    result = execute_query(query, (clinic_name,), fetch='one')
    return dict(result) if result else None


def search_clinics(search_term: str) -> List[Dict[str, Any]]:
    """
    Search clinics by name, address, or email
    
    Args:
        search_term: The search term
        
    Returns:
        List of matching clinic dictionaries
    """
    search_pattern = f"%{search_term}%"
    query = """
        SELECT id, clinic_name, address, email, phone
        FROM clinics
        WHERE 
            clinic_name LIKE ? OR 
            address LIKE ? OR
            email LIKE ?
        ORDER BY clinic_name
    """
    
    params = [search_pattern] * 3
    results = execute_query(query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


def get_profession_clinic_statistics() -> Dict[str, Any]:
    """
    Get statistics about professions and clinics
    
    Returns:
        Statistics dictionary
    """
    conn = get_db_connection()
    try:
        stats = {}
        
        # Total professions
        prof_result = conn.execute("SELECT COUNT(*) FROM professions").fetchone()
        stats['total_professions'] = prof_result[0] if prof_result else 0
        
        # Total clinics
        clinic_result = conn.execute("SELECT COUNT(*) FROM clinics").fetchone()
        stats['total_clinics'] = clinic_result[0] if clinic_result else 0
        
        # Professions with practice details
        practice_result = conn.execute(
            "SELECT COUNT(*) FROM professions WHERE practice_name IS NOT NULL AND practice_name != ''"
        ).fetchone()
        stats['professions_with_practice_details'] = practice_result[0] if practice_result else 0
        
        # Clinics with contact info
        contact_result = conn.execute(
            "SELECT COUNT(*) FROM clinics WHERE email IS NOT NULL AND email != ''"
        ).fetchone()
        stats['clinics_with_contact_info'] = contact_result[0] if contact_result else 0
        
        # Therapists by profession
        prof_therapists = conn.execute("""
            SELECT profession, COUNT(*) 
            FROM therapists 
            GROUP BY profession
            ORDER BY COUNT(*) DESC
        """).fetchall()
        
        stats['therapists_by_profession'] = {}
        for profession, count in prof_therapists:
            stats['therapists_by_profession'][profession] = count
        
        # Therapists by clinic
        clinic_therapists = conn.execute("""
            SELECT clinic, COUNT(*) 
            FROM therapists 
            GROUP BY clinic
            ORDER BY COUNT(*) DESC
        """).fetchall()
        
        stats['therapists_by_clinic'] = {}
        for clinic, count in clinic_therapists:
            stats['therapists_by_clinic'][clinic] = count
        
        return stats
        
    finally:
        conn.close()


def get_unique_profession_names() -> List[str]:
    """
    Get list of unique profession names
    
    Returns:
        List of profession names
    """
    query = "SELECT DISTINCT profession_name FROM professions WHERE profession_name IS NOT NULL ORDER BY profession_name"
    results = execute_query(query, fetch='all')
    return [row[0] for row in results] if results else []


def get_unique_clinic_names() -> List[str]:
    """
    Get list of unique clinic names
    
    Returns:
        List of clinic names
    """
    query = "SELECT DISTINCT clinic_name FROM clinics WHERE clinic_name IS NOT NULL ORDER BY clinic_name"
    results = execute_query(query, fetch='all')
    return [row[0] for row in results] if results else []