# Standard library imports
import json
import logging
import os
import sqlite3
import smtplib
import ssl
import textwrap
from datetime import datetime
from io import BytesIO
from typing import List, Optional

# Third-party imports
import bcrypt
import httpx
import pandas as pd
from dotenv import load_dotenv
from fastapi import (
    FastAPI, HTTPException, Depends, Request, Query, Body,
    UploadFile, File, APIRouter, Path
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, Response, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from reportlab.pdfgen import canvas
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from email.message import EmailMessage

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import our modular utilities
from modules.database import get_db_connection
from modules.appointments import (
    Booking, get_bookings, get_booking_by_id, create_booking,
    update_booking, delete_booking, get_bookings_for_day_for_therapists,
    check_treatment_notes
)
from modules.treatment_notes import (
    submit_treatment_note, get_full_treatment_note, add_supplementary_note,
    check_treatment_note, get_latest_session_note, get_unbilled_treatment_notes
)
from modules.therapists import (
    Therapist, get_all_therapists, get_therapist_by_id, get_therapist_basic_info,
    create_therapist, update_therapist, delete_therapist, import_therapists_from_excel,
    get_therapist_stats
)
from modules.medical_aids import (
    MedicalAid, get_all_medical_aids, get_all_medical_aids_full, create_medical_aid,
    update_medical_aid, delete_medical_aid, get_medical_aid_plans, import_medical_aids_from_excel
)
from modules.auth import (
    security, login_user, logout_user, check_login_status, serve_login_page,
    get_all_users, create_user, signup_user, update_user, delete_user
)
from modules.professions_clinics import (
    get_all_professions, create_profession, update_profession, delete_profession,
    get_all_clinics, create_clinic, update_clinic, delete_clinic
)

# Initialize FastAPI app and router
app = FastAPI()
router = APIRouter()
# security is now imported from modules.auth


# --- Favicon route: silence 404s until a real icon is added ---
@app.get("/favicon.ico")
async def favicon():
    # Silence favicon 404s until a real icon is added
    return Response(status_code=204)


# Add SessionMiddleware for user sessions
# NOTE: Change "SUPER_SECRET_KEY" to a strong secret in production!
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY")

# patient_id should be str for compatibility with string-based IDs
@app.put("/api/patient/{patient_id}/alerts/{appointment_id}/resolve")
def toggle_alert_resolution(patient_id: str, appointment_id: str, payload: dict = Body(...)):
    # Ensure resolved is interpreted as a Python boolean
    resolved = payload.get("resolved", False)
    if isinstance(resolved, str):
        resolved = resolved.lower() == "true"
    elif isinstance(resolved, int):
        resolved = bool(resolved)
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            UPDATE treatment_notes
            SET alert_resolved = ?
            WHERE patient_id = ? AND appointment_id = ?
        """, ("Yes" if resolved else "No", patient_id, appointment_id))
    return {"status": "updated"}
# --- New endpoint: Get latest alerts for a patient ---
@app.get("/api/patient/{patient_id}/alerts")
def get_alerts(patient_id: str):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT appointment_id, appointment_date, therapist_name, profession, alert_comment, alert_resolved
            FROM treatment_notes
            WHERE patient_id = ? AND alert_comment IS NOT NULL AND alert_comment != ''
            ORDER BY appointment_date DESC
            LIMIT 5
        """, (patient_id,))
        alerts = [
            {
                "id": row[0],
                "date": row[1],
                "therapist": row[2],
                "profession": row[3],
                "note": row[4],
                "resolved": row[5]
            } for row in cursor.fetchall()
        ]
    return alerts
import re
# --- Helper function for generating AI medical history summary ---
async def generate_ai_medical_history(patient_id: str) -> str:
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute(
            """
            SELECT appointment_date, start_time, profession, therapist_name,
                   subjective_findings, objective_findings, treatment, plan, duration
            FROM treatment_notes
            WHERE patient_id = ?
            ORDER BY appointment_date ASC, start_time ASC
            """,
            (patient_id,)
        )
        notes = cursor.fetchall()

    if not notes:
        raise HTTPException(status_code=404, detail="No treatment notes found for this patient.")

    notes_dicts = [
        {
            "date": note[0] or "",
            "time": note[1] or "",
            "profession": note[2] or "",
            "therapist": note[3] or "",
            "subjective_findings": note[4] or "",
            "objective_findings": note[5] or "",
            "treatment": note[6] or "",
            "plan": note[7] or "",
            "duration_minutes": note[8] if len(note) > 8 and note[8] is not None else "",
        }
        for note in notes
    ]

    combined_notes = "\n\n".join([
        f"Session on {note['date']} at {note['time']} with {note['therapist']} ({note['profession']}) — Duration: {note['duration_minutes']} minutes\n"
        f"Subjective: {note['subjective_findings']}\n"
        f"Objective: {note['objective_findings']}\n"
        f"Treatment: {note['treatment']}\n"
        f"Plan: {note['plan']}"
        for note in notes_dicts
    ])

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "mistralai/mistral-nemo:free",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant summarising clinical notes for healthcare professionals."},
            {"role": "user", "content": f"Please extract the medical history and level of function from the following notes:\n{combined_notes}. Never make anything up, only use the information provided. If there is not enough information, say 'No information available'. For headings please use html strong text"}
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
        res.raise_for_status()
        summary = res.json()["choices"][0]["message"]["content"]
        summary = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", summary)
        return summary


# AI summary endpoint (fetches real treatment notes from DB)
@router.get("/api/patient/{patient_id}/summary/ai")
async def get_ai_summary(patient_id: str):
    summary = await generate_ai_medical_history(patient_id)
    return {"summary": summary}

# --- New endpoint: Get latest treatment note summary for patient and profession, with AI summary ---


@app.get("/api/patient/{patient_id}/summary/{profession}/latest")
async def get_latest_note_summary(patient_id: str, profession: str):
    # Use the same DB as the rest of the app
    db_path = "data/bookings.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            appointment_date,
            start_time,
            duration,
            therapist_name,
            profession,
            subjective_findings,
            objective_findings,
            treatment,
            plan
        FROM treatment_notes
        WHERE patient_id = ? AND LOWER(profession) = LOWER(?)
        ORDER BY appointment_date DESC, start_time DESC
        LIMIT 1
    """, (patient_id, profession))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No treatment notes found for this profession")

    note = {
        "date": row[0],
        "time": row[1],
        "duration": row[2],
        "therapist": row[3],
        "profession": row[4],
        "subjective": row[5],
        "objective": row[6],
        "treatment": row[7],
        "plan": row[8],
    }

    full_text = (
        f"Date: {note['date']} {note['time']} ({note['duration']})\n"
        f"Therapist: {note['therapist']} ({note['profession']})\n"
        f"Subjective: {note['subjective']}\n"
        f"Objective: {note['objective']}\n"
        f"Treatment: {note['treatment']}\n"
        f"Plan: {note['plan']}"
    )

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "HadadaHealth"
    }

    body = {
        "model": "mistralai/mistral-nemo:free",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant summarising clinical notes for healthcare professionals."},
            {"role": "user", "content": f"Please write a short paragraph summary (no more than 4 sentances) in simple pros of the latest session with a focus on what was worked on and what the plan is:\n{full_text}"}
        ]
    }

    # Write the AI prompt to a file for debugging (before POST request)
    with open("debug_ai_prompt_latest.json", "w") as f:
        json.dump(body["messages"], f, indent=2)

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)

    if res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"OpenRouter Error: {res.text}")

    data = res.json()
    return {"summary": data["choices"][0]["message"]["content"]}

# --- New endpoint: Get latest session note for a patient and profession

@app.get("/api/patient/{patient_id}/latest-session-note/{profession}")
def get_latest_session_note(patient_id: int, profession: str):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT appointment_date, start_time, therapist_name, subjective_findings, objective_findings, treatment, plan, note_to_patient
            FROM treatment_notes
            WHERE patient_id = ? AND LOWER(profession) = LOWER(?)
            ORDER BY appointment_date DESC, start_time DESC
            LIMIT 1
        """, (patient_id, profession))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No treatment note found")
        return {
            "date": row[0],
            "start_time": row[1],
            "therapist_name": row[2],
            "subjective_findings": row[3],
            "objective_findings": row[4],
            "treatment": row[5],
            "plan": row[6],
            "note_to_patient": row[7]
        }

# --- Batch endpoint: Check treatment notes for multiple appointment IDs ---

@app.get("/api/check-treatment-notes")
def check_treatment_notes(ids: str = Query(..., description="Comma separated appointment IDs")):
    id_list = ids.split(",")
    placeholders = ",".join("?" for _ in id_list)
    sql = f"SELECT appointment_id FROM treatment_notes WHERE appointment_id IN ({placeholders})"
    with sqlite3.connect("data/bookings.db") as conn:
        rows = conn.execute(sql, id_list).fetchall()
    found = {row[0] for row in rows}
    return [{"id": appt_id, "has_note": appt_id in found} for appt_id in id_list]

# POST endpoint to create a new billing session with associated billing entries
@app.post("/billing-sessions")
def create_billing_session(data: dict, request: Request):
    session_data = data.get("session")
    entries_data = data.get("entries", [])

    if not session_data or not entries_data:
        raise HTTPException(status_code=400, detail="Session and entries are required")

    # ensure we have a therapist_id (fall back to session-linked therapist)
    therapist_id = session_data.get("therapist_id") or request.session.get("linked_therapist_id")
    if not therapist_id:
        raise HTTPException(status_code=400, detail="Therapist ID is required")

    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()
        session_id = session_data["id"]
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
        for entry in entries_data:
            cursor.execute("""
                INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"{session_id}-{entry['code_id']}",  # unique entry ID
                session_id,                          # appointment reference
                entry["code_id"],                    # billing code foreign key
                entry.get("billing_modifier", ""),   # any modifier
                entry["final_fee"]                   # final fee charged
            ))
        # Also insert into invoices table for this session
        cursor.execute("""
            INSERT OR REPLACE INTO invoices (
                id,
                appointment_id,
                patient_id,
                therapist_id,
                invoice_date,
                due_date,
                status,
                notes,
                total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "INV" + session_id[4:],         # invoice id as "INV" + session_id[4:]
            session_id,                  # appointment reference
            session_data["patient_id"],
            therapist_id,
            session_data["session_date"],
            None,                        # due_date blank for now
            'Draft',                     # initial status
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


# --- New: POST endpoint to submit a full billing payload (overwrite session and entries) ---
@app.post("/submit-billing")
def submit_billing(data: dict):
    session_data = data.get("session")
    entries_data = data.get("entries", [])

    if not session_data or not entries_data:
        raise HTTPException(status_code=400, detail="Session and entries are required")

    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()

        # Insert or replace billing session
        cursor.execute("""
            INSERT OR REPLACE INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_data["id"],  # appointment_id as billing session ID
            session_data["patient_id"],
            session_data["therapist_id"],
            session_data["session_date"],
            session_data.get("notes", ""),
            session_data.get("total_amount", 0)
        ))

        # Delete any previous entries for this appointment to avoid duplicates
        cursor.execute("DELETE FROM billing_entries WHERE appointment_id = ?", (session_data["id"],))

        # Insert new billing entries
        for entry in entries_data:
            cursor.execute("""
                INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"{session_data['id']}-{entry['code_id']}",  # unique ID
                session_data["id"],
                entry["code_id"],
                entry.get("billing_modifier", ""),
                entry["final_fee"]
            ))
        # Also upsert invoice for this session
        cursor.execute("""
            INSERT OR REPLACE INTO invoices (
                id,
                appointment_id,
                patient_id,
                therapist_id,
                invoice_date,
                due_date,
                status,
                notes,
                total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "INV" + session_data["id"][4:],  # invoice id as "INV" + session_data["id"][4:]
            session_data["id"],
            session_data["patient_id"],
            session_data["therapist_id"],
            session_data["session_date"],
            None,
            'Draft',
            session_data.get("notes", ""),
            session_data.get("total_amount", 0)
        ))
        # Also update the booking to mark billing as completed
        cursor.execute(
            "UPDATE bookings SET billing_completed = 1 WHERE id = ?",
            (session_data["id"],)
        )

        # Also create or update an invoice record for this billing session
        cursor.execute("""
            INSERT OR REPLACE INTO invoices (
                id,
                appointment_id,
                patient_id,
                therapist_id,
                invoice_date,
                due_date,
                status,
                notes,
                total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "INV-" + session_data["id"],     # invoice id
            session_data["id"],              # appointment reference
            session_data["patient_id"],
            session_data["therapist_id"],
            session_data["session_date"],
            None,                            # due_date blank
            'Draft',                         # initial status
            session_data.get("notes", ""),
            session_data.get("total_amount", 0)
        ))
        conn.commit()

    return {"detail": "Billing saved successfully"}


# --- GET: Return all billing codes as JSON ---
@app.get("/api/billing_codes")
def get_billing_codes():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT id, code, description, base_fee, profession FROM billing_codes;")
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

# GET endpoint to retrieve billing sessions with their entries for a patient
@app.get("/billing-sessions/{patient_id}")
def get_billing_sessions(patient_id: int):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT * FROM billing_sessions WHERE patient_id = ?
        """, (patient_id,))
        sessions = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

        for session in sessions:
            entry_cursor = conn.execute("""
                SELECT * FROM billing_entries WHERE appointment_id = ?
            """, (session["id"],))
            session["entries"] = [dict(zip([col[0] for col in entry_cursor.description], row)) for row in entry_cursor.fetchall()]
    return sessions

# --- New endpoint: List all invoices with their entries and therapist profession ---
@app.get("/invoices")
def list_invoices():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT i.*, t.profession AS therapist_profession
            FROM invoices i
            LEFT JOIN therapists t ON i.therapist_id = t.id
        """)
        cols = [col[0] for col in cursor.description]
        invoices = [dict(zip(cols, row)) for row in cursor.fetchall()]
        for inv in invoices:
            entry_cursor = conn.execute(
                "SELECT code_id, billing_modifier, final_fee FROM billing_entries WHERE appointment_id = ?",
                (inv["appointment_id"],)
            )
            inv["entries"] = [
                {"code_id": row[0], "billing_modifier": row[1], "final_fee": row[2]}
                for row in entry_cursor.fetchall()
            ]
    return invoices

# --- PDF endpoint for invoices ---
@app.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id: str):
    """
    Generate and return a PDF of the specified invoice.
    """
    # Fetch invoice header
    with sqlite3.connect("data/bookings.db") as conn:
        cur = conn.execute("SELECT id, appointment_id, patient_id, therapist_id, invoice_date, status, total_amount FROM invoices WHERE id = ?", (invoice_id,))
        inv = cur.fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        # Unpack invoice tuple into descriptive variables
        invoice_id, appointment_id, patient_id_val, therapist_id_val, invoice_date, status, total_amount = inv
        # Fetch patient details
        pcur = conn.execute("""
            SELECT id AS patient_table_id, medical_aid_name, plan_name, dependent_number, claim_number, main_member_name,
                   first_name, surname, icd10_codes
            FROM patients WHERE id = ?
        """, (patient_id_val,))
        prow = pcur.fetchone()
        if prow:
            patient_table_id = prow[0]
            med_aid = prow[1] or ""
            plan = prow[2] or ""
            dependent_no = prow[3] or ""
            membership_no = prow[4] or ""
            principal_member = prow[5] or ""
            first_name = prow[6] or ""
            surname = prow[7] or ""
            patient_icd10_codes = prow[8] or ""
            # patient_name_full: combine first_name and full surname
            patient_name_full = f"{first_name} {surname}"
        else:
            patient_table_id = ""
            med_aid = plan = dependent_no = membership_no = principal_member = patient_name_full = patient_icd10_codes = ""
        # Fetch therapist details
        tcur = conn.execute("""
            SELECT name, surname, profession
            FROM therapists WHERE id = ?
        """, (therapist_id_val,))
        trow = tcur.fetchone()
        if trow:
            name, t_surname, provider_profession = trow
            provider_name = f"{name} {t_surname}"
        else:
            provider_name = ""
            provider_profession = ""
        # Lookup practice number from professions table
        prof_cur = conn.execute("""
            SELECT practice_number FROM professions WHERE profession_name = ?
        """, (provider_profession,))
        prof_row = prof_cur.fetchone()
        practice_number = prof_row[0] if prof_row and prof_row[0] else ""
        # fetch billing entries along with code and description, matching either by id or code string
        entry_rows = conn.execute(
            """
            SELECT
              be.code_id,
              COALESCE(bc.code, CAST(be.code_id AS TEXT)) AS code,
              COALESCE(bc.description, '') AS description,
              be.billing_modifier,
              be.final_fee
            FROM billing_entries be
            LEFT JOIN billing_codes bc
              ON be.code_id = bc.id
              OR CAST(be.code_id AS TEXT) = bc.code
            WHERE be.appointment_id = ?
            """,
            (appointment_id,)
        ).fetchall()
        logging.info(f"👉 Entry rows for invoice {appointment_id}: {entry_rows}")
        entries = []
        for code_id, code_str, desc_str, modifier, fee in entry_rows:
            entries.append((code_id, code_str or "", desc_str or "", modifier or "", fee or 0))
    # Create PDF in memory
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setTitle(f"{provider_profession} Invoice - {invoice_id}")
    # Set up fonts and margins
    pdf.setFont("Helvetica-Bold", 16)
    left_margin = 50
    right_margin = 550
    line_height = 24
    y_start = 800
    y = y_start
    # Colored header background
    pdf.setFillColorRGB(45/255, 99/255, 86/255)  # Brand accent color
    pdf.rect(left_margin, y - (line_height * 0.3), right_margin - left_margin, line_height * 1.5, fill=True, stroke=False)
    # White text for header
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 16)
    # Draw header
    pdf.drawString(left_margin, y, f"{provider_profession} Invoice - {invoice_id}")
    y -= line_height * 2
    # Reset to default text color and font
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 12)
    # Two-column patient and service details
    mid_x = (left_margin + right_margin) / 2
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left_margin, y, "Patient Details:")
    pdf.drawString(mid_x, y, "Therapist Details:")
    y -= line_height
    pdf.setFont("Helvetica", 12)
    # Patient column (left)
    pdf.drawString(left_margin, y, f"Patient: {patient_name_full}")
    pdf.drawString(left_margin, y - line_height, f"Patient ID: {patient_table_id}")
    pdf.drawString(left_margin, y - line_height * 2, f"Medical Aid: {med_aid}")
    pdf.drawString(left_margin, y - line_height * 3, f"Plan: {plan}")
    pdf.drawString(left_margin, y - line_height * 4, f"Dependent No.: {dependent_no}")
    pdf.drawString(left_margin, y - line_height * 5, f"Main Member: {principal_member}")
    # Therapist column (right)
    pdf.drawString(mid_x, y, f"Name: {provider_name}")
    pdf.drawString(mid_x, y - line_height, f"Profession: {provider_profession}")
    pdf.drawString(mid_x, y - line_height * 2, f"Practice No.: {practice_number}")
    pdf.drawString(mid_x, y - line_height * 3, f"Date of Service: {invoice_date[:10]}")
    y -= line_height * 6
    y -= line_height * 1.5
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left_margin, y, "Line Items:")
    y -= line_height
    # Table header
    pdf.setFillColorRGB(45/255, 99/255, 86/255)
    pdf.rect(left_margin, y - line_height, right_margin - left_margin, line_height, fill=True, stroke=False)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left_margin + 5, y - line_height + 4, "Code")
    pdf.drawString(left_margin + 60, y - line_height + 4, "Description")
    pdf.drawString(left_margin + 260, y - line_height + 4, "ICD-10")
    pdf.drawString(left_margin + 360, y - line_height + 4, "Qty")
    pdf.drawString(left_margin + 420, y - line_height + 4, "Modifier")
    pdf.drawRightString(right_margin - 5, y - line_height + 4, "Fee")
    # After drawing table header, reset to black for entries
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 12)
    y -= line_height * 1.5
    # Render each entry with wrapped text for desc and icd
    for idx, (code_id, code, desc, modifier, fee) in enumerate(entries):
        qty = 1
        icd = patient_icd10_codes.split(",")[0] if patient_icd10_codes else ""
        # Define column widths in characters (approximation)
        desc_col_width = 35  # fits in Description column
        icd_col_width = 18   # fits in ICD-10 column
        # Wrap description and icd
        desc_lines = textwrap.wrap(desc, width=desc_col_width) or [""]
        icd_lines = textwrap.wrap(icd, width=icd_col_width) or [""]
        max_lines = max(len(desc_lines), len(icd_lines))
        # Draw first line with all columns
        pdf.drawString(left_margin + 5, y, code)
        pdf.drawString(left_margin + 60, y, desc_lines[0] if desc_lines else "")
        pdf.drawString(left_margin + 260, y, icd_lines[0] if icd_lines else "")
        pdf.drawString(left_margin + 360, y, str(qty))
        pdf.drawString(left_margin + 420, y, modifier or "")
        pdf.drawRightString(right_margin - 5, y, f"R{fee:.2f}")
        # Draw additional wrapped lines (for desc/icd)
        for i in range(1, max_lines):
            y -= line_height
            pdf.drawString(left_margin + 60, y, desc_lines[i] if i < len(desc_lines) else "")
            pdf.drawString(left_margin + 260, y, icd_lines[i] if i < len(icd_lines) else "")
        # Calculate total height for this row
        row_height = max_lines * line_height
        y -= line_height  # After last line, extra spacing for row separation
        y -= 6
        # Table grid line if not last entry or at page break
        if (idx < len(entries) - 1 and y > 100) or (y <= 100):
            pdf.line(left_margin, y + line_height - 2 + 6, right_margin, y + line_height - 2 + 6)
        if y < 100 and idx < len(entries) - 1:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = y_start
    # Reset fill color to black in case changed
    pdf.setFillColorRGB(0, 0, 0)
    # Determine X position for totals block on right
    totals_block_x = right_margin - 200
    # Totals block: total, paid, and due each on its own line
    y -= line_height // 2
    pdf.setFont("Helvetica-Bold", 12)
    # Total
    pdf.drawString(totals_block_x, y, "Total:")
    pdf.drawRightString(right_margin - 5, y, f"R{total_amount:.2f}")
    # Amount Paid
    y -= line_height
    pdf.setFont("Helvetica", 12)
    amount_paid = total_amount if str(status).lower() == 'paid' else 0
    pdf.drawString(totals_block_x, y, "Amount Paid:")
    pdf.drawRightString(right_margin - 5, y, f"R{amount_paid:.2f}")
    # Amount Due
    y -= line_height
    amount_due = total_amount - amount_paid
    pdf.drawString(totals_block_x, y, "Amount Due:")
    pdf.drawRightString(right_margin - 5, y, f"R{amount_due:.2f}")
    # Finish PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={invoice_id}.pdf"}
    )
# Users table setup
def init_users_table():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT,
                linked_therapist_id INTEGER,
                permissions TEXT
            );
        """)

# DELETE therapist
@app.delete("/delete-therapist/{therapist_id}")
def delete_therapist_endpoint(therapist_id: int):
    """Delete therapist using the therapists module"""
    success = delete_therapist(therapist_id)
    if success:
        return {"detail": "Therapist deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete therapist")

# --- USER MANAGEMENT ENDPOINTS (Admin-only) ---

# List all users (Admin-only)
@app.get("/users")
def list_users_endpoint(request: Request):
    """Get all users using the auth module"""
    return get_all_users(request)

# Update a user (Admin-only)
@app.put("/users/{user_id}")
def update_user_endpoint(user_id: int, user_data: dict = Body(...), request: Request = None):
    """Update user using the auth module"""
    return update_user(user_id, user_data, request)

# Delete a user (Admin-only)
@app.delete("/users/{user_id}")
def delete_user_endpoint(user_id: int, request: Request):
    """Delete user using the auth module"""
    return delete_user(user_id, request)

# --- USER SIGNUP (Admin-only in future) ---
@app.post("/signup")
def signup_endpoint(
    username: str = Body(...),
    password: str = Body(...),
    role: str = Body(...),
    permissions: List[str] = Body(default=[])
):
    """User signup using the auth module"""
    user_data = {
        'username': username,
        'password': password,
        'role': role,
        'permissions': permissions
    }
    return signup_user(user_data)

# --- CREATE USER ENDPOINT (Admin-only) ---
@app.post("/create-user")
def create_user_endpoint(
    username: str = Body(...),
    password: str = Body(...),
    role: str = Body(...),
    permissions: List[str] = Body(default=[]),
    linked_therapist_id: int = Body(default=None)
):
    """Create user using the auth module"""
    user_data = {
        'username': username,
        'password': password,
        'role': role,
        'permissions': permissions,
        'linked_therapist_id': linked_therapist_id
    }
    return create_user(user_data)

# --- USER LOGIN ---
@app.post("/login")
def login_endpoint(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    """Login using the auth module"""
    return login_user(request, credentials)

# API endpoint to update an existing therapist's data
@app.put("/update-therapist/{therapist_id}")
def update_therapist_endpoint(therapist_id: int, therapist_data: dict = Body(...)):
    """Update therapist using the therapists module"""
    success = update_therapist(therapist_id, therapist_data)
    if success:
        return {"detail": "Therapist updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update therapist")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; update to restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the AI summary router
app.include_router(router)

# ContactRequest Pydantic model for /contact endpoint
class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    phone_e164: Optional[str] = None
    org: Optional[str] = None
    message: Optional[str] = None

@app.post("/contact")
async def contact_send(data: ContactRequest):
    """
    Send contact emails via Resend (preferred), SMTP (optional), or console fallback.
    Priority:
      1) If RESEND_API_KEY is set and EMAIL_MODE in {auto,resend} -> Resend API
      2) Else if EMAIL_MODE == smtp and SMTP vars are present -> SMTP
      3) Else -> Console log (demo mode)
    """
    mode = os.getenv("EMAIL_MODE", "auto").lower()  # auto|resend|smtp|console

    # Common fields
    to_addr = os.getenv("SMTP_TO", "duncan@hadadahealth.com")
    subject = f"HadadaHealth enquiry from {data.name}"
    body = (
        f"Name: {data.name}\n"
        f"Email: {data.email}\n"
        f"Phone: {data.phone or ''}\n"
        f"Phone (E.164): {data.phone_e164 or ''}\n"
        f"Organisation: {data.org or ''}\n\n"
        f"Message:\n{data.message or ''}\n"
    )

    # 1) Resend API path (default when RESEND_API_KEY is present)
    resend_key = os.getenv("RESEND_API_KEY")
    resend_from = os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM") or "onboarding@resend.dev"
    if resend_key and mode in {"auto", "resend"}:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                    json={
                        "from": resend_from,
                        "to": [to_addr],
                        "subject": subject,
                        "text": body,
                    },
                )
            if r.status_code >= 400:
                # Log and continue to console fallback
                logging.error("Resend API error %s: %s", r.status_code, r.text)
                raise HTTPException(status_code=500, detail=f"Resend error: {r.text}")
            return {"ok": True, "mode": "resend"}
        except Exception as e:
            logging.exception("Resend send failed")
            # Fall through to console success so UI doesn't break during demos
            return {"ok": True, "mode": "console", "note": f"Resend failed: {e}"}

    # 2) SMTP path (only if explicitly selected)
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")
    from_addr = os.getenv("SMTP_FROM", user or "noreply@hadadahealth.com")
    if mode == "smtp" and host and user and pwd:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg.set_content(body)
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port) as server:
                server.starttls(context=context)
                server.login(user, pwd)
                server.send_message(msg)
            return {"ok": True, "mode": "smtp"}
        except Exception as e:
            logging.exception("SMTP send failed")
            return {"ok": True, "mode": "console", "note": f"SMTP failed: {e}"}

    # 3) Console fallback (demo mode)
    logging.info("📬 [Console Email] To: %s\nSubject: %s\n\n%s", to_addr, subject, body)
    return {"ok": True, "mode": "console"}
# Database setup
def init_db():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                therapist TEXT NOT NULL,
                date TEXT NOT NULL,
                day TEXT NOT NULL,
                time TEXT NOT NULL,
                duration INTEGER NOT NULL,
                notes TEXT,
                colour TEXT,
                profession TEXT,
                user_id INTEGER,
                patient_id INTEGER
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS supplementary_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (appointment_id) REFERENCES bookings(id)
            );
        """)

from datetime import datetime

@app.post("/api/treatment-notes/{appointment_id}/supplementary_note")
def add_supplementary_note_endpoint(appointment_id: str, data: dict, request: Request):
    """Add supplementary note using the treatment_notes module"""
    return add_supplementary_note(appointment_id, data, request)

# --- Outcome Measure Types endpoint (dropdown source, subscores only) ---
@app.get("/api/outcome-measure-types")
def get_outcome_measure_types_from_subscores():
    conn = get_db_connection()
    outcome_types = conn.execute("""
        SELECT DISTINCT outcome_measure_type_id, subcategory_name
        FROM outcome_measure_type_subscores
    """).fetchall()
    conn.close()
    return [
        {
            "id": row["outcome_measure_type_id"],
            "name": row["subcategory_name"]
        }
        for row in outcome_types
    ]

def init_patients_table():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                surname TEXT,
                preferred_name TEXT,
                date_of_birth TEXT,
                gender TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                town TEXT,
                postal_code TEXT,
                country TEXT,
                email TEXT,
                contact_number TEXT,
                clinic TEXT,
                account_name TEXT,
                account_id_number TEXT,
                account_address TEXT,
                account_phone TEXT,
                account_email TEXT,
                funding_option TEXT,
                main_member_name TEXT,
                medical_aid_name TEXT,
                medical_aid_other TEXT,
                plan_name TEXT,
                medical_aid_number TEXT,
                dependent_number TEXT,
                alternative_funding_source TEXT,
                alternative_funding_other TEXT,
                claim_number TEXT,
                case_manager TEXT,
                patient_important_info TEXT,
                consent_treatment TEXT,
                consent_photography TEXT,
                consent_data TEXT,
                consent_communication TEXT,
                consent_billing TEXT,
                consent_terms TEXT,
                signature_identity TEXT,
                signature_name TEXT,
                signature_relationship TEXT,
                signature_data TEXT
            );
        """)
        # Ensure icd10_codes column exists
        try:
            conn.execute("ALTER TABLE patients ADD COLUMN icd10_codes TEXT;")
        except sqlite3.OperationalError:
            # Column already exists
            pass

# Medical aids table setup
def init_medical_aids_table():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS medical_aids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                website TEXT,
                claims_email TEXT,
                plans TEXT,
                claim_tips TEXT,
                administrator TEXT
            );
        """)

# Populate medical aids table with a comprehensive list
def populate_medical_aids():
    aids = [
        "AECI Medical Aid Society", "Alliance-Midmed Medical Scheme", "Anglo Medical Scheme",
        "Anglovaal Group Medical Scheme", "Bankmed", "Barloworld Medical Scheme",
        "Bestmed Medical Scheme", "BMW Employees Medical Aid Society", "Bonitas Medical Fund",
        "BP Medical Aid Society", "Building & Construction Industry Medical Aid Fund",
        "Cape Medical Plan", "CAMAF", "Compcare Medical Scheme", "Consumer Goods Medical Scheme",
        "De Beers Benefit Society", "Discovery Health Medical Scheme", "Engen Medical Benefit Fund",
        "Fedhealth Medical Scheme", "Fishing Industry Medical Scheme (Fishmed)", "Foodmed Medical Scheme",
        "Genesis Medical Scheme", "Glencore Medical Scheme", "Golden Arrow Employees' Medical Benefit Fund",
        "GEMS", "Health Squared Medical Scheme", "Horizon Medical Scheme", "Impala Medical Plan",
        "Imperial and Motus Medical Aid", "KeyHealth", "LA-Health Medical Scheme", "Libcare Medical Scheme",
        "Lonmin Medical Scheme", "Makoti Medical Scheme", "Malcor Medical Scheme", "Massmart Health Plan",
        "MBMed Medical Aid Fund", "Medihelp", "Medimed Medical Scheme", "Medipos Medical Scheme",
        "Medshield Medical Scheme", "Momentum Medical Scheme", "Motohealth Care",
        "Multichoice Medical Aid Scheme", "Netcare Medical Scheme", "Old Mutual Staff Medical Aid Fund",
        "Parmed Medical Aid Scheme", "PG Group Medical Scheme", "Pick n Pay Medical Scheme",
        "Platinum Health", "Profmed", "Rand Water Medical Scheme", "Remedi Medical Aid Scheme",
        "Retail Medical Scheme", "Rhodes University Medical Scheme", "SABC Medical Aid Scheme", "SAMWUMED",
        "Sasolmed", "SEDMED", "Sisonke Health Medical Scheme", "Sizwe Hosmed Medical Scheme", "SABMAS",
        "Polmed", "Suremed Health", "TFG Medical Aid Scheme", "Thebemed", "Transmed Medical Fund",
        "Tsogo Sun Group Medical Scheme", "Umvuzo Health Medical Scheme", "University of Kwa-Zulu Natal Medical Scheme",
        "Witbank Coalfields Medical Aid Scheme", "Wooltru Healthcare Fund"
    ]
    with sqlite3.connect("data/bookings.db") as conn:
        for name in aids:
            try:
                conn.execute("INSERT INTO medical_aids (name) VALUES (?)", (name,))
            except sqlite3.IntegrityError:
                continue  # Skip duplicates


# Therapist table setup
def init_therapists_table():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS therapists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                surname TEXT,
                preferred_name TEXT,
                profession TEXT,
                cellphone TEXT,
                clinic TEXT,
                email TEXT,
                hpcsa_number TEXT,
                malpractice_number TEXT,
                malpractice_expiry TEXT,
                hpcsa_expiry TEXT,
                date_of_birth TEXT,
                permissions TEXT
            );
        """)

def init_settings_table():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                slot_duration INTEGER,
                weekdays TEXT,
                dark_mode BOOLEAN
            );
        """)
        # Ensure one default settings row exists
        conn.execute(
            "INSERT OR IGNORE INTO settings (id, start_time, end_time, slot_duration, weekdays, dark_mode) VALUES (1, '09:00', '15:00', 15, 'Mon,Tue,Wed,Thu,Fri', 0)"
        )


# Professions table setup
def init_professions_table():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS professions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profession_name TEXT,
                practice_name TEXT,
                practice_owner TEXT,
                practice_number TEXT,
                practice_email TEXT,
                clinics TEXT
            );
        """)

# Clinics table setup
def init_clinics_table():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clinics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clinic_name TEXT,
                address TEXT,
                email TEXT,
                phone TEXT
            );
        """)

# Billing tables setup
def init_billing_tables():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                description TEXT,
                base_fee REAL NOT NULL,
                profession TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_sessions (
                id TEXT PRIMARY KEY,
                patient_id INTEGER NOT NULL,
                therapist_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                notes TEXT,
                total_amount REAL,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (therapist_id) REFERENCES therapists(id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_entries (
                id TEXT PRIMARY KEY,
                appointment_id TEXT NOT NULL,
                code_id INTEGER NOT NULL,
                billing_modifier TEXT,
                final_fee REAL,
                FOREIGN KEY (appointment_id) REFERENCES billing_sessions(id),
                FOREIGN KEY (code_id) REFERENCES billing_codes(id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_modifiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modifier_code TEXT NOT NULL,
                modifier_name TEXT,
                modifier_description TEXT,
                modifier_effect TEXT,
                modifier_multiplier REAL NOT NULL,
                profession TEXT NOT NULL
            );
        """)

init_db()
init_patients_table()
init_medical_aids_table()
populate_medical_aids()
init_therapists_table()
init_settings_table()
init_professions_table()
init_clinics_table()
init_users_table()
init_billing_tables()

# Booking model is now imported from modules.appointments

# Patient model
class Patient(BaseModel):
    first_name: str
    surname: str
    preferred_name: str
    date_of_birth: str
    gender: str
    id_number: str
    address_line1: str
    address_line2: Optional[str] = None
    town: str
    postal_code: str
    country: str
    email: str
    contact_number: str
    clinic: Optional[str] = None
    account_name: Optional[str] = None
    account_id_number: Optional[str] = None
    account_address: Optional[str] = None
    account_phone: Optional[str] = None
    account_email: Optional[str] = None
    funding_option: Optional[str] = None
    main_member_name: Optional[str] = None
    medical_aid_name: Optional[str] = None
    medical_aid_other: Optional[str] = None
    plan_name: Optional[str] = None
    medical_aid_number: Optional[str] = None
    dependent_number: Optional[str] = None
    alternative_funding_source: Optional[str] = None
    alternative_funding_other: Optional[str] = None
    claim_number: Optional[str] = None
    case_manager: Optional[str] = None
    patient_important_info: Optional[str] = None
    consent_treatment: Optional[str] = None
    consent_photography: Optional[str] = None
    consent_data: Optional[str] = None
    consent_communication: Optional[str] = None
    consent_billing: Optional[str] = None
    consent_terms: Optional[str] = None
    signature_identity: Optional[str] = None
    signature_name: Optional[str] = None
    signature_relationship: Optional[str] = None
    signature_data: Optional[str] = None

# Therapist model
# Therapist model is now imported from modules.therapists

# Settings model
class Settings(BaseModel):
    start_time: str
    end_time: str
    slot_duration: int
    weekdays: List[str]
    dark_mode: bool

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    phone_e164: Optional[str] = None
    org: Optional[str] = None
    message: Optional[str] = None

from typing import Optional
@app.get("/bookings")  # Removed response_model since we return dicts now
def get_bookings_endpoint(request: Request, therapist_id: Optional[int] = None, start: str = Query(None), end: str = Query(None)):
    """Get bookings using the appointments module"""
    return get_bookings(request, therapist_id, start, end)

@app.get("/bookings/{booking_id}")
def get_booking_endpoint(booking_id: int):
    """Get single booking using the appointments module"""
    return get_booking_by_id(booking_id)
# Session info endpoint for frontend to get user/role/therapist
@app.get("/session-info")
def session_info(request: Request):
    return {
        "user_id": request.session.get("user_id"),
        "username": request.session.get("username"),
        "role": request.session.get("role"),
        "linked_therapist_id": request.session.get("linked_therapist_id")
    }

# POST new booking for the logged-in user
@app.post("/bookings", response_model=Booking)
def add_booking(booking: Booking, request: Request):
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    therapist_id = booking.therapist or request.session.get('linked_therapist_id')
    if not therapist_id:
        raise HTTPException(status_code=400, detail="Therapist ID is required")

    with sqlite3.connect("data/bookings.db") as conn:
        try:
            conn.execute("""
                INSERT INTO bookings (id, name, therapist, date, day, time, duration, notes, colour, user_id, profession, patient_id)
                VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking.id,
                booking.name,
                str(therapist_id),
                booking.date[:10],
                booking.day,
                booking.time,
                booking.duration,
                booking.notes,
                booking.colour,
                user_id,
                booking.profession,
                booking.patient_id
            ))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Booking ID already exists")
    return booking


# PUT update booking
@app.put("/bookings/{booking_id}", response_model=Booking)
def update_booking(booking_id: str, booking: Booking, request: Request):
    therapist_id = booking.therapist or request.session.get('linked_therapist_id')
    if not therapist_id:
        raise HTTPException(status_code=400, detail="Therapist ID is required")

    with sqlite3.connect("data/bookings.db") as conn:
        if not conn.execute("SELECT 1 FROM bookings WHERE id = ?", (booking_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Booking not found")
        conn.execute("""
            UPDATE bookings SET name=?, therapist=?, date=?, day=?, time=?, duration=?, notes=?, colour=?, profession=?, patient_id=?
            WHERE id=?
        """, (
            booking.name,
            str(therapist_id),
            booking.date[:10],
            booking.day,
            booking.time,
            booking.duration,
            booking.notes,
            booking.colour,
            booking.profession,
            booking.patient_id,
            booking_id
        ))
    return booking

# --- New endpoint: Mark billing complete and auto-create draft invoice ---
@app.post("/complete-billing/{booking_id}")
def complete_billing(booking_id: str, request: Request):
    # ensure authenticated
    if not request.session.get('user_id'):
        raise HTTPException(status_code=401, detail="Not authenticated")
    with sqlite3.connect("data/bookings.db") as conn:
        # mark booking as billed
        conn.execute("UPDATE bookings SET billing_completed = 1 WHERE id = ?", (booking_id,))
        # only insert a draft if one doesn't exist
        exists = conn.execute(
            "SELECT 1 FROM billing_sessions WHERE id = ?", (booking_id,)
        ).fetchone()
        if not exists:
            # create minimal draft invoice
            conn.execute("""
                INSERT INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
                SELECT id, patient_id, therapist, date || 'T' || time || ':00', '', 0
                FROM bookings WHERE id = ?
            """, (booking_id,))
            # Also create a corresponding invoice record if not exists
            invoice_exists = conn.execute(
                "SELECT 1 FROM invoices WHERE appointment_id = ?", (booking_id,)
            ).fetchone()
            if not invoice_exists:
                conn.execute("""
                    INSERT INTO invoices (
                        id,
                        appointment_id,
                        patient_id,
                        therapist_id,
                        invoice_date,
                        due_date,
                        status,
                        notes,
                        total_amount
                    ) SELECT
                        'INV' || substr(id,5),
                        id,
                        patient_id,
                        therapist,
                        date || 'T' || time || ':00',
                        NULL,
                        'Draft',
                        '',
                        0
                    FROM bookings
                    WHERE id = ?
                """, (booking_id,))
    return {"detail": "Booking marked billed and draft invoice created"}

# DELETE booking
@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    print(f"🧹 DELETE called for booking ID: {booking_id}")  # Debug log
    with sqlite3.connect("data/bookings.db") as conn:
        exists = conn.execute("SELECT 1 FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        print(f"🔎 Booking exists? {bool(exists)}")  # Debug log
        if not exists:
            print("⚠️ Booking not found in DB")  # Debug log
            raise HTTPException(status_code=404, detail="Booking not found")
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        print("✅ Booking deleted successfully")  # Debug log
    return {"detail": "Booking deleted"}

# POST save patient (with therapist_id support)
@app.post("/patients")
def save_patient(patient: Patient, request: Request):
    therapist_id = request.session.get("linked_therapist_id")
    if hasattr(patient, "therapist_id") and getattr(patient, "therapist_id", None):
        therapist_id = getattr(patient, "therapist_id")

    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            INSERT INTO patients (
                first_name, surname, preferred_name, date_of_birth, gender, id_number,
                address_line1, address_line2, town, postal_code, country,
                email, contact_number, clinic,
                account_name, account_id_number, account_address, account_phone, account_email,
                funding_option, main_member_name, medical_aid_name, medical_aid_other, plan_name,
                medical_aid_number, dependent_number, alternative_funding_source, alternative_funding_other,
                claim_number, case_manager, patient_important_info,
                consent_treatment, consent_photography, consent_data, consent_communication,
                consent_billing, consent_terms,
                signature_identity, signature_name, signature_relationship, signature_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient.first_name,
            patient.surname,
            patient.preferred_name,
            patient.date_of_birth,
            patient.gender,
            patient.id_number,
            patient.address_line1,
            patient.address_line2,
            patient.town,
            patient.postal_code,
            patient.country,
            patient.email,
            patient.contact_number,
            patient.clinic,
            patient.account_name,
            patient.account_id_number,
            patient.account_address,
            patient.account_phone,
            patient.account_email,
            patient.funding_option,
            patient.main_member_name,
            patient.medical_aid_name,
            patient.medical_aid_other,
            patient.plan_name,
            patient.medical_aid_number,
            patient.dependent_number,
            patient.alternative_funding_source,
            patient.alternative_funding_other,
            patient.claim_number,
            patient.case_manager,
            patient.patient_important_info,
            patient.consent_treatment,
            patient.consent_photography,
            patient.consent_data,
            patient.consent_communication,
            patient.consent_billing,
            patient.consent_terms,
            patient.signature_identity,
            patient.signature_name,
            patient.signature_relationship,
            patient.signature_data
        ))
    return {"detail": "Patient saved"}

from typing import Dict

# Update patient endpoint (PUT)
@app.put("/update-patient/{patient_id}")
def update_patient(patient_id: int, patient_data: dict = Body(...)):
    # Dynamically build the SQL update statement
    fields = []
    values = []
    for key, value in patient_data.items():
        # Support updating icd10_codes (and any other field)
        fields.append(f"{key} = ?")
        values.append(value)
    values.append(patient_id)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    with sqlite3.connect("data/bookings.db") as conn:
        # Ensure icd10_codes column exists
        try:
            conn.execute("ALTER TABLE patients ADD COLUMN icd10_codes TEXT;")
        except sqlite3.OperationalError:
            pass
        cur = conn.execute(f"UPDATE patients SET {', '.join(fields)} WHERE id = ?", values)
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
    return {"detail": "Patient updated successfully"}

# --- GET all patients, including icd10_codes ---
# --- GET all patients, including icd10_codes ---
@app.get("/patients")
def get_patients():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT * FROM patients")
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


# --- New endpoint: Get medical history summary and generated date for a patient ---
@app.get("/api/patient/{patient_id}/medical-history")
def get_medical_history(patient_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT medical_history_ai, medical_history_ai_generated
        FROM patients
        WHERE id = ?
    """, (patient_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "summary": row["medical_history_ai"],
            "generated_at": row["medical_history_ai_generated"]
        }
    else:
        return {"summary": "", "generated_at": ""}

# --- New endpoint: Regenerate AI medical history summary for a patient ---
@app.post("/api/patient/{patient_id}/medical-history/regenerate")
async def regenerate_medical_history(patient_id: str):
    summary = await generate_ai_medical_history(patient_id)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE patients
        SET medical_history_ai = ?, medical_history_ai_generated = ?
        WHERE id = ?
    """, (summary, now, patient_id))
    conn.commit()
    conn.close()

    return {"success": True, "summary": summary, "generated_at": now}

# MedicalAid model for create/update endpoints
# Medical Aid model is now imported from modules.medical_aids

# GET all medical aid names
@app.get("/medical_aids", response_model=List[str])
def get_medical_aids_endpoint():
    """Get all medical aid names using the medical aids module"""
    return get_all_medical_aids()

# GET all medical aid full records
@app.get("/medical_aids_full")
def get_medical_aids_full_endpoint():
    """Get all medical aids with full details using the medical aids module"""
    return get_all_medical_aids_full()

# POST new medical aid
@app.post("/medical_aids", status_code=201)
def add_medical_aid_endpoint(aid: MedicalAid):
    """Create medical aid using the medical aids module"""
    return create_medical_aid(aid)

# PUT update medical aid name
@app.put("/medical_aids/{old_name}")
def update_medical_aid_endpoint(old_name: str, aid: MedicalAid):
    """Update medical aid using the medical aids module"""
    return update_medical_aid(old_name, aid)

# DELETE medical aid
@app.delete("/medical_aids/{name}")
def delete_medical_aid_endpoint(name: str):
    """Delete medical aid using the medical aids module"""
    return delete_medical_aid(name)

# GET plans for a specific medical aid
@app.get("/medical_aid_plans/{medical_aid_name}", response_model=List[str])
def get_plans_for_medical_aid_endpoint(medical_aid_name: str):
    """Get medical aid plans using the medical aids module"""
    return get_medical_aid_plans(medical_aid_name)

# Bulk import medical aids from Excel
@app.post("/import-medical-aids")
def import_medical_aids_endpoint(file: UploadFile = File(...)):
    """Import medical aids from Excel using the medical aids module"""
    return import_medical_aids_from_excel(file)



# Bulk import patients from Excel
@app.post("/import-patients")
def import_patients(file: UploadFile = File(...)):
    try:
        df = pd.read_excel(file.file)
        with sqlite3.connect("data/bookings.db") as conn:
            for _, row in df.iterrows():
                values = (
                    row.get('first_name', ''),
                    row.get('surname', ''),
                    row.get('preferred_name', ''),
                    row.get('date_of_birth', ''),
                    row.get('gender', ''),
                    row.get('id_number', ''),
                    row.get('address_line1', ''),
                    row.get('address_line2', ''),
                    row.get('town', ''),
                    row.get('postal_code', ''),
                    row.get('country', ''),
                    row.get('email', ''),
                    row.get('contact_number', ''),
                    row.get('clinic', ''),
                    row.get('account_name', ''),
                    row.get('account_id_number', ''),
                    row.get('account_address', ''),
                    row.get('account_phone', ''),
                    row.get('account_email', ''),
                    row.get('funding_option', ''),
                    row.get('main_member_name', ''),
                    row.get('medical_aid_name', ''),
                    row.get('medical_aid_other', ''),
                    row.get('plan_name', ''),
                    row.get('medical_aid_number', ''),
                    row.get('dependent_number', ''),
                    row.get('alternative_funding_source', ''),
                    row.get('alternative_funding_other', ''),
                    row.get('claim_number', ''),
                    row.get('case_manager', ''),
                    row.get('patient_important_info', ''),
                    row.get('consent_treatment', ''),
                    row.get('consent_photography', ''),
                    row.get('consent_data', ''),
                    row.get('consent_communication', ''),
                    row.get('consent_billing', ''),
                    row.get('consent_terms', ''),
                    row.get('signature_identity', ''),
                    row.get('signature_name', ''),
                    row.get('signature_relationship', ''),
                    row.get('signature_data', ''),
                )
                conn.execute("""
                    INSERT INTO patients (
                        first_name, surname, preferred_name, date_of_birth, gender, id_number,
                        address_line1, address_line2, town, postal_code, country,
                        email, contact_number, clinic,
                        account_name, account_id_number, account_address, account_phone, account_email,
                        funding_option, main_member_name, medical_aid_name, medical_aid_other, plan_name,
                        medical_aid_number, dependent_number, alternative_funding_source, alternative_funding_other,
                        claim_number, case_manager, patient_important_info,
                        consent_treatment, consent_photography, consent_data, consent_communication,
                        consent_billing, consent_terms,
                        signature_identity, signature_name, signature_relationship, signature_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, values)
        return {"detail": "Patients imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# Bulk import therapists from Excel
@app.post("/import-therapists")
def import_therapists_endpoint(file: UploadFile = File(...)):
    """Import therapists from Excel using the therapists module"""
    return import_therapists_from_excel(file)

# GET all therapists
@app.get("/therapists")
def get_therapists_endpoint():
    """Get all therapists using the therapists module"""
    return get_all_therapists()

# GET a single therapist by ID
@app.get("/therapist/{therapist_id}")
def get_therapist_endpoint(therapist_id: int):
    """Get therapist by ID using the therapists module"""
    therapist = get_therapist_basic_info(therapist_id)
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    return therapist


# POST save therapist and create linked user
@app.post("/save-therapist")
def save_therapist_endpoint(therapist: Therapist):
    """Create therapist and linked user using the therapists module"""
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()
        
        # Create therapist using module function
        therapist_id = create_therapist(therapist)

        # Automatically create linked user with unique username
        password = bcrypt.hashpw("welcome123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        base_username = (therapist.preferred_name or therapist.name) + therapist.surname
        username = base_username.lower().replace(" ", "")
        original_username = username
        counter = 1
        # Ensure username is unique
        while cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            username = f"{original_username}{counter}"
            counter += 1
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, linked_therapist_id, permissions)
            VALUES (?, ?, ?, ?, ?)
        """, (
            username,
            password,
            "Clinician",
            therapist_id,
            json.dumps(["calendar", "patients", "notes"])
        ))
        conn.commit()
    return {"detail": "Therapist and linked user created successfully"}


from starlette.requests import Request

# Serve HTML pages from templates directory, requiring login for sensitive pages
@app.get("/")
def serve_index(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "index.html"))

@app.get("/add-patient-page")
def serve_add_patient_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "add-patient.html"))

@app.get("/therapists-page")
def serve_therapists_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "therapists.html"))

@app.get("/week-calendar-page")
def serve_week_calendar_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "week-calendar.html"))


# New: Serve Patient Profile page, requiring login and accepting patient id as query parameter
@app.get("/patient-profile-page")
def serve_patient_profile_page(request: Request, id: int = Query(...)):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "Patient Profile.html"))

@app.get("/medical-aid-page")
def serve_medical_aid_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "Medical Aid.html"))

# @app.get("/billing-page")
@app.get("/billing-page")
def serve_billing_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "billing.html"))

@app.get("/treatment-notes-page")
def serve_treatment_notes_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "treatment-notes.html"))

@app.get("/patient-dash-page")
def serve_patient_dash(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "Patient Dash.html"))

@app.get("/test-calendar-page")
def serve_test_calendar(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "Test Calendar.html"))

@app.get("/patients-page")
def serve_patients_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "patients.html"))

# Serve the settings page
@app.get("/settings-page")
def serve_settings_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "settings.html"))

# Serve the manage users page
@app.get("/manage-users-page")
def serve_manage_users_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "manage-users.html"))

# Settings API endpoints
@app.get("/settings", response_model=Settings)
def get_settings():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT start_time, end_time, slot_duration, weekdays, dark_mode FROM settings WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return {
                "start_time": row[0],
                "end_time": row[1],
                "slot_duration": row[2],
                "weekdays": row[3].split(","),
                "dark_mode": bool(row[4])
            }
        raise HTTPException(status_code=404, detail="Settings not found")

@app.post("/settings")
def update_settings(settings: Settings = Body(...)):
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            UPDATE settings
            SET start_time = ?, end_time = ?, slot_duration = ?, weekdays = ?, dark_mode = ?
            WHERE id = 1
        """, (
            settings.start_time,
            settings.end_time,
            settings.slot_duration,
            ",".join(settings.weekdays),
            int(settings.dark_mode)
        ))
    return {"detail": "Settings updated"}

@app.get("/patients")
def get_patients():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT 
                id, first_name, surname, preferred_name, gender, date_of_birth, id_number,
                address_line1, address_line2, town, postal_code, country,
                email, contact_number, clinic,
                account_name, account_id_number, account_address, account_phone, account_email,
                funding_option, main_member_name, medical_aid_name, plan_name,
                alternative_funding_source, claim_number, case_manager, patient_important_info,
                consent_treatment, consent_photography, consent_data, consent_communication,
                consent_billing, consent_terms,
                signature_identity, signature_name, signature_relationship,
                signature_data
            FROM patients
        """)
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "first_name": row[1],
                "surname": row[2],
                "preferred_name": row[3],
                "gender": row[4],
                "date_of_birth": row[5],
                "id_number": row[6],
                "address_line1": row[7],
                "address_line2": row[8],
                "town": row[9],
                "postal_code": row[10],
                "country": row[11],
                "email": row[12],
                "contact_number": row[13],
                "clinic": row[14], 
                "account_name": row[15],
                "account_id_number": row[16],
                "account_address": row[17],
                "account_phone": row[18],
                "account_email": row[19],
                "funding_option": row[20],
                "main_member_name": row[21],
                "medical_aid_name": row[22],
                "plan_name": row[23],
                "alternative_funding_source": row[24],
                "claim_number": row[25],
                "case_manager": row[26],
                "patient_important_info": row[27],
                "consent_treatment": row[28],
                "consent_photography": row[29],
                "consent_data": row[30],
                "consent_communication": row[31],
                "consent_billing": row[32],
                "consent_terms": row[33],
                "signature_identity": row[34],
                "signature_name": row[35],
                "signature_relationship": row[36],
                "signature_data": row[37],
            }
            for row in rows
        ]

# API endpoint to update an existing patient's data
@app.put("/update-patient/{patient_id}")
def update_patient(patient_id: int, patient_data: dict = Body(...)):
    with sqlite3.connect("data/bookings.db") as conn:
        columns = ", ".join([f"{key} = ?" for key in patient_data.keys()])
        values = list(patient_data.values())
        values.append(patient_id)
        conn.execute(f"UPDATE patients SET {columns} WHERE id = ?", values)
    return {"detail": "Patient updated successfully"}

# API endpoint to delete a patient by ID
@app.delete("/delete-patient/{patient_id}")
def delete_patient(patient_id: int):
    with sqlite3.connect("data/bookings.db") as conn:
        if not conn.execute("SELECT 1 FROM patients WHERE id = ?", (patient_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Patient not found")
        conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    return {"detail": "Patient deleted"}
# Professions API endpoints
from typing import Dict

@app.get("/professions")
def get_professions_endpoint():
    """Get all professions using the professions_clinics module"""
    return get_all_professions()

@app.post("/add-profession")
def add_profession_endpoint(profession: Dict):
    """Create profession using the professions_clinics module"""
    return create_profession(profession)

# New: Update profession
@app.put("/update-profession/{profession_id}")
def update_profession_endpoint(profession_id: int, profession_data: dict = Body(...)):
    """Update profession using the professions_clinics module"""
    return update_profession(profession_id, profession_data)

# Delete profession
@app.delete("/delete-profession/{profession_id}")
def delete_profession_endpoint(profession_id: int):
    """Delete profession using the professions_clinics module"""
    return delete_profession(profession_id)

# Clinics API endpoints
@app.get("/clinics")
def get_clinics_endpoint():
    """Get all clinics using the professions_clinics module"""
    return get_all_clinics()

@app.post("/add-clinic")
def add_clinic_endpoint(clinic: Dict):
    """Create clinic using the professions_clinics module"""
    return create_clinic(clinic)

# Update clinic
@app.put("/update-clinic/{clinic_id}")
def update_clinic_endpoint(clinic_id: int, clinic_data: dict = Body(...)):
    """Update clinic using the professions_clinics module"""
    return update_clinic(clinic_id, clinic_data)

# Delete clinic
@app.delete("/delete-clinic/{clinic_id}")
def delete_clinic_endpoint(clinic_id: int):
    """Delete clinic using the professions_clinics module"""
    return delete_clinic(clinic_id)


@app.get("/login-page")
def serve_login_page_endpoint():
    """Serve login page using the auth module"""
    return serve_login_page()

# --- LOGOUT Route ---
@app.get("/logout")
def logout_endpoint(request: Request, response: Response):
    """Logout using the auth module"""
    return logout_user(request, response)

# --- CHECK if user is logged in (Optional helper) ---
@app.get("/check-login")
def check_login_endpoint(request: Request):
    """Check login status using the auth module"""
    return check_login_status(request)

@app.get("/therapist-calendar")
def serve_therapist_calendar(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "therapist-calendar.html"))

@app.get("/mdt-calendar")
def serve_mdt_calendar(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "mdt-calendar.html"))

# --- New JSON endpoint: get all billing codes ---
@app.get("/api/billing-codes")
def get_billing_codes(profession: Optional[str] = None):
    with sqlite3.connect("data/bookings.db") as conn:
        if profession:
            cursor = conn.execute("""
                SELECT id, code, description, base_fee, profession
                FROM billing_codes
                WHERE LOWER(profession) = ?
            """, (profession.lower(),))
        else:
            cursor = conn.execute("SELECT id, code, description, base_fee, profession FROM billing_codes")
        return [
            {
                "id": row[0],
                "code": row[1],
                "description": row[2],
                "base_fee": row[3],
                "profession": row[4]
            }
            for row in cursor.fetchall()
        ]

# --- New JSON endpoint: get all billing modifiers ---
from typing import Optional
@app.get("/api/billing_modifiers")
def get_billing_modifiers(profession: Optional[str] = None):
    with sqlite3.connect("data/bookings.db") as conn:
        if profession:
            cursor = conn.execute("""
                SELECT modifier_code, modifier_name, modifier_description, modifier_effect, modifier_multiplier, profession
                FROM billing_modifiers
                WHERE LOWER(profession) = ?
            """, (profession.lower(),))
        else:
            cursor = conn.execute("""
                SELECT modifier_code, modifier_name, modifier_description, modifier_effect, modifier_multiplier, profession
                FROM billing_modifiers
            """)
        return [
            {
                "modifier_code": row[0],
                "modifier_name": row[1],
                "modifier_description": row[2],
                "modifier_effect": row[3],
                "modifier_multiplier": row[4],
                "profession": row[5]
            }
            for row in cursor.fetchall()
        ]

@app.get("/billing-codes")
def serve_billing_codes(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "billing-codes.html"))

# --- New endpoint: get billing codes for a specific profession ---
@app.get("/billing-codes-for-profession")
def get_billing_codes_for_profession(profession: str):
    profession = profession.lower()  # Normalize input for case-insensitive match
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT id, code, description, base_fee, profession
            FROM billing_codes
            WHERE profession = ?
        """, (profession,))
        codes = [
            {
                "id": row[0],
                "code": row[1],
                "description": row[2],
                "base_fee": row[3],
                "profession": row[4]
            }
            for row in cursor.fetchall()
        ]
    return codes

# --- New endpoint: update a billing code ---

@app.put("/billing-codes/{code_id}")
def update_billing_code(code_id: int, updated_data: dict = Body(...)):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE billing_codes
            SET code = ?, description = ?, base_fee = ?
            WHERE id = ?
        """, (
            updated_data.get("code", ""),
            updated_data.get("description", ""),
            float(updated_data.get("base_fee", 0.0)),
            code_id
        ))
        conn.commit()
    return {"detail": "Billing code updated successfully"}

# --- DELETE endpoint for deleting billing codes ---
@app.delete("/billing-codes/{code_id}")
def delete_billing_code(code_id: int):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()
        if not cursor.execute("SELECT 1 FROM billing_codes WHERE id = ?", (code_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Billing code not found")
        cursor.execute("DELETE FROM billing_codes WHERE id = ?", (code_id,))
        conn.commit()
    return {"detail": "Billing code deleted successfully"}


# --- New endpoint: get full treatment note, billing, and supplementary notes for an appointment ---
@app.get("/api/treatment-notes/full/{appointment_id}")
def get_full_treatment_note_endpoint(appointment_id: str):
    """Get full treatment note using the treatment_notes module"""
    return get_full_treatment_note(appointment_id)

    with sqlite3.connect("data/bookings.db") as conn:
        # Check for duplicate billing code for the same profession
        existing = conn.execute("""
            SELECT 1 FROM billing_codes WHERE code = ? AND profession = ?
        """, (data["code"], data["profession"].lower())).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Billing code already exists for this profession")
        conn.execute("""
            INSERT INTO billing_codes (code, description, base_fee, profession)
            VALUES (?, ?, ?, ?)
        """, (
            data["code"],
            data["description"],
            float(data["base_fee"]),
            data["profession"].lower()
        ))
    return {"detail": "Billing code added successfully"}


@app.get("/bookings-for-day-for-therapists")
def bookings_for_day_for_therapists(
    date: str = Query(...),
    therapist_ids: List[int] = Query(...)
):
    print("🗓️ Fetching for date:", date)
    print("🧑‍⚕️ Therapist IDs:", therapist_ids)

    if not therapist_ids:
        return []

    placeholders = ",".join(["?"] * len(therapist_ids))
    query = f"""
        SELECT 
            b.id, b.name, b.therapist, b.date, b.day, b.time, b.duration, b.notes, b.colour,
            t.profession, t.id as therapist_id, t.preferred_name, t.name as therapist_name, t.surname
        FROM bookings b
        JOIN therapists t ON b.therapist = t.id
        WHERE b.date = ? AND b.therapist IN ({placeholders})
    """
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute(query, [date] + therapist_ids)
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print(f"📦 Returning {len(rows)} appointments")
        return rows
    

# --- Treatment Notes Submission Endpoint ---

# --- Modifiers API endpoint ---
# Place this near the other /api/ or /billing-codes routes
@app.get("/api/billing_modifiers")
def get_Billing_modifiers():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT code, description, adjustment_factor FROM billing_modifiers")
        return [
            {
                "code": row[0],
                "description": row[1],
                "adjustment_factor": row[2]
            }
            for row in cursor.fetchall()
        ]

@app.post("/submit-treatment-note")
def submit_treatment_note_endpoint(note: dict):
    """Submit treatment note using the treatment_notes module"""
    return submit_treatment_note(note)
    

# --- ICD-10 Codes API Endpoint ---
from typing import Optional

@app.get("/api/icd10-codes")
def get_icd10_codes(query: str = Query(default="", description="Search ICD-10 codes or descriptions"),
                    is_pmb: Optional[bool] = Query(default=None, description="Filter by PMB status")):
    query = query.lower()
    with sqlite3.connect("data/icd10_with_pmb.db") as conn:
        cursor = conn.cursor()
        sql = """
            SELECT code, description, valid_for_use, valid_as_primary, is_asterisk, is_dagger, is_sequelae, age_range, sex, is_pmb, pmb_condition
            FROM icd10_codes
            WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%"]
        if is_pmb is not None:
            sql += " AND is_pmb = ?"
            params.append("Y" if is_pmb else "N")
        cursor.execute(sql, params)
        results = [
            {
                "code": row[0],
                "description": row[1],
                "valid_for_use": row[2],
                "valid_as_primary": row[3],
                "is_asterisk": row[4],
                "is_dagger": row[5],
                "is_sequelae": row[6],
                "age_range": row[7],
                "sex": row[8],
                "is_pmb": row[9],
                "pmb_condition": row[10]
            }
            for row in cursor.fetchall()
        ]
    return results

# --- GET a single patient by ID (full details for profile) ---

@app.get("/api/patient/{patient_id}")
def get_patient_by_id(patient_id: int):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

# --- GET distinct professions who have booked the patient ---
@app.get("/api/patient/{patient_id}/professions")
def get_patient_professions(patient_id: int):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT DISTINCT t.profession
            FROM bookings b
            JOIN therapists t ON b.therapist = t.id
            WHERE b.patient_id = ?
        """, (patient_id,))
        return [row[0] for row in cursor.fetchall()]

# --- GET patient summary for a specific profession (for Patient Profile) ---
@app.get("/api/patient/{patient_id}/summary/{profession}")
def patient_profession_summary(patient_id: int, profession: str):
    with sqlite3.connect("data/bookings.db") as conn:
        cur = conn.cursor()
        # Last session info with appointment_id and therapist_id for optional linking
        cur.execute("""
            SELECT appointment_date, start_time, therapist_name, appointment_id, therapist_id
            FROM treatment_notes
            WHERE patient_id = ? AND LOWER(profession) = LOWER(?)
            ORDER BY appointment_date DESC, start_time DESC
            LIMIT 1
        """, (patient_id, profession))
        row = cur.fetchone()
        if row:
            date_str = row[0]
            time_str = row[1]
            therapist = row[2]
            appointment_id = row[3]
            therapist_id = row[4]
            last_session = f"{date_str} at {time_str} with {therapist}"
        else:
            last_session = None
            appointment_id = None
            therapist_id = None

        # Count past and future bookings for this profession
        cur.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE patient_id = ? AND LOWER(profession) = LOWER(?) AND date < DATE('now')
        """, (patient_id, profession))
        past_bookings = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE patient_id = ? AND LOWER(profession) = LOWER(?) AND date >= DATE('now')
        """, (patient_id, profession))
        future_bookings = cur.fetchone()[0]

        return {
            "last_session": last_session,
            "appointment_id": appointment_id,
            "therapist_id": therapist_id,
            "past_bookings": past_bookings,
            "future_bookings": future_bookings
        }
    

# Add this endpoint near other /api/patient routes
@app.get("/api/patient/{patient_id}/summary/ai")
def get_patient_ai_summary(patient_id: int):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT appointment_date, profession, subjective_findings, objective_findings, treatment, plan
            FROM treatment_notes
            WHERE patient_id = ?
            ORDER BY appointment_date
        """, (patient_id,))
        notes = cursor.fetchall()

    if not notes:
        return {"summary": "No treatment notes found for this patient."}

    combined_notes = ""
    for row in notes:
        date, prof, subj, obj, tx, plan = row
        combined_notes += f"\n\n[{date}] {prof}\nSubjective: {subj}\nObjective: {obj}\nTreatment: {tx}\nPlan: {plan}"

    prompt = f"Summarise the following multidisciplinary treatment notes for a patient:\n{combined_notes}"

    model = GPT4All("mistral-7b-instruct.gguf")
    model.open()
    summary = model.prompt(prompt)

    return {"summary": summary.strip()}

# --- API: Check if a treatment note exists for an appointment ---
@app.get("/api/check-treatment-note/{appointment_id}")
def check_treatment_note(appointment_id: str):
    with sqlite3.connect("data/bookings.db") as conn:
        cur = conn.execute("SELECT 1 FROM treatment_notes WHERE appointment_id = ?", (appointment_id,))
        return {"has_note": bool(cur.fetchone())}

@app.get("/api/treatment-notes/full/{appointment_id}")
def get_full_notes(appointment_id: str):
    with sqlite3.connect("data/bookings.db") as conn:
        # Fetch main treatment note
        cur = conn.execute("""
            SELECT subjective_findings, objective_findings, treatment, plan, note_completed_at
            FROM treatment_notes
            WHERE appointment_id = ?
        """, (appointment_id,))
        treatment = cur.fetchone()

        # Fetch supplementary notes
        sup_cur = conn.execute("""
            SELECT note, timestamp FROM supplementary_notes
            WHERE appointment_id = ?
            ORDER BY timestamp ASC
        """, (appointment_id,))
        supplementary = [{"note": row[0], "timestamp": row[1]} for row in sup_cur.fetchall()]

        #Fetch billing codes
        cur = conn.execute("""
            SELECT bc.code
            FROM billing_entries be
            JOIN billing_codes bc ON be.code_id = bc.id
            WHERE be.appointment_id = ?
        """, (appointment_id,))
        billing_codes = [row[0] for row in cur.fetchall()]
        return {
            "treatment": {
                "subjective_findings": treatment[0],
                "objective_findings": treatment[1],
                "treatment": treatment[2],
                "plan": treatment[3],
                "note_completed_at": treatment[4]   
            } if treatment else None,
            "supplementary": supplementary,
            "billing": [{"code": code} for code in billing_codes],
        }
# --- NEW ENDPOINT: GET /api/unbilled-treatment-notes ---
# Returns all treatment notes that have not yet been billed (billing_completed = 0 or NULL)
@app.get("/api/unbilled-treatment-notes")
def get_unbilled_treatment_notes():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT tn.*, b.name as booking_name, b.therapist as booking_therapist, b.date as booking_date
            FROM treatment_notes tn
            LEFT JOIN bookings b ON b.id = tn.appointment_id
            WHERE IFNULL(tn.billing_completed, 0) = 0
        """)
        columns = [col[0] for col in cursor.description]
        notes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return notes

# --- NEW ENDPOINT: POST /api/billing-for-appointment ---
# Accepts: { "appointment_id": "string", "billing_entries": [ ... ] }
# Updates billing tables and marks treatment note as billed
@app.post("/api/billing-for-appointment")
def billing_for_appointment(payload: dict = Body(...)):
    appointment_id = payload.get("appointment_id")
    billing_entries = payload.get("billing_entries", [])
    if not appointment_id or not billing_entries:
        raise HTTPException(status_code=400, detail="appointment_id and billing_entries required")
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()
        # Find patient_id and therapist_id from bookings or treatment_notes
        booking = cursor.execute("SELECT patient_id, therapist FROM bookings WHERE id = ?", (appointment_id,)).fetchone()
        if booking:
            patient_id, therapist_id = booking
        else:
            # fallback: try treatment_notes
            note = cursor.execute("SELECT patient_id FROM treatment_notes WHERE appointment_id = ?", (appointment_id,)).fetchone()
            patient_id = note[0] if note else None
            therapist_id = None
        # Compose session_date from bookings or today
        session_date = cursor.execute("SELECT date FROM bookings WHERE id = ?", (appointment_id,)).fetchone()
        session_date = session_date[0] if session_date else None
        # Insert or replace billing_session
        cursor.execute("""
            INSERT OR REPLACE INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            appointment_id,
            patient_id,
            therapist_id,
            session_date,
            payload.get("notes", ""),
            payload.get("total_amount", 0)
        ))
        # Remove previous billing_entries for this appointment
        cursor.execute("DELETE FROM billing_entries WHERE appointment_id = ?", (appointment_id,))
        # Insert billing_entries
        for entry in billing_entries:
            cursor.execute("""
                INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"{appointment_id}-{entry['code_id']}",
                appointment_id,
                entry["code_id"],
                entry.get("billing_modifier", ""),
                entry["final_fee"]
            ))
        # Mark treatment_note as billed
        cursor.execute("UPDATE treatment_notes SET billing_completed = 1 WHERE appointment_id = ?", (appointment_id,))
    return {"detail": "Billing saved and appointment marked as billed"}

# --- INVOICE MANAGEMENT ENDPOINTS ---
from datetime import datetime

# GET /invoices — Return all invoices.
@app.get("/invoices")
def get_invoices():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT * FROM invoices
        """)
        columns = [col[0] for col in cursor.description]
        invoices = [dict(zip(columns, row)) for row in cursor.fetchall()]
        # Optionally, add patient/therapist names if needed
    return invoices

# POST /invoices — Create invoice and assign billing entries.
@app.post("/invoices")
def create_invoice(data: dict = Body(...)):
    invoice_data = data.get("invoice")
    entry_ids = data.get("entry_ids", [])
    if not invoice_data or not entry_ids:
        raise HTTPException(status_code=400, detail="Invoice and entry_ids are required")
    invoice_id = invoice_data.get("id")
    if not invoice_id:
        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()
        # Insert invoice
        cursor.execute("""
            INSERT INTO invoices (id, patient_id, therapist_id, invoice_date, due_date, status, notes, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            invoice_data["patient_id"],
            invoice_data["therapist_id"],
            invoice_data["invoice_date"],
            invoice_data.get("due_date"),
            invoice_data.get("status", "Draft"),
            invoice_data.get("notes", ""),
            invoice_data.get("total_amount", 0)
        ))
        # Assign billing entries to this invoice
        for entry_id in entry_ids:
            cursor.execute("""
                UPDATE billing_entries SET invoice_id = ? WHERE id = ?
            """, (invoice_id, entry_id))
    return {"detail": "Invoice created", "invoice_id": invoice_id}

# GET /invoices/{invoice_id} — Return invoice details and entries.
@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str = Path(...)):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        invoice = cursor.fetchone()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        columns = [col[0] for col in cursor.description]
        invoice_dict = dict(zip(columns, invoice))
        # Get associated billing entries
        entry_cursor = conn.execute("SELECT * FROM billing_entries WHERE invoice_id = ?", (invoice_id,))
        entry_columns = [col[0] for col in entry_cursor.description]
        entries = [dict(zip(entry_columns, row)) for row in entry_cursor.fetchall()]
        invoice_dict["entries"] = entries
    return invoice_dict

# PUT /invoices/{invoice_id} — Update invoice status.
@app.put("/invoices/{invoice_id}")
def update_invoice(invoice_id: str, update_data: dict = Body(...)):
    allowed_fields = {"status", "notes", "due_date", "total_amount"}
    fields = []
    values = []
    for key, value in update_data.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            values.append(value)
    if not fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    values.append(invoice_id)
    with sqlite3.connect("data/bookings.db") as conn:
        cur = conn.execute(f"UPDATE invoices SET {', '.join(fields)} WHERE id = ?", values)
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
    return {"detail": "Invoice updated"}

# DELETE /invoices/{invoice_id} — Delete invoice and unassign billing entries.
@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: str):
    with sqlite3.connect("data/bookings.db") as conn:
        # Unassign billing entries
        conn.execute("UPDATE billing_entries SET invoice_id = NULL WHERE invoice_id = ?", (invoice_id,))
        # Delete invoice
        cur = conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
    return {"detail": "Invoice deleted"}


@app.get("/therapist-stats")
def get_therapist_stats_endpoint():
    """Get therapist statistics using the therapists module"""
    return get_therapist_stats()


@app.post("/reminders")
def create_reminder(data: dict, request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (
                title, description, created_by_user_id, patient_id, therapist_id, appointment_id,
                due_date, recurrence, completed, completed_at, visibility, priority,
                colour, notify, notify_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("title"),
            data.get("description"),
            user_id,
            data.get("patient_id"),
            data.get("therapist_id"),
            data.get("appointment_id"),
            data.get("due_date"),
            data.get("recurrence"),
            data.get("completed", 0),
            data.get("completed_at"),
            data.get("visibility", "private"),
            data.get("priority", "normal"),
            data.get("colour", "#2D6356"),
            data.get("notify", 0),
            data.get("notify_at")
        ))
        conn.commit()
        reminder_id = cursor.lastrowid

    return {"detail": "Reminder created", "id": reminder_id}

# --- Reminders: GET all reminders for the logged-in user or visible to team/patient ---
@app.get("/reminders")
def get_reminders(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            SELECT * FROM reminders
            WHERE created_by_user_id = ? OR visibility IN ('team', 'patient')
            ORDER BY due_date IS NULL, due_date ASC
        """, (user_id,))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
# --- Patient Bookings Endpoint ---
@app.get("/api/patient/{patient_id}/bookings")
def get_patient_bookings(patient_id: str):
    """
    Return a list of bookings for a specific patient, including therapist name,
    billing and notes completion status.
    """
    with sqlite3.connect("data/bookings.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.date,
                b.time,
                b.profession,
                t.name || ' ' || t.surname AS therapist_name,
                CASE WHEN be.id IS NOT NULL THEN 1 ELSE 0 END AS billing_completed,
                CASE WHEN tn.id IS NOT NULL THEN 1 ELSE 0 END AS notes_completed
            FROM bookings b
            LEFT JOIN therapists t ON b.therapist = t.id
            LEFT JOIN billing_entries be ON b.id = be.appointment_id
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            WHERE b.patient_id = ?
            ORDER BY b.date DESC, b.time DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]    
# --- Outcome Measures Endpoint ---

# --- Outcome Measure Types API ---
@app.get("/api/outcome-measure-types")
def get_outcome_measure_types():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT id, name, description, score_type, max_score, interpretation FROM outcome_measure_types")
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "score_type": row[3],
            "max_score": row[4],
            "interpretation": row[5]
        }
        for row in rows
    ]
# Create a new outcome_measure_type
@app.post("/api/outcome-measure-types")
async def create_outcome_measure_type(data: dict):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            INSERT INTO outcome_measure_types (name, max_score, has_subscores)
            VALUES (?, ?, ?)
        """, (data["name"], data["max_score"], data["has_subscores"]))
        conn.commit()
        return {"status": "success", "id": cursor.lastrowid}

# Create a new outcome_measure_type_subscore
@app.post("/api/outcome-measure-type-subscores")
async def create_outcome_measure_type_subscore(data: dict):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("""
            INSERT INTO outcome_measure_type_subscores (outcome_measure_type_id, name, max_score)
            VALUES (?, ?, ?)
        """, (data["outcome_measure_type_id"], data["name"], data["max_score"]))
        conn.commit()
        return {"status": "success", "id": cursor.lastrowid}

# --- New endpoint: Get outcome measure subscores for a given outcome_measure_id ---
@app.get("/api/outcome-measure-subscores/{outcome_measure_id}")
def get_outcome_measure_subscores(outcome_measure_id: int):
    conn = get_db_connection()
    cur = conn.execute(
        "SELECT * FROM outcome_measure_subscores WHERE outcome_measure_id = ?",
        (outcome_measure_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/outcome-measure-types/{type_id}/subscores")
def get_outcome_measure_type_subscores(type_id: int):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute(
            """
            SELECT id, subcategory_name, max_score
            FROM outcome_measure_type_subscores
            WHERE outcome_measure_type_id = ?
            """,
            (type_id,)
        )
        rows = cursor.fetchall()

    return [{"id": row[0], "subcategory_name": row[1], "max_score": row[2]} for row in rows]

# --- Outcome Measure Type Categories Endpoints ---

# Return unique category strings
@app.get("/api/outcome-measure-types/categories")
def get_outcome_measure_categories():
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT DISTINCT category FROM outcome_measure_types WHERE category IS NOT NULL AND TRIM(category) != ''")
        categories = [row[0] for row in cursor.fetchall()]
    return categories

# Return outcome measure types filtered by category
@app.get("/api/outcome-measure-types/by-category/{category}")
def get_outcome_measures_by_category(category: str):
    with sqlite3.connect("data/bookings.db") as conn:
        cursor = conn.execute("SELECT id, name FROM outcome_measure_types WHERE category = ?", (category,))
        measures = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    return measures
from datetime import datetime

@app.post("/api/outcome-measures")
def create_outcome_measure(data: dict = Body(...)):
    """
    Expects JSON with: patient_id, therapist, appointment_id, date,
    outcome_measure_type_id, score (optional/nullable), comments (optional)
    """
    with sqlite3.connect("data/bookings.db") as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO outcome_measures
              (patient_id, therapist, appointment_id, date, outcome_measure_type_id, score, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("patient_id"),
                data.get("therapist", ""),
                data.get("appointment_id"),
                data.get("date"),
                data.get("outcome_measure_type_id"),
                data.get("score"),
                data.get("comments", "")
            )
        )
        new_id = cur.lastrowid
        conn.commit()
    return {"id": new_id}

@app.post("/api/outcome-measures/{measure_id}/subscores")
def add_outcome_measure_subscores(measure_id: int, subscores: List[dict] = Body(...)):
    """
    Expects a JSON array of { subcategory_name, max_score, score, comments }
    """
    if not isinstance(subscores, list):
        raise HTTPException(status_code=400, detail="Subscores must be a list")
    with sqlite3.connect("data/bookings.db") as conn:
        cur = conn.cursor()
        for s in subscores:
            cur.execute(
                """
                INSERT INTO outcome_measure_subscores
                  (outcome_measure_id, subcategory_name, score, max_score, comments)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    measure_id,
                    s.get("subcategory_name", ""),
                    s.get("score"),
                    s.get("max_score"),
                    s.get("comments", "")
                )
            )
        conn.commit()
    return {"status": "ok", "count": len(subscores)}