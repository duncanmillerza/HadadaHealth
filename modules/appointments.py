"""
Appointment and booking management for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel
from datetime import datetime, date
from .database import get_db_connection, execute_query
import sqlite3


class Booking(BaseModel):
    """Booking/Appointment model"""
    id: str
    name: str
    therapist: int
    date: str
    day: str
    time: str
    duration: int
    notes: Optional[str] = ""
    colour: Optional[str] = None
    profession: Optional[str] = None
    patient_id: Optional[int] = None
    has_note: bool = False
    billing_completed: bool = False
    appointment_type_id: Optional[int] = None  # New field for appointment type
    billing_code: Optional[str] = None  # Billing code field


def get_bookings(request: Request, therapist_id: Optional[int] = None, 
                start: str = None, end: str = None) -> List[Dict[str, Any]]:
    """
    Get bookings with optional filtering by therapist, date range
    
    Args:
        request: FastAPI request object for session data
        therapist_id: Optional therapist ID to filter by
        start: Start date filter (YYYY-MM-DD)
        end: End date filter (YYYY-MM-DD)
        
    Returns:
        List of booking dictionaries
        
    Raises:
        HTTPException: If not authenticated or no therapist ID available
    """
    user_id = request.session.get('user_id')
    session_therapist_id = request.session.get('linked_therapist_id')
    role = request.session.get('role')

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    target_id = therapist_id if role == "Admin" and therapist_id else session_therapist_id

    if not target_id:
        raise HTTPException(status_code=400, detail="No therapist ID available")

    base_sql = """
    SELECT
      b.id,
      b.name,
      b.therapist,
      b.date,
      b.day,
      b.time,
      b.duration,
      b.colour,
      b.profession,
      b.patient_id,
      b.appointment_type_id,
      CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END AS has_note,
      CASE WHEN be.appointment_id IS NOT NULL THEN 1 ELSE 0 END AS has_billing,
      b.billing_completed,
      p.first_name as patient_first_name,
      p.surname as patient_surname,
      at.name as appointment_type_name
    FROM bookings b
    LEFT JOIN treatment_notes tn
      ON b.id = tn.appointment_id
    LEFT JOIN billing_entries be
      ON b.id = be.appointment_id
    LEFT JOIN patients p
      ON b.patient_id = p.id
    LEFT JOIN appointment_types at
      ON b.appointment_type_id = at.id
    WHERE b.therapist = ?
    """
    params = [target_id]
    
    if start and end:
        base_sql += " AND date >= ? AND date < ?"
        params += [start, end]
    
    conn = get_db_connection()
    try:
        cursor = conn.execute(base_sql, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        bookings = []
        
        for row in rows:
            d = dict(zip(columns, row))
            # Map has_billing (int) to hasBilling (bool) for JS
            d['hasBilling'] = bool(d.pop('has_billing', 0))
            # Map billing_completed (may be None or 0/1) to bool for JS
            d['billing_completed'] = bool(d.get('billing_completed', 0))
            bookings.append(d)
            
        return bookings
    finally:
        conn.close()


def get_booking_by_id(booking_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single booking by ID
    
    Args:
        booking_id: The booking ID
        
    Returns:
        Booking dictionary or None if not found
    """
    query = """
        SELECT b.*, t.name as therapist_name, t.profession,
               p.first_name, p.surname
        FROM bookings b
        LEFT JOIN therapists t ON b.therapist = t.id
        LEFT JOIN patients p ON b.patient_id = p.id
        WHERE b.id = ?
    """
    result = execute_query(query, (booking_id,), fetch='one')
    return dict(result) if result else None


def create_booking(booking: Booking) -> int:
    """
    Create a new booking
    
    Args:
        booking: Booking object with appointment details
        
    Returns:
        The ID of the created booking
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        # Convert string IDs to integers for database
        therapist_id = int(booking.therapist) if booking.therapist else None
        patient_id = int(booking.patient_id) if booking.patient_id else None
        
        cursor = conn.cursor()
        query = """
            INSERT INTO bookings (
                name, therapist, date, day, time, duration, 
                notes, colour, profession, patient_id, billing_completed, appointment_type_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            booking.name,
            therapist_id,
            booking.date,
            booking.day,
            booking.time,
            booking.duration,
            booking.notes or "",
            booking.colour,
            booking.profession,
            patient_id,
            booking.billing_completed,
            booking.appointment_type_id
        ))
        
        booking_id = cursor.lastrowid
        conn.commit()
        return booking_id
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")
    finally:
        conn.close()


def update_booking(booking_id: int, booking: Booking) -> bool:
    """
    Update an existing booking
    
    Args:
        booking_id: The booking ID to update
        booking: Updated booking data
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If update fails or booking not found
    """
    conn = get_db_connection()
    try:
        # Check if booking exists
        existing = get_booking_by_id(booking_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Convert string IDs to integers for database
        therapist_id = int(booking.therapist) if booking.therapist else None
        patient_id = int(booking.patient_id) if booking.patient_id else None
        
        cursor = conn.cursor()
        query = """
            UPDATE bookings SET
                name = ?, therapist = ?, date = ?, day = ?, time = ?,
                duration = ?, notes = ?, colour = ?, profession = ?,
                patient_id = ?, billing_completed = ?, appointment_type_id = ?
            WHERE id = ?
        """
        
        cursor.execute(query, (
            booking.name,
            therapist_id,
            booking.date,
            booking.day,
            booking.time,
            booking.duration,
            booking.notes or "",
            booking.colour,
            booking.profession,
            patient_id,
            booking.billing_completed,
            booking.appointment_type_id,
            booking_id
        ))
        
        conn.commit()
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update booking: {str(e)}")
    finally:
        conn.close()


def delete_booking(booking_id: int) -> bool:
    """
    Delete a booking
    
    Args:
        booking_id: The booking ID to delete
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If deletion fails or booking not found
    """
    conn = get_db_connection()
    try:
        # Check if booking exists
        existing = get_booking_by_id(booking_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete booking: {str(e)}")
    finally:
        conn.close()


def get_bookings_for_day_for_therapists(date_param: str) -> List[Dict[str, Any]]:
    """
    Get all bookings for a specific date across all therapists
    
    Args:
        date_param: Date in YYYY-MM-DD format
        
    Returns:
        List of booking dictionaries with therapist information
    """
    query = """
        SELECT b.*, t.name as therapist_name, t.profession,
               p.first_name, p.surname
        FROM bookings b
        LEFT JOIN therapists t ON b.therapist = t.id
        LEFT JOIN patients p ON b.patient_id = p.id
        WHERE b.date = ?
        ORDER BY b.time, t.name
    """
    
    results = execute_query(query, (date_param,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_therapist_calendar(therapist_id: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """
    Get calendar view for a specific therapist
    
    Args:
        therapist_id: The therapist ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of appointment dictionaries
    """
    base_query = """
        SELECT b.*, p.first_name, p.surname,
               CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END AS has_note
        FROM bookings b
        LEFT JOIN patients p ON b.patient_id = p.id
        LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
        WHERE b.therapist = ?
    """
    
    params = [therapist_id]
    
    if start_date and end_date:
        base_query += " AND b.date >= ? AND b.date <= ?"
        params.extend([start_date, end_date])
    
    base_query += " ORDER BY b.date, b.time"
    
    results = execute_query(base_query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []


def get_mdt_calendar(date_param: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get Multi-Disciplinary Team (MDT) calendar for a specific date
    
    Args:
        date_param: Date in YYYY-MM-DD format
        
    Returns:
        Dictionary with therapist names as keys and their appointments as values
    """
    query = """
        SELECT b.*, t.name as therapist_name, t.profession,
               p.first_name, p.surname
        FROM bookings b
        LEFT JOIN therapists t ON b.therapist = t.id
        LEFT JOIN patients p ON b.patient_id = p.id
        WHERE b.date = ?
        ORDER BY t.name, b.time
    """
    
    results = execute_query(query, (date_param,), fetch='all')
    
    # Group by therapist
    mdt_calendar = {}
    for row in results:
        booking = dict(row)
        therapist_name = booking['therapist_name'] or f"Unknown ({booking['therapist']})"
        
        if therapist_name not in mdt_calendar:
            mdt_calendar[therapist_name] = []
            
        mdt_calendar[therapist_name].append(booking)
    
    return mdt_calendar


def check_treatment_notes(appointment_ids: str) -> List[Dict[str, Any]]:
    """
    Check treatment notes status for multiple appointments
    
    Args:
        appointment_ids: Comma-separated string of appointment IDs
        
    Returns:
        List of dictionaries with note status for each appointment
    """
    if not appointment_ids:
        return []
    
    try:
        ids = [int(id.strip()) for id in appointment_ids.split(',') if id.strip()]
        if not ids:
            return []
        
        placeholders = ','.join(['?' for _ in ids])
        query = f"""
            SELECT b.id, b.name, b.date, b.time,
                   CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END AS has_note
            FROM bookings b
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            WHERE b.id IN ({placeholders})
        """
        
        results = execute_query(query, tuple(ids), fetch='all')
        return [dict(row) for row in results] if results else []
        
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid appointment IDs format")


def get_booking_with_treatment_note(appointment_id: int) -> Optional[Dict[str, Any]]:
    """
    Get booking details with treatment note information
    
    Args:
        appointment_id: The appointment ID
        
    Returns:
        Booking dictionary with treatment note data or None
    """
    query = """
        SELECT b.*, tn.subjective_findings, tn.objective_findings,
               tn.treatment, tn.plan, tn.notes, tn.timestamp as note_timestamp,
               p.first_name, p.surname, t.name as therapist_name
        FROM bookings b
        LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
        LEFT JOIN patients p ON b.patient_id = p.id
        LEFT JOIN therapists t ON b.therapist = t.id
        WHERE b.id = ?
    """
    
    result = execute_query(query, (appointment_id,), fetch='one')
    return dict(result) if result else None


def get_upcoming_appointments(therapist_id: int, days_ahead: int = 7) -> List[Dict[str, Any]]:
    """
    Get upcoming appointments for a therapist
    
    Args:
        therapist_id: The therapist ID
        days_ahead: Number of days ahead to look (default 7)
        
    Returns:
        List of upcoming appointment dictionaries
    """
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)
    
    query = """
        SELECT b.*, p.first_name, p.surname
        FROM bookings b
        LEFT JOIN patients p ON b.patient_id = p.id
        WHERE b.therapist = ? AND b.date >= ? AND b.date <= ?
        ORDER BY b.date, b.time
    """
    
    results = execute_query(query, (therapist_id, str(today), str(end_date)), fetch='all')
    return [dict(row) for row in results] if results else []


def search_bookings(search_term: str, therapist_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Search bookings by patient name or appointment details
    
    Args:
        search_term: The search term
        therapist_id: Optional therapist ID to filter by
        
    Returns:
        List of matching booking dictionaries
    """
    base_query = """
        SELECT b.*, p.first_name, p.surname, t.name as therapist_name
        FROM bookings b
        LEFT JOIN patients p ON b.patient_id = p.id
        LEFT JOIN therapists t ON b.therapist = t.id
        WHERE (
            b.name LIKE ? OR 
            p.first_name LIKE ? OR 
            p.surname LIKE ? OR
            b.notes LIKE ?
        )
    """
    
    search_pattern = f"%{search_term}%"
    params = [search_pattern, search_pattern, search_pattern, search_pattern]
    
    if therapist_id:
        base_query += " AND b.therapist = ?"
        params.append(therapist_id)
    
    base_query += " ORDER BY b.date DESC, b.time DESC"
    
    results = execute_query(base_query, tuple(params), fetch='all')
    return [dict(row) for row in results] if results else []