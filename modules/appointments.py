"""
Appointments and booking management module for HadadaHealth
"""
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, date

from .database import get_db_connection


class Booking(BaseModel):
    id: str
    name: str
    therapist: str  # Changed to str to match frontend
    date: str
    day: str
    time: str
    duration: int
    notes: Optional[str] = ""
    colour: Optional[str] = None
    profession: Optional[str] = None
    patient_id: Optional[str] = None  # Changed to str to match frontend
    has_note: bool = False
    billing_completed: bool = False


def get_bookings(therapist_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get all bookings, optionally filtered by therapist and date range"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build query conditions
        conditions = []
        params = []
        
        if therapist_id:
            conditions.append("b.therapist = ?")
            params.append(therapist_id)
        
        if start_date:
            conditions.append("b.date >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("b.date < ?")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        query = f"""
            SELECT b.*, 
                   CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END as has_note,
                   t.profession, t.name as therapist_name
            FROM bookings b
            JOIN therapists t ON b.therapist = t.id
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            {where_clause}
            ORDER BY b.date, b.time
        """
        
        bookings = cursor.execute(query, params).fetchall()
        columns = [description[0] for description in cursor.description]
        
        return [
            dict(zip(columns, booking))
            for booking in bookings
        ]


def get_booking_by_id(booking_id: str):
    """Get a specific booking by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        booking = cursor.execute("""
            SELECT b.*, t.name as therapist_name, t.profession,
                   CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END as has_note
            FROM bookings b
            JOIN therapists t ON b.therapist = t.id
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            WHERE b.id = ?
        """, (booking_id,)).fetchone()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {
            "id": booking[0], "name": booking[1], "therapist": booking[2],
            "date": booking[3], "day": booking[4], "time": booking[5], "duration": booking[6],
            "notes": booking[7], "colour": booking[8], "user_id": booking[9],
            "profession": booking[10], "patient_id": booking[11], 
            "note_completed": bool(booking[12]), "billing_completed": bool(booking[13]),
            "therapist_name": booking[14], "therapist_profession": booking[15], "has_note": bool(booking[16])
        }


def create_booking(booking: Booking):
    """Create a new booking"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if booking ID already exists
        existing = cursor.execute(
            "SELECT id FROM bookings WHERE id = ?", (booking.id,)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Booking ID already exists")
        
        # Convert date from ISO string to YYYY-MM-DD format
        try:
            if 'T' in booking.date:  # ISO format
                date_only = booking.date.split('T')[0]
            else:
                date_only = booking.date
        except:
            date_only = booking.date
        
        # Convert string IDs to integers for database
        therapist_id = int(booking.therapist) if booking.therapist else None
        patient_id = int(booking.patient_id) if booking.patient_id else None
        
        # Insert new booking using correct column names
        cursor.execute("""
            INSERT INTO bookings (id, name, therapist, date, day, time, duration, 
                                notes, colour, profession, patient_id, billing_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            booking.id, booking.name, therapist_id, date_only, booking.day,
            booking.time, booking.duration, booking.notes, booking.colour,
            booking.profession, patient_id, booking.billing_completed
        ))
        
        conn.commit()
    
    return booking


def update_booking(booking_id: str, updates: Dict[str, Any]):
    """Update a booking"""
    with get_db_connection() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        
        for field, value in updates.items():
            # Use field names as they are since they match the database schema
            update_fields.append(f"{field} = ?")
            params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(booking_id)
        query = f"UPDATE bookings SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        conn.commit()
    
    # Return updated booking
    return get_booking_by_id(booking_id)


def delete_booking(booking_id: str):
    """Delete a booking"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Also delete related treatment notes
        cursor.execute("DELETE FROM treatment_notes WHERE appointment_id = ?", (booking_id,))
        cursor.execute("DELETE FROM billing_entries WHERE appointment_id = ?", (booking_id,))
        cursor.execute("DELETE FROM billing_sessions WHERE id = ?", (booking_id,))
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        conn.commit()
    
    return {"detail": "Booking deleted successfully"}


def get_bookings_for_day_for_therapists(date_str: str, therapist_ids: List[int]):
    """Get bookings for specific therapists on a specific day"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create placeholders for therapist IDs
        placeholders = ','.join(['?' for _ in therapist_ids])
        
        query = f"""
            SELECT b.*, t.name as therapist_name, t.profession,
                   CASE WHEN tn.appointment_id IS NOT NULL THEN 1 ELSE 0 END as has_note
            FROM bookings b
            JOIN therapists t ON b.therapist = t.id
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            WHERE b.date = ? AND b.therapist IN ({placeholders})
            ORDER BY b.time
        """
        
        params = [date_str] + therapist_ids
        bookings = cursor.execute(query, params).fetchall()
        
        return [
            {
                "id": booking[0], "patient_name": booking[1], "therapist_id": booking[2],
                "date": booking[3], "time": booking[4], "duration": booking[5],
                "notes": booking[6], "patient_id": booking[7], "billing_completed": bool(booking[8]),
                "therapist_name": booking[9], "profession": booking[10], "has_note": bool(booking[11])
            }
            for booking in bookings
        ]


def get_session_info(request: Request):
    """Get session information for current user"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "logged_in": True,
        "user_id": user_id,
        "username": request.session.get("username"),
        "role": request.session.get("role"),
        "linked_therapist_id": request.session.get("linked_therapist_id"),
        "permissions": request.session.get("permissions", [])
    }


def get_therapist_stats():
    """Get statistics for all therapists"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get comprehensive therapist statistics
        stats = cursor.execute("""
            WITH therapist_stats AS (
                SELECT 
                    t.id as therapist_id,
                    t.name as therapist_name,
                    -- Total appointments
                    COUNT(b.id) as total_appointments,
                    -- Recent appointments (30 days)
                    COUNT(CASE WHEN b.date >= date('now', '-30 days') THEN 1 END) as recent_appointments_30d,
                    -- Average note completion time (lifetime) - placeholder
                    NULL as avg_note_completion_minutes,
                    -- Average note completion time (30 days) - placeholder
                    NULL as avg_note_completion_minutes_30d,
                    -- Average invoice amount (lifetime)
                    AVG(i.total_amount) as avg_invoice_amount,
                    -- Average invoice amount (30 days)
                    AVG(CASE 
                        WHEN i.invoice_date >= date('now', '-30 days') 
                        THEN i.total_amount 
                    END) as avg_invoice_amount_30d,
                    -- Total invoiced (lifetime)
                    COALESCE(SUM(i.total_amount), 0) as total_invoiced,
                    -- Total invoiced (30 days)
                    COALESCE(SUM(CASE 
                        WHEN i.invoice_date >= date('now', '-30 days') 
                        THEN i.total_amount 
                    END), 0) as total_invoiced_30d
                FROM therapists t
                LEFT JOIN bookings b ON t.id = b.therapist
                LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
                LEFT JOIN invoices i ON t.id = i.therapist_id
                GROUP BY t.id, t.name
            )
            SELECT * FROM therapist_stats
            ORDER BY therapist_name
        """).fetchall()
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, stat)) for stat in stats]


def check_treatment_notes(appointment_ids: List[str]):
    """Check which appointments have treatment notes"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in appointment_ids])
        query = f"SELECT appointment_id FROM treatment_notes WHERE appointment_id IN ({placeholders})"
        
        existing_notes = cursor.execute(query, appointment_ids).fetchall()
        existing_ids = [note[0] for note in existing_notes]
        
        return {
            "appointments_with_notes": existing_ids,
            "appointments_without_notes": [aid for aid in appointment_ids if aid not in existing_ids]
        }


def check_treatment_note(appointment_id: str):
    """Check if a specific appointment has a treatment note"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        note = cursor.execute(
            "SELECT appointment_id FROM treatment_notes WHERE appointment_id = ?",
            (appointment_id,)
        ).fetchone()
        
        return {"has_note": note is not None}


def get_treatment_note_full(appointment_id: str):
    """Get full treatment note for an appointment with billing and supplementary notes"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get main treatment note
        note = cursor.execute("""
            SELECT tn.*, b.name as patient_name, b.date, b.time, t.name as therapist_name, t.profession
            FROM treatment_notes tn
            JOIN bookings b ON tn.appointment_id = b.id
            JOIN therapists t ON b.therapist = t.id
            WHERE tn.appointment_id = ?
        """, (appointment_id,)).fetchone()
        
        if not note:
            raise HTTPException(status_code=404, detail="Treatment note not found")
        
        columns = [description[0] for description in cursor.description]
        result = dict(zip(columns, note))
        
        # Get billing information
        billing_data = cursor.execute("""
            SELECT be.*, bc.code, bc.description, bc.base_fee, bm.modifier_name, bm.modifier_description
            FROM billing_entries be
            JOIN billing_codes bc ON be.code_id = bc.code
            LEFT JOIN billing_modifiers bm ON be.billing_modifier = bm.modifier_code
            WHERE be.appointment_id = ?
            ORDER BY be.id
        """, (appointment_id,)).fetchall()
        
        if billing_data:
            billing_columns = [description[0] for description in cursor.description]
            result["billing"] = [dict(zip(billing_columns, entry)) for entry in billing_data]
        else:
            result["billing"] = []
        
        # Get supplementary notes with author information
        supplementary_data = cursor.execute("""
            SELECT sn.*, u.username as author_username
            FROM supplementary_notes sn
            JOIN users u ON sn.user_id = u.id
            WHERE sn.appointment_id = ?
            ORDER BY sn.timestamp DESC
        """, (appointment_id,)).fetchall()
        
        if supplementary_data:
            supp_columns = [description[0] for description in cursor.description]
            result["supplementary"] = [dict(zip(supp_columns, entry)) for entry in supplementary_data]
        else:
            result["supplementary"] = []
        
        return result