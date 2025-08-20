"""
Treatment notes and clinical documentation for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel
from datetime import datetime
from .database import get_db_connection, execute_query
import sqlite3


class TreatmentNote(BaseModel):
    """Treatment Note model"""
    appointment_id: int
    appointment_date: str
    start_time: str
    duration: int
    patient_name: str
    patient_id: int
    profession: str
    therapist_name: str
    therapist_id: int
    subjective_findings: str
    objective_findings: str
    treatment: str
    plan: str
    note_to_patient: Optional[str] = ""
    consent_to_treatment: bool = False
    team_alert: Optional[str] = ""
    alert_comment: Optional[str] = ""
    alert_resolved: Optional[str] = ""


class SupplementaryNote(BaseModel):
    """Supplementary Note model"""
    appointment_id: int
    note: str
    author_id: int
    author_name: str


def submit_treatment_note(note: Dict[str, Any]) -> Dict[str, str]:
    """
    Submit a treatment note for an appointment
    
    Args:
        note: Dictionary containing treatment note data
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If required fields are missing or submission fails
    """
    required_fields = [
        "appointment_id", "appointment_date", "start_time", "duration", "patient_name",
        "patient_id", "profession", "therapist_name", "therapist_id",
        "subjective_findings", "objective_findings", "treatment", "plan", "note_to_patient"
    ]

    for field in required_fields:
        if field not in note:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        completed_at = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO treatment_notes (
                appointment_id, appointment_date, start_time, duration,
                patient_name, patient_id, profession, therapist_name, therapist_id,
                subjective_findings, objective_findings, treatment, plan, note_to_patient,
                consent_to_treatment, team_alert, alert_comment, alert_resolved, note_completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            note["appointment_id"], note["appointment_date"], note["start_time"], note["duration"],
            note["patient_name"], note["patient_id"], note["profession"], note["therapist_name"], note["therapist_id"],
            note["subjective_findings"], note["objective_findings"], note["treatment"], note["plan"], note["note_to_patient"], 
            note.get("consent_to_treatment", False), note.get("team_alert", ""),
            note.get("alert_comment", ""), note.get("alert_resolved", ""), completed_at,
        ))
        
        # Mark booking as having a completed note
        cursor.execute(
            "UPDATE bookings SET note_completed = 1 WHERE id = ?",
            (note["appointment_id"],)
        )
        
        conn.commit()
        return {"detail": "Treatment note submitted successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit treatment note: {str(e)}")
    finally:
        conn.close()


def get_full_treatment_note(appointment_id: str) -> Dict[str, Any]:
    """
    Get complete treatment note with billing information
    
    Args:
        appointment_id: The appointment ID
        
    Returns:
        Dictionary containing treatment note and billing data
    """
    conn = get_db_connection()
    try:
        # Treatment note
        treatment_row = conn.execute("""
            SELECT *
            FROM treatment_notes
            WHERE appointment_id = ?
        """, (appointment_id,)).fetchone()

        treatment = None
        if treatment_row:
            columns = [col[1] for col in conn.execute("PRAGMA table_info(treatment_notes)")]
            treatment = dict(zip(columns, treatment_row))

        # Billing entries (include billing_modifier)
        billing_rows = conn.execute("""
            SELECT be.code_id, be.final_fee, bc.code, bc.description, be.billing_modifier
            FROM billing_entries be
            LEFT JOIN billing_codes bc ON be.code_id = bc.id
            WHERE be.appointment_id = ?
        """, (appointment_id,)).fetchall()

        billing = []
        for row in billing_rows:
            billing.append({
                "code_id": row[0],
                "final_fee": row[1],
                "code": row[2],
                "description": row[3],
                "billing_modifier": row[4]
            })

        # Supplementary notes - match original schema
        supp_rows = conn.execute("""
            SELECT note, timestamp
            FROM supplementary_notes
            WHERE appointment_id = ?
            ORDER BY timestamp ASC
        """, (appointment_id,)).fetchall()

        supplementary = []
        for row in supp_rows:
            supplementary.append({
                "note": row[0],
                "timestamp": row[1]
            })

        return {
            "treatment": treatment,
            "billing": billing,
            "supplementary": supplementary
        }
        
    finally:
        conn.close()


def add_supplementary_note(appointment_id: str, data: Dict[str, Any], request: Request) -> Dict[str, str]:
    """
    Add a supplementary note to an appointment
    
    Args:
        appointment_id: The appointment ID
        data: Note data dictionary
        request: FastAPI request object for user session
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If user not authenticated or note creation fails
    """
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    note_text = data.get("note", "").strip()
    if not note_text:
        raise HTTPException(status_code=400, detail="Note text is required")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO supplementary_notes (appointment_id, user_id, note, timestamp)
            VALUES (?, ?, ?, ?)
        """, (appointment_id, user_id, note_text, timestamp))
        
        conn.commit()
        return {"detail": "Supplementary note added successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add supplementary note: {str(e)}")
    finally:
        conn.close()


def check_treatment_notes(ids: str) -> List[Dict[str, Any]]:
    """
    Check treatment notes status for multiple appointments
    
    Args:
        ids: Comma-separated string of appointment IDs
        
    Returns:
        List of appointment note status dictionaries
    """
    if not ids:
        return []

    try:
        appointment_ids = [int(id.strip()) for id in ids.split(',') if id.strip()]
        if not appointment_ids:
            return []

        placeholders = ','.join(['?' for _ in appointment_ids])
        query = f"""
            SELECT b.id, b.name, b.date, b.time,
                   CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END AS has_note
            FROM bookings b
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            WHERE b.id IN ({placeholders})
        """
        
        results = execute_query(query, tuple(appointment_ids), fetch='all')
        return [dict(row) for row in results] if results else []
        
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid appointment IDs format")


def check_treatment_note(appointment_id: str) -> Dict[str, Any]:
    """
    Check if a specific appointment has a treatment note
    
    Args:
        appointment_id: The appointment ID
        
    Returns:
        Dictionary with note status information
    """
    query = """
        SELECT b.id, b.name, b.date, b.time,
               CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END AS has_note,
               tn.note_completed_at
        FROM bookings b
        LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
        WHERE b.id = ?
    """
    
    result = execute_query(query, (appointment_id,), fetch='one')
    return dict(result) if result else {"has_note": False}


def get_latest_session_note(patient_id: int, profession: str) -> Optional[Dict[str, Any]]:
    """
    Get the latest session note for a patient and profession
    
    Args:
        patient_id: The patient ID
        profession: The profession type
        
    Returns:
        Latest session note dictionary or None
    """
    query = """
        SELECT tn.*, b.date, b.time
        FROM treatment_notes tn
        JOIN bookings b ON tn.appointment_id = b.id
        WHERE tn.patient_id = ? AND tn.profession = ?
        ORDER BY b.date DESC, b.time DESC
        LIMIT 1
    """
    
    result = execute_query(query, (patient_id, profession), fetch='one')
    return dict(result) if result else None


def get_unbilled_treatment_notes() -> List[Dict[str, Any]]:
    """
    Get treatment notes that don't have associated billing entries
    
    Returns:
        List of unbilled treatment note dictionaries
    """
    query = """
        SELECT tn.*, b.date, b.time, b.therapist, t.name as therapist_name,
               p.first_name, p.surname
        FROM treatment_notes tn
        JOIN bookings b ON tn.appointment_id = b.id
        LEFT JOIN therapists t ON b.therapist = t.id
        LEFT JOIN patients p ON tn.patient_id = p.id
        LEFT JOIN billing_entries be ON tn.appointment_id = be.appointment_id
        WHERE be.appointment_id IS NULL
        ORDER BY b.date DESC, b.time DESC
    """
    
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def get_patient_treatment_notes(patient_id: int, profession: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all treatment notes for a patient, optionally filtered by profession
    
    Args:
        patient_id: The patient ID
        profession: Optional profession filter
        
    Returns:
        List of treatment note dictionaries
    """
    base_query = """
        SELECT tn.*, b.date, b.time
        FROM treatment_notes tn
        JOIN bookings b ON tn.appointment_id = b.id
        WHERE tn.patient_id = ?
    """
    
    params = [patient_id]
    
    if profession:
        base_query += " AND tn.profession = ?"
        params.append(profession)
    
    base_query += " ORDER BY b.date DESC, b.time DESC"
    
    results = execute_query(base_query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


def get_therapist_treatment_notes(therapist_id: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """
    Get treatment notes for a specific therapist
    
    Args:
        therapist_id: The therapist ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of treatment note dictionaries
    """
    base_query = """
        SELECT tn.*, b.date, b.time, p.first_name, p.surname
        FROM treatment_notes tn
        JOIN bookings b ON tn.appointment_id = b.id
        LEFT JOIN patients p ON tn.patient_id = p.id
        WHERE tn.therapist_id = ?
    """
    
    params = [therapist_id]
    
    if start_date and end_date:
        base_query += " AND b.date >= ? AND b.date <= ?"
        params.extend([start_date, end_date])
    
    base_query += " ORDER BY b.date DESC, b.time DESC"
    
    results = execute_query(base_query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


def update_treatment_note(appointment_id: int, updates: Dict[str, Any]) -> bool:
    """
    Update an existing treatment note
    
    Args:
        appointment_id: The appointment ID
        updates: Dictionary of fields to update
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If update fails or note not found
    """
    if not updates:
        return True
    
    # Check if note exists
    existing = execute_query(
        "SELECT id FROM treatment_notes WHERE appointment_id = ?",
        (appointment_id,),
        fetch='one'
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Treatment note not found")
    
    # Build update query
    valid_fields = [
        'subjective_findings', 'objective_findings', 'treatment', 'plan',
        'note_to_patient', 'consent_to_treatment', 'team_alert',
        'alert_comment', 'alert_resolved'
    ]
    
    update_fields = [field for field in valid_fields if field in updates]
    if not update_fields:
        return True
    
    set_clause = ', '.join([f"{field} = ?" for field in update_fields])
    values = [updates[field] for field in update_fields] + [appointment_id]
    
    query = f"UPDATE treatment_notes SET {set_clause} WHERE appointment_id = ?"
    
    try:
        execute_query(query, tuple(values))
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update treatment note: {str(e)}")


def delete_treatment_note(appointment_id: int) -> bool:
    """
    Delete a treatment note
    
    Args:
        appointment_id: The appointment ID
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If deletion fails or note not found
    """
    # Check if note exists
    existing = execute_query(
        "SELECT id FROM treatment_notes WHERE appointment_id = ?",
        (appointment_id,),
        fetch='one'
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Treatment note not found")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Delete supplementary notes first
        cursor.execute("DELETE FROM supplementary_notes WHERE appointment_id = ?", (appointment_id,))
        
        # Delete treatment note
        cursor.execute("DELETE FROM treatment_notes WHERE appointment_id = ?", (appointment_id,))
        
        # Update booking
        cursor.execute("UPDATE bookings SET note_completed = 0 WHERE id = ?", (appointment_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete treatment note: {str(e)}")
    finally:
        conn.close()


def get_supplementary_notes(appointment_id: int) -> List[Dict[str, Any]]:
    """
    Get all supplementary notes for an appointment
    
    Args:
        appointment_id: The appointment ID
        
    Returns:
        List of supplementary note dictionaries
    """
    query = """
        SELECT note, timestamp, user_id
        FROM supplementary_notes
        WHERE appointment_id = ?
        ORDER BY timestamp DESC
    """
    
    results = execute_query(query, (appointment_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def search_treatment_notes(search_term: str, profession: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search treatment notes by content
    
    Args:
        search_term: The search term
        profession: Optional profession filter
        
    Returns:
        List of matching treatment note dictionaries
    """
    base_query = """
        SELECT tn.*, b.date, b.time, p.first_name, p.surname
        FROM treatment_notes tn
        JOIN bookings b ON tn.appointment_id = b.id
        LEFT JOIN patients p ON tn.patient_id = p.id
        WHERE (
            tn.subjective_findings LIKE ? OR
            tn.objective_findings LIKE ? OR
            tn.treatment LIKE ? OR
            tn.plan LIKE ? OR
            tn.note_to_patient LIKE ? OR
            tn.patient_name LIKE ?
        )
    """
    
    search_pattern = f"%{search_term}%"
    params = [search_pattern] * 6
    
    if profession:
        base_query += " AND tn.profession = ?"
        params.append(profession)
    
    base_query += " ORDER BY b.date DESC, b.time DESC"
    
    results = execute_query(base_query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []