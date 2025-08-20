"""
Billing and invoice management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime
import json
from io import BytesIO
from reportlab.pdfgen import canvas
import textwrap
from .database import get_db_connection, execute_query
import sqlite3


def get_billing_codes() -> List[Dict[str, Any]]:
    """
    Get all billing codes
    
    Returns:
        List of billing code dictionaries
    """
    query = "SELECT * FROM billing_codes ORDER BY code"
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def get_billing_codes_for_profession(profession: str) -> List[Dict[str, Any]]:
    """
    Get billing codes for a specific profession
    
    Args:
        profession: The profession name
        
    Returns:
        List of billing code dictionaries
    """
    query = """
        SELECT * FROM billing_codes 
        WHERE profession = ? OR profession IS NULL OR profession = ''
        ORDER BY code
    """
    results = execute_query(query, (profession,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_billing_modifiers() -> List[Dict[str, Any]]:
    """
    Get all billing modifiers
    
    Returns:
        List of billing modifier dictionaries
    """
    query = "SELECT * FROM billing_modifiers ORDER BY modifier"
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def create_billing_session(data: Dict[str, Any]) -> int:
    """
    Create a new billing session
    
    Args:
        data: Billing session data
        
    Returns:
        The ID of the created billing session
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            INSERT INTO billing_sessions (patient_id, session_date, therapist_id, total_amount, notes)
            VALUES (?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            data.get('patient_id'),
            data.get('session_date'),
            data.get('therapist_id'),
            data.get('total_amount', 0),
            data.get('notes', '')
        ))
        
        session_id = cursor.lastrowid
        conn.commit()
        return session_id
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create billing session: {str(e)}")
    finally:
        conn.close()


def submit_billing(data: Dict[str, Any]) -> bool:
    """
    Submit billing information for an appointment
    
    Args:
        data: Billing data containing entries and session info
        
    Returns:
        True if successful
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        patient_id = data.get('patient_id')
        appointment_id = data.get('appointment_id')
        entries = data.get('entries', [])
        
        # Delete existing billing entries for this appointment
        cursor.execute(
            "DELETE FROM billing_entries WHERE patient_id = ? AND appointment_id = ?",
            (patient_id, appointment_id)
        )
        
        # Insert new billing entries
        for entry in entries:
            cursor.execute("""
                INSERT INTO billing_entries (
                    patient_id, appointment_id, code_id, quantity, 
                    modifier, amount, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                appointment_id,
                entry.get('code_id'),
                entry.get('quantity', 1),
                entry.get('modifier', ''),
                entry.get('amount', 0),
                entry.get('notes', '')
            ))
        
        # Mark appointment billing as completed
        cursor.execute(
            "UPDATE bookings SET billing_completed = 1 WHERE id = ?",
            (appointment_id,)
        )
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit billing: {str(e)}")
    finally:
        conn.close()


def get_billing_sessions(patient_id: int) -> List[Dict[str, Any]]:
    """
    Get billing sessions for a patient
    
    Args:
        patient_id: The patient ID
        
    Returns:
        List of billing session dictionaries
    """
    query = """
        SELECT bs.*, t.name as therapist_name
        FROM billing_sessions bs
        LEFT JOIN therapists t ON bs.therapist_id = t.id
        WHERE bs.patient_id = ?
        ORDER BY bs.session_date DESC
    """
    
    results = execute_query(query, (patient_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_all_invoices() -> List[Dict[str, Any]]:
    """
    Get all invoices with their details
    
    Returns:
        List of invoice dictionaries
    """
    query = """
        SELECT i.*, p.first_name, p.surname, t.name as therapist_name, t.profession
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id = p.id
        LEFT JOIN therapists t ON i.therapist_id = t.id
        ORDER BY i.created_at DESC
    """
    
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def create_invoice(invoice_data: Dict[str, Any]) -> int:
    """
    Create a new invoice
    
    Args:
        invoice_data: Invoice data dictionary
        
    Returns:
        The ID of the created invoice
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            INSERT INTO invoices (
                patient_id, therapist_id, invoice_date, due_date,
                subtotal, tax_amount, total_amount, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            invoice_data.get('patient_id'),
            invoice_data.get('therapist_id'),
            invoice_data.get('invoice_date', datetime.now().date()),
            invoice_data.get('due_date'),
            invoice_data.get('subtotal', 0),
            invoice_data.get('tax_amount', 0),
            invoice_data.get('total_amount', 0),
            invoice_data.get('status', 'draft'),
            invoice_data.get('notes', '')
        ))
        
        invoice_id = cursor.lastrowid
        conn.commit()
        return invoice_id
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")
    finally:
        conn.close()


def get_invoice_by_id(invoice_id: int) -> Optional[Dict[str, Any]]:
    """
    Get an invoice by ID
    
    Args:
        invoice_id: The invoice ID
        
    Returns:
        Invoice dictionary or None if not found
    """
    query = """
        SELECT i.*, p.first_name, p.surname, p.address, p.email,
               t.name as therapist_name, t.profession
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id = p.id
        LEFT JOIN therapists t ON i.therapist_id = t.id
        WHERE i.id = ?
    """
    
    result = execute_query(query, (invoice_id,), fetch='one')
    return dict(result) if result else None


def update_invoice(invoice_id: int, invoice_data: Dict[str, Any]) -> bool:
    """
    Update an existing invoice
    
    Args:
        invoice_id: The invoice ID to update
        invoice_data: Updated invoice data
        
    Returns:
        True if successful
    """
    conn = get_db_connection()
    try:
        # Check if invoice exists
        existing = get_invoice_by_id(invoice_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        cursor = conn.cursor()
        query = """
            UPDATE invoices SET
                due_date = ?, subtotal = ?, tax_amount = ?,
                total_amount = ?, status = ?, notes = ?
            WHERE id = ?
        """
        
        cursor.execute(query, (
            invoice_data.get('due_date'),
            invoice_data.get('subtotal'),
            invoice_data.get('tax_amount'),
            invoice_data.get('total_amount'),
            invoice_data.get('status'),
            invoice_data.get('notes'),
            invoice_id
        ))
        
        conn.commit()
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update invoice: {str(e)}")
    finally:
        conn.close()


def delete_invoice(invoice_id: int) -> bool:
    """
    Delete an invoice
    
    Args:
        invoice_id: The invoice ID to delete
        
    Returns:
        True if successful
    """
    conn = get_db_connection()
    try:
        # Check if invoice exists
        existing = get_invoice_by_id(invoice_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete invoice: {str(e)}")
    finally:
        conn.close()


def generate_invoice_pdf(invoice_id: int) -> BytesIO:
    """
    Generate PDF for an invoice
    
    Args:
        invoice_id: The invoice ID
        
    Returns:
        BytesIO object containing the PDF data
        
    Raises:
        HTTPException: If invoice not found or generation fails
    """
    invoice = get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        
        # Invoice header
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, 750, "INVOICE")
        
        p.setFont("Helvetica", 12)
        p.drawString(50, 720, f"Invoice ID: {invoice['id']}")
        p.drawString(50, 700, f"Date: {invoice['invoice_date']}")
        p.drawString(50, 680, f"Due Date: {invoice['due_date']}")
        
        # Patient information
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, 640, "Bill To:")
        
        p.setFont("Helvetica", 12)
        patient_name = f"{invoice['first_name']} {invoice['surname']}"
        p.drawString(50, 620, patient_name)
        
        if invoice['address']:
            # Wrap address text
            address_lines = textwrap.wrap(invoice['address'], width=50)
            y_pos = 600
            for line in address_lines:
                p.drawString(50, y_pos, line)
                y_pos -= 20
        
        # Therapist information
        p.setFont("Helvetica-Bold", 14)
        p.drawString(350, 640, "From:")
        
        p.setFont("Helvetica", 12)
        p.drawString(350, 620, invoice['therapist_name'])
        p.drawString(350, 600, invoice['profession'])
        
        # Invoice totals
        y_pos = 400
        p.setFont("Helvetica", 12)
        p.drawString(350, y_pos, f"Subtotal: R{invoice['subtotal']:.2f}")
        y_pos -= 20
        p.drawString(350, y_pos, f"Tax: R{invoice['tax_amount']:.2f}")
        y_pos -= 20
        p.setFont("Helvetica-Bold", 14)
        p.drawString(350, y_pos, f"Total: R{invoice['total_amount']:.2f}")
        
        # Notes
        if invoice['notes']:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, 300, "Notes:")
            p.setFont("Helvetica", 10)
            
            notes_lines = textwrap.wrap(invoice['notes'], width=80)
            y_pos = 280
            for line in notes_lines:
                p.drawString(50, y_pos, line)
                y_pos -= 15
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


def update_billing_code(code_id: int, code_data: Dict[str, Any]) -> bool:
    """
    Update a billing code
    
    Args:
        code_id: The billing code ID
        code_data: Updated code data
        
    Returns:
        True if successful
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            UPDATE billing_codes SET
                code = ?, description = ?, amount = ?, profession = ?
            WHERE id = ?
        """
        
        cursor.execute(query, (
            code_data.get('code'),
            code_data.get('description'),
            code_data.get('amount'),
            code_data.get('profession'),
            code_id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update billing code: {str(e)}")
    finally:
        conn.close()


def delete_billing_code(code_id: int) -> bool:
    """
    Delete a billing code
    
    Args:
        code_id: The billing code ID to delete
        
    Returns:
        True if successful
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM billing_codes WHERE id = ?", (code_id,))
        conn.commit()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete billing code: {str(e)}")
    finally:
        conn.close()


def complete_appointment_billing(booking_id: int) -> bool:
    """
    Mark appointment billing as completed
    
    Args:
        booking_id: The booking/appointment ID
        
    Returns:
        True if successful
    """
    query = "UPDATE bookings SET billing_completed = 1 WHERE id = ?"
    execute_query(query, (booking_id,))
    return True


def get_billing_for_appointment(appointment_id: int) -> List[Dict[str, Any]]:
    """
    Get billing entries for a specific appointment
    
    Args:
        appointment_id: The appointment ID
        
    Returns:
        List of billing entry dictionaries
    """
    query = """
        SELECT be.*, bc.code, bc.description, bc.amount as code_amount
        FROM billing_entries be
        LEFT JOIN billing_codes bc ON be.code_id = bc.id
        WHERE be.appointment_id = ?
        ORDER BY be.id
    """
    
    results = execute_query(query, (appointment_id,), fetch='all')
    return [dict(row) for row in results] if results else []