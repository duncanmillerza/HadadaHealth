"""
Outcome measures management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Body
from pydantic import BaseModel
from datetime import datetime
from .database import get_db_connection, execute_query
import sqlite3


class OutcomeMeasureType(BaseModel):
    """Outcome Measure Type model"""
    name: str
    description: Optional[str] = None
    score_type: Optional[str] = None
    max_score: Optional[int] = None
    interpretation: Optional[str] = None
    category: Optional[str] = None
    has_subscores: bool = False


class OutcomeMeasureTypeSubscore(BaseModel):
    """Outcome Measure Type Subscore model"""
    outcome_measure_type_id: int
    name: str
    subcategory_name: Optional[str] = None
    max_score: Optional[int] = None


class OutcomeMeasure(BaseModel):
    """Outcome Measure model"""
    patient_id: str
    therapist: str
    appointment_id: Optional[str] = None
    date: str
    outcome_measure_type_id: int
    score: Optional[float] = None
    comments: Optional[str] = ""


class OutcomeMeasureSubscore(BaseModel):
    """Outcome Measure Subscore model"""
    outcome_measure_id: int
    subcategory_name: str
    score: Optional[float] = None
    max_score: Optional[int] = None
    comments: Optional[str] = ""


# ===== OUTCOME MEASURE TYPES MANAGEMENT =====

def get_all_outcome_measure_types() -> List[Dict[str, Any]]:
    """
    Get all outcome measure types
    
    Returns:
        List of outcome measure type dictionaries
    """
    query = """
        SELECT id, name, description, score_type, max_score, interpretation, category, has_subscores
        FROM outcome_measure_types
        ORDER BY name
    """
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def get_outcome_measure_types_from_subscores() -> List[Dict[str, Any]]:
    """
    Get outcome measure types that have subscores (for dropdown usage)
    
    Returns:
        List of outcome measure types with subscore information
    """
    query = """
        SELECT DISTINCT outcome_measure_type_id, subcategory_name
        FROM outcome_measure_type_subscores
        ORDER BY subcategory_name
    """
    results = execute_query(query, fetch='all')
    return [
        {
            "id": row["outcome_measure_type_id"],
            "name": row["subcategory_name"]
        }
        for row in results
    ] if results else []


def create_outcome_measure_type(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new outcome measure type
    
    Args:
        data: Dictionary containing outcome measure type information
        
    Returns:
        Success response with new ID
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO outcome_measure_types (name, description, score_type, max_score, 
                                             interpretation, category, has_subscores)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("name"),
            data.get("description"),
            data.get("score_type"),
            data.get("max_score"),
            data.get("interpretation"),
            data.get("category"),
            data.get("has_subscores", False)
        ))
        new_id = cursor.lastrowid
        conn.commit()
        return {"status": "success", "id": new_id}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Outcome measure type already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create outcome measure type: {str(e)}")
    finally:
        conn.close()


def update_outcome_measure_type(type_id: int, data: Dict[str, Any]) -> Dict[str, str]:
    """
    Update an existing outcome measure type
    
    Args:
        type_id: The outcome measure type ID to update
        data: Dictionary containing updated information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If update fails or type not found
    """
    # Check if type exists
    existing = get_outcome_measure_type_by_id(type_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Outcome measure type not found")
    
    valid_fields = [
        'name', 'description', 'score_type', 'max_score', 
        'interpretation', 'category', 'has_subscores'
    ]
    
    update_fields = [field for field in valid_fields if field in data]
    if not update_fields:
        return {"detail": "No fields to update"}
    
    conn = get_db_connection()
    try:
        set_clause = ', '.join([f"{field} = ?" for field in update_fields])
        values = [data[field] for field in update_fields] + [type_id]
        
        query = f"UPDATE outcome_measure_types SET {set_clause} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return {"detail": "Outcome measure type updated successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update outcome measure type: {str(e)}")
    finally:
        conn.close()


def delete_outcome_measure_type(type_id: int) -> Dict[str, str]:
    """
    Delete an outcome measure type
    
    Args:
        type_id: The outcome measure type ID to delete
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If deletion fails or type not found
    """
    # Check if type exists
    existing = get_outcome_measure_type_by_id(type_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Outcome measure type not found")
    
    conn = get_db_connection()
    try:
        # Check if type is being used
        measures_check = conn.execute(
            "SELECT COUNT(*) FROM outcome_measures WHERE outcome_measure_type_id = ?", 
            (type_id,)
        ).fetchone()
        
        if measures_check and measures_check[0] > 0:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete outcome measure type with associated measures"
            )
        
        cursor = conn.cursor()
        # Delete associated subscores first
        cursor.execute("DELETE FROM outcome_measure_type_subscores WHERE outcome_measure_type_id = ?", (type_id,))
        # Delete the type
        cursor.execute("DELETE FROM outcome_measure_types WHERE id = ?", (type_id,))
        conn.commit()
        
        return {"detail": "Outcome measure type deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete outcome measure type: {str(e)}")
    finally:
        conn.close()


def get_outcome_measure_type_by_id(type_id: int) -> Optional[Dict[str, Any]]:
    """
    Get an outcome measure type by ID
    
    Args:
        type_id: The outcome measure type ID
        
    Returns:
        Outcome measure type dictionary or None if not found
    """
    query = """
        SELECT id, name, description, score_type, max_score, interpretation, category, has_subscores
        FROM outcome_measure_types WHERE id = ?
    """
    result = execute_query(query, (type_id,), fetch='one')
    return dict(result) if result else None


def get_outcome_measure_categories() -> List[str]:
    """
    Get unique outcome measure categories
    
    Returns:
        List of category names
    """
    query = """
        SELECT DISTINCT category 
        FROM outcome_measure_types 
        WHERE category IS NOT NULL AND TRIM(category) != ''
        ORDER BY category
    """
    results = execute_query(query, fetch='all')
    return [row[0] for row in results] if results else []


def get_outcome_measures_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get outcome measures filtered by category
    
    Args:
        category: The category to filter by
        
    Returns:
        List of outcome measure dictionaries
    """
    query = """
        SELECT id, name, description, max_score
        FROM outcome_measure_types 
        WHERE category = ?
        ORDER BY name
    """
    results = execute_query(query, (category,), fetch='all')
    return [dict(row) for row in results] if results else []


# ===== OUTCOME MEASURE TYPE SUBSCORES MANAGEMENT =====

def create_outcome_measure_type_subscore(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new outcome measure type subscore
    
    Args:
        data: Dictionary containing subscore information
        
    Returns:
        Success response with new ID
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO outcome_measure_type_subscores (outcome_measure_type_id, name, subcategory_name, max_score)
            VALUES (?, ?, ?, ?)
        """, (
            data.get("outcome_measure_type_id"),
            data.get("name"),
            data.get("subcategory_name"),
            data.get("max_score")
        ))
        new_id = cursor.lastrowid
        conn.commit()
        return {"status": "success", "id": new_id}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create outcome measure type subscore: {str(e)}")
    finally:
        conn.close()


def get_outcome_measure_type_subscores(type_id: int) -> List[Dict[str, Any]]:
    """
    Get subscores for an outcome measure type
    
    Args:
        type_id: The outcome measure type ID
        
    Returns:
        List of subscore dictionaries
    """
    query = """
        SELECT id, subcategory_name, max_score, name
        FROM outcome_measure_type_subscores
        WHERE outcome_measure_type_id = ?
        ORDER BY subcategory_name
    """
    results = execute_query(query, (type_id,), fetch='all')
    return [dict(row) for row in results] if results else []


# ===== OUTCOME MEASURES MANAGEMENT =====

def create_outcome_measure(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new outcome measure
    
    Args:
        data: Dictionary containing outcome measure information
        
    Returns:
        Success response with new ID
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO outcome_measures
              (patient_id, therapist, appointment_id, date, outcome_measure, score, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("patient_id"),
            data.get("therapist", ""),
            data.get("appointment_id"),
            data.get("date"),
            data.get("outcome_measure_type_id") or data.get("outcome_measure", ""),
            data.get("score"),
            data.get("comments", "")
        ))
        new_id = cursor.lastrowid
        conn.commit()
        return {"id": new_id}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create outcome measure: {str(e)}")
    finally:
        conn.close()


def get_outcome_measures_by_patient(patient_id: str) -> List[Dict[str, Any]]:
    """
    Get outcome measures for a specific patient
    
    Args:
        patient_id: The patient ID
        
    Returns:
        List of outcome measure dictionaries
    """
    query = """
        SELECT om.*, omt.name as type_name, omt.description as type_description
        FROM outcome_measures om
        JOIN outcome_measure_types omt ON om.outcome_measure_type_id = omt.id
        WHERE om.patient_id = ?
        ORDER BY om.date DESC
    """
    results = execute_query(query, (patient_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_outcome_measure_by_id(measure_id: int) -> Optional[Dict[str, Any]]:
    """
    Get an outcome measure by ID
    
    Args:
        measure_id: The outcome measure ID
        
    Returns:
        Outcome measure dictionary or None if not found
    """
    query = """
        SELECT * FROM outcome_measures WHERE id = ?
    """
    result = execute_query(query, (measure_id,), fetch='one')
    return dict(result) if result else None


def update_outcome_measure(measure_id: int, data: Dict[str, Any]) -> Dict[str, str]:
    """
    Update an existing outcome measure
    
    Args:
        measure_id: The outcome measure ID to update
        data: Dictionary containing updated information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If update fails or measure not found
    """
    # Check if measure exists
    existing = get_outcome_measure_by_id(measure_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Outcome measure not found")
    
    valid_fields = ['patient_id', 'therapist', 'appointment_id', 'date', 'outcome_measure_type_id', 'score', 'comments']
    update_fields = [field for field in valid_fields if field in data]
    
    if not update_fields:
        return {"detail": "No fields to update"}
    
    conn = get_db_connection()
    try:
        set_clause = ', '.join([f"{field} = ?" for field in update_fields])
        values = [data[field] for field in update_fields] + [measure_id]
        
        query = f"UPDATE outcome_measures SET {set_clause} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return {"detail": "Outcome measure updated successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update outcome measure: {str(e)}")
    finally:
        conn.close()


def delete_outcome_measure(measure_id: int) -> Dict[str, str]:
    """
    Delete an outcome measure
    
    Args:
        measure_id: The outcome measure ID to delete
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If deletion fails or measure not found
    """
    # Check if measure exists
    existing = get_outcome_measure_by_id(measure_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Outcome measure not found")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Delete associated subscores first
        cursor.execute("DELETE FROM outcome_measure_subscores WHERE outcome_measure_id = ?", (measure_id,))
        # Delete the measure
        cursor.execute("DELETE FROM outcome_measures WHERE id = ?", (measure_id,))
        conn.commit()
        
        return {"detail": "Outcome measure deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete outcome measure: {str(e)}")
    finally:
        conn.close()


# ===== OUTCOME MEASURE SUBSCORES MANAGEMENT =====

def add_outcome_measure_subscores(measure_id: int, subscores: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Add subscores to an outcome measure
    
    Args:
        measure_id: The outcome measure ID
        subscores: List of subscore dictionaries
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If creation fails
    """
    if not isinstance(subscores, list):
        raise HTTPException(status_code=400, detail="Subscores must be a list")
    
    # Check if measure exists
    existing = get_outcome_measure_by_id(measure_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Outcome measure not found")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for subscore in subscores:
            cursor.execute("""
                INSERT INTO outcome_measure_subscores
                  (outcome_measure_id, subcategory_name, score, max_score, comments)
                VALUES (?, ?, ?, ?, ?)
            """, (
                measure_id,
                subscore.get("subcategory_name"),
                subscore.get("score"),
                subscore.get("max_score"),
                subscore.get("comments", "")
            ))
        conn.commit()
        return {"detail": "Subscores added successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add subscores: {str(e)}")
    finally:
        conn.close()


def get_outcome_measure_subscores(measure_id: int) -> List[Dict[str, Any]]:
    """
    Get subscores for an outcome measure
    
    Args:
        measure_id: The outcome measure ID
        
    Returns:
        List of subscore dictionaries
    """
    query = """
        SELECT id, outcome_measure_id, subcategory_name, score, max_score, comments
        FROM outcome_measure_subscores
        WHERE outcome_measure_id = ?
        ORDER BY subcategory_name
    """
    results = execute_query(query, (measure_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def search_outcome_measures(search_term: str) -> List[Dict[str, Any]]:
    """
    Search outcome measures by patient, therapist, or type
    
    Args:
        search_term: The search term
        
    Returns:
        List of matching outcome measure dictionaries
    """
    search_pattern = f"%{search_term}%"
    query = """
        SELECT om.*, omt.name as type_name, omt.description as type_description
        FROM outcome_measures om
        JOIN outcome_measure_types omt ON om.outcome_measure_type_id = omt.id
        WHERE 
            om.patient_id LIKE ? OR 
            om.therapist LIKE ? OR
            omt.name LIKE ? OR
            om.comments LIKE ?
        ORDER BY om.date DESC
    """
    
    params = [search_pattern] * 4
    results = execute_query(query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


def get_outcome_measures_statistics() -> Dict[str, Any]:
    """
    Get statistics about outcome measures
    
    Returns:
        Statistics dictionary
    """
    conn = get_db_connection()
    try:
        stats = {}
        
        # Total outcome measures
        total_result = conn.execute("SELECT COUNT(*) FROM outcome_measures").fetchone()
        stats['total_outcome_measures'] = total_result[0] if total_result else 0
        
        # Total outcome measure types
        types_result = conn.execute("SELECT COUNT(*) FROM outcome_measure_types").fetchone()
        stats['total_outcome_measure_types'] = types_result[0] if types_result else 0
        
        # Measures by type
        type_stats = conn.execute("""
            SELECT omt.name, COUNT(om.id) as count
            FROM outcome_measure_types omt
            LEFT JOIN outcome_measures om ON omt.id = om.outcome_measure_type_id
            GROUP BY omt.id, omt.name
            ORDER BY count DESC
        """).fetchall()
        
        stats['measures_by_type'] = {}
        for type_name, count in type_stats:
            stats['measures_by_type'][type_name] = count
        
        # Measures by category
        category_stats = conn.execute("""
            SELECT omt.category, COUNT(om.id) as count
            FROM outcome_measure_types omt
            LEFT JOIN outcome_measures om ON omt.id = om.outcome_measure_type_id
            WHERE omt.category IS NOT NULL AND omt.category != ''
            GROUP BY omt.category
            ORDER BY count DESC
        """).fetchall()
        
        stats['measures_by_category'] = {}
        for category, count in category_stats:
            stats['measures_by_category'][category] = count
        
        # Recent measures (last 30 days)
        recent_result = conn.execute("""
            SELECT COUNT(*) FROM outcome_measures 
            WHERE date >= date('now', '-30 days')
        """).fetchone()
        stats['recent_measures_30d'] = recent_result[0] if recent_result else 0
        
        return stats
        
    finally:
        conn.close()