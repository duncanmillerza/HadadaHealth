"""
Billing and invoicing module for HadadaHealth
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from fastapi import Request, HTTPException
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

from .database import get_db_connection


class BillingCode(BaseModel):
    code: str
    description: str
    profession: str
    fee: float
    pmb_indicator: Optional[str] = None


class Invoice(BaseModel):
    patient_id: int
    therapist_id: int
    invoice_date: str
    due_date: Optional[str] = None
    status: str = "Draft"
    notes: Optional[str] = None
    total_amount: float = 0.0


def create_billing_session(data: dict, request: Request):
    """Create a new billing session with associated billing entries"""
    session_data = data.get("session")
    entries_data = data.get("entries", [])

    if not session_data or not entries_data:
        raise HTTPException(status_code=400, detail="Session and entries are required")

    # ensure we have a therapist_id (fall back to session-linked therapist)
    therapist_id = session_data.get("therapist_id") or request.session.get("linked_therapist_id")
    if not therapist_id:
        raise HTTPException(status_code=400, detail="Therapist ID is required")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        session_id = session_data["id"]
        
        # Create billing session
        cursor.execute("""
            INSERT INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            session_data["patient_id"],
            therapist_id,
            session_data["session_date"],
            session_data.get("notes", ""),
            session_data.get("total_amount", 0)
        ))
        
        # Create billing entries
        for entry in entries_data:
            cursor.execute("""
                INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"{session_id}-{entry['code_id']}",
                session_id,
                entry["code_id"],
                entry.get("billing_modifier", ""),
                entry["final_fee"]
            ))
        
        # Create invoice
        cursor.execute("""
            INSERT OR REPLACE INTO invoices (
                id, appointment_id, patient_id, therapist_id, invoice_date,
                due_date, status, notes, total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "INV" + session_id[4:],
            session_id,
            session_data["patient_id"],
            therapist_id,
            session_data["session_date"],
            None,
            'Draft',
            session_data.get("notes", ""),
            session_data.get("total_amount", 0)
        ))
        
        # Mark booking as billing completed
        cursor.execute(
            "UPDATE bookings SET billing_completed = 1 WHERE id = ?",
            (session_id,)
        )
        
        conn.commit()
    
    return {"detail": "Billing session and entries created successfully"}


def submit_billing(data: dict):
    """Submit a full billing payload (overwrite session and entries)"""
    session_data = data.get("session")
    entries_data = data.get("entries", [])

    if not session_data or not entries_data:
        raise HTTPException(status_code=400, detail="Session and entries are required")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        session_id = session_data["id"]
        
        # Delete existing entries for this session
        cursor.execute("DELETE FROM billing_entries WHERE appointment_id = ?", (session_id,))
        
        # Insert/Update billing session
        cursor.execute("""
            INSERT OR REPLACE INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            session_data["patient_id"],
            session_data["therapist_id"],
            session_data["session_date"],
            session_data.get("notes", ""),
            session_data.get("total_amount", 0)
        ))
        
        # Insert new entries
        for entry in entries_data:
            cursor.execute("""
                INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"{session_id}-{entry['code_id']}",
                session_id,
                entry["code_id"],
                entry.get("billing_modifier", ""),
                entry["final_fee"]
            ))
        
        conn.commit()
    
    return {"detail": "Billing updated successfully"}


def get_billing_codes():
    """Get all billing codes"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        codes = cursor.execute("""
            SELECT id, code, description, profession, base_fee
            FROM billing_codes
            ORDER BY profession, code
        """).fetchall()
        
        return [
            {
                "id": code[0], "code": code[1], "description": code[2],
                "profession": code[3], "base_fee": code[4]
            }
            for code in codes
        ]


def get_billing_codes_for_profession(profession: str):
    """Get billing codes for a specific profession"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        codes = cursor.execute("""
            SELECT id, code, description, base_fee
            FROM billing_codes
            WHERE LOWER(profession) = LOWER(?)
            ORDER BY code
        """, (profession,)).fetchall()
        
        return [
            {
                "id": code[0], "code": code[1], "description": code[2],
                "base_fee": code[3]
            }
            for code in codes
        ]


def get_billing_modifiers():
    """Get all billing modifiers"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        modifiers = cursor.execute("""
            SELECT modifier_code, modifier_name, modifier_description, 
                   modifier_effect, modifier_multiplier, profession
            FROM billing_modifiers
            ORDER BY modifier_code
        """).fetchall()
        
        return [
            {
                "modifier_code": mod[0], "modifier_name": mod[1], 
                "modifier_description": mod[2], "modifier_effect": mod[3],
                "modifier_multiplier": mod[4], "profession": mod[5]
            }
            for mod in modifiers
        ]


def update_billing_code(code_id: int, updates: Dict[str, Any]):
    """Update a billing code"""
    with get_db_connection() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        
        for field, value in updates.items():
            update_fields.append(f"{field} = ?")
            params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(code_id)
        query = f"UPDATE billing_codes SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Billing code not found")
    
    return {"detail": "Billing code updated successfully"}


def delete_billing_code(code_id: int):
    """Delete a billing code"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM billing_codes WHERE id = ?", (code_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Billing code not found")
    
    return {"detail": "Billing code deleted successfully"}


def get_billing_sessions(patient_id: int):
    """Get billing sessions for a patient"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sessions = cursor.execute("""
            SELECT bs.*, t.name as therapist_name
            FROM billing_sessions bs
            JOIN therapists t ON bs.therapist_id = t.id
            WHERE bs.patient_id = ?
            ORDER BY bs.session_date DESC
        """, (patient_id,)).fetchall()
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, session)) for session in sessions]


def complete_billing(booking_id: int):
    """Mark a booking as billing completed"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE bookings SET billing_completed = 1 WHERE id = ?",
            (booking_id,)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"detail": "Billing marked as completed"}


def get_unbilled_treatment_notes():
    """Get treatment notes that haven't been billed yet"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        notes = cursor.execute("""
            SELECT tn.appointment_id, b.patient_name, b.date, b.time,
                   t.name as therapist_name, t.profession,
                   tn.session_type, tn.session_length
            FROM treatment_notes tn
            JOIN bookings b ON tn.appointment_id = b.id
            JOIN therapists t ON b.therapist_id = t.id
            WHERE b.billing_completed = 0
            ORDER BY b.date DESC, b.time DESC
        """).fetchall()
        
        return [
            {
                "appointment_id": note[0], "patient_name": note[1], "date": note[2],
                "time": note[3], "therapist_name": note[4], "profession": note[5],
                "session_type": note[6], "session_length": note[7]
            }
            for note in notes
        ]


def create_billing_for_appointment(appointment_data: dict):
    """Create billing for a specific appointment"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert billing session
        cursor.execute("""
            INSERT INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            appointment_data["appointment_id"],
            appointment_data["patient_id"],
            appointment_data["therapist_id"],
            appointment_data["session_date"],
            appointment_data.get("notes", ""),
            appointment_data.get("total_amount", 0)
        ))
        
        # Insert billing entries
        for entry in appointment_data.get("entries", []):
            cursor.execute("""
                INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"{appointment_data['appointment_id']}-{entry['code_id']}",
                appointment_data["appointment_id"],
                entry["code_id"],
                entry.get("billing_modifier", ""),
                entry["final_fee"]
            ))
        
        # Mark booking as billed
        cursor.execute(
            "UPDATE bookings SET billing_completed = 1 WHERE id = ?",
            (appointment_data["appointment_id"],)
        )
        
        conn.commit()
    
    return {"detail": "Billing created for appointment"}


def get_invoices():
    """Get all invoices"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        invoices = cursor.execute("""
            SELECT i.*, p.first_name, p.surname, t.name as therapist_name
            FROM invoices i
            JOIN patients p ON i.patient_id = p.id
            JOIN therapists t ON i.therapist_id = t.id
            ORDER BY i.invoice_date DESC
        """).fetchall()
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, invoice)) for invoice in invoices]


def create_invoice(invoice_data: dict):
    """Create a new invoice"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (patient_id, therapist_id, invoice_date, due_date, 
                                status, notes, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_data["patient_id"],
            invoice_data["therapist_id"],
            invoice_data["invoice_date"],
            invoice_data.get("due_date"),
            invoice_data.get("status", "Draft"),
            invoice_data.get("notes", ""),
            invoice_data.get("total_amount", 0)
        ))
        
        invoice_id = cursor.lastrowid
        conn.commit()
    
    return {"id": invoice_id, "detail": "Invoice created successfully"}


def get_invoice_by_id(invoice_id: int):
    """Get a specific invoice by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        invoice = cursor.execute("""
            SELECT i.*, p.first_name, p.surname, p.email, p.contact_number,
                   t.name as therapist_name
            FROM invoices i
            JOIN patients p ON i.patient_id = p.id
            JOIN therapists t ON i.therapist_id = t.id
            WHERE i.id = ?
        """, (invoice_id,)).fetchone()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, invoice))


def update_invoice(invoice_id: int, updates: Dict[str, Any]):
    """Update an invoice"""
    with get_db_connection() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        
        for field, value in updates.items():
            update_fields.append(f"{field} = ?")
            params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(invoice_id)
        query = f"UPDATE invoices SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"detail": "Invoice updated successfully"}


def delete_invoice(invoice_id: int):
    """Delete an invoice"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"detail": "Invoice deleted successfully"}


def generate_invoice_pdf(invoice_id: int):
    """Generate PDF for an invoice"""
    invoice = get_invoice_by_id(invoice_id)
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"Invoice #{invoice['id']}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Invoice details
    details_data = [
        ['Patient:', f"{invoice['first_name']} {invoice['surname']}"],
        ['Therapist:', invoice['therapist_name']],
        ['Date:', invoice['invoice_date']],
        ['Due Date:', invoice['due_date'] or 'Not specified'],
        ['Status:', invoice['status']],
        ['Total:', f"R{invoice['total_amount']:.2f}"]
    ]
    
    details_table = Table(details_data)
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(details_table)
    
    if invoice['notes']:
        story.append(Spacer(1, 12))
        notes = Paragraph(f"<b>Notes:</b> {invoice['notes']}", styles['Normal'])
        story.append(notes)
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()