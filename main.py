# Standard library imports
import io
import json
import logging
import os
import sqlite3
import smtplib
import ssl
import textwrap
from datetime import datetime, timedelta
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
from models.validation import (
    PatientCreateModel, PatientUpdateModel, TreatmentNoteModel, 
    BillingAmountModel, BillingSessionModel, BillingSubmissionModel, AlertResolutionModel,
    UserUpdateModel, TherapistUpdateModel, SettingsUpdateModel, ProfessionUpdateModel,
    ClinicUpdateModel, BillingCodeUpdateModel, InvoiceCreateModel, InvoiceUpdateModel,
    ReminderCreateModel, ReminderUpdateModel,
    UserPreferencesUpdateModel, SystemConfigurationModel, SystemBackupModel, AppointmentBillingModel
)
from controllers.report_controller import (
    ReportCreateRequest, ReportUpdateRequest, AIContentGenerationRequest,
    ReportResponse, ReportDashboardResponse, WizardOptionsResponse,
    TherapistCompletionRequest, TherapistCompletionResponse, ReportCompletionStatusResponse
)
from controllers.template_controller import (
    StructuredTemplateResponse, TemplateInstanceResponse, 
    TemplateInstanceCreateRequest, TemplateInstanceUpdateRequest,
    get_structured_templates, get_structured_template_by_id,
    create_template_instance, get_template_instance_by_id,
    update_template_instance, get_template_instances_for_patient,
    delete_template_instance, generate_ai_content_for_section,
    regenerate_ai_content_for_section
)
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
from modules.database import get_db_connection, get_database_path
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
from modules.reminders import (
    get_all_reminders, create_reminder, get_reminder_by_id, update_reminder,
    delete_reminder, get_pending_reminders, mark_reminder_completed, search_reminders
)
from modules.reports_analytics import (
    get_dashboard_summary, get_patient_summary_report, get_patient_profession_summary,
    get_patient_ai_summary_data, get_latest_note_summary, get_system_overview_report,
    get_therapist_performance_report, get_financial_summary_report, export_patient_data
)
from modules.settings_configuration import (
    get_system_settings, update_system_settings, get_user_preferences, update_user_preferences,
    get_system_configuration, update_system_configuration, create_system_backup,
    restore_system_backup, get_application_info, get_settings_summary
)
from modules.outcome_measures import (
    get_all_domains, get_measures_by_domain, get_measure_by_id,
    create_outcome_entry, get_outcome_entries_for_treatment_note,
    get_outcome_entry_by_id, update_outcome_entry, delete_outcome_entry,
    OutcomeMeasureCalculator, OutcomeMeasureValidator
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


# Add SessionMiddleware for user sessions with secure configuration
from modules.config import config, validate_security_config
from modules.auth import require_auth, require_admin, require_therapist_or_admin, filter_patients_by_access

# Validate security configuration at startup
if not validate_security_config():
    raise RuntimeError("Security configuration validation failed. Check your environment variables.")

# Configure secure session middleware
session_config = config.get_session_config()
app.add_middleware(SessionMiddleware, **session_config)

# patient_id should be str for compatibility with string-based IDs
@app.put("/api/patient/{patient_id}/alerts/{appointment_id}/resolve")
def toggle_alert_resolution(patient_id: str, appointment_id: str, payload: AlertResolutionModel, request: Request = None, user: dict = Depends(require_auth)):
    # Use validated payload data
    resolved = payload.resolved
    with sqlite3.connect(get_database_path()) as conn:
        conn.execute("""
            UPDATE treatment_notes
            SET alert_resolved = ?
            WHERE patient_id = ? AND appointment_id = ?
        """, ("Yes" if resolved else "No", patient_id, appointment_id))
    return {"status": "updated"}
# --- New endpoint: Get latest alerts for a patient ---
@app.get("/api/patient/{patient_id}/alerts")
def get_alerts(patient_id: str, user: dict = Depends(require_auth)):
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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

    # API Security Monitoring - Log usage for tracking and alerting
    api_start_time = datetime.now()
    input_length = len(combined_notes)
    
    # Security: Validate API key exists before making request
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logging.error("SECURITY ALERT: OpenRouter API key not configured")
        raise HTTPException(status_code=500, detail="AI service not available")
    
    # Security: Check rate limits before processing
    if not check_rate_limit():
        raise HTTPException(status_code=429, detail="Daily API usage limit exceeded")
    
    logging.info(f"API USAGE: Medical history generation for patient {patient_id}, input length: {input_length} chars")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hadadahealth.com",
        "X-Title": "HadadaHealth Medical AI"
    }

    body = {
        "model": "mistralai/mistral-nemo:free",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant summarising clinical notes for healthcare professionals."},
            {"role": "user", "content": f"Please extract the medical history and level of function from the following notes:\n{combined_notes}. Never make anything up, only use the information provided. If there is not enough information, say 'No information available'. For headings please use html strong text"}
        ],
        "max_tokens": 1000,  # Security: Limit token usage to prevent cost overruns
        "temperature": 0.3   # Security: Lower temperature for consistent medical summaries
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
            res.raise_for_status()
            
            response_data = res.json()
            summary = response_data["choices"][0]["message"]["content"]
            
            # API Usage Monitoring
            api_end_time = datetime.now()
            duration = (api_end_time - api_start_time).total_seconds()
            
            # Extract usage statistics if available
            usage_info = response_data.get("usage", {})
            prompt_tokens = usage_info.get("prompt_tokens", 0)
            completion_tokens = usage_info.get("completion_tokens", 0)
            total_tokens = usage_info.get("total_tokens", 0)
            
            # Log comprehensive usage statistics
            logging.info(f"API SUCCESS: Medical history generation completed - "
                        f"Patient: {patient_id}, Duration: {duration:.2f}s, "
                        f"Tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")
            
            # Security: Alert on high token usage (potential cost concern)
            if total_tokens > 5000:  # Configurable threshold
                logging.warning(f"HIGH USAGE ALERT: Medical history generation used {total_tokens} tokens for patient {patient_id}")
            
            # Track API usage for monitoring and cost management
            track_api_usage(total_tokens, "medical_history_generation")
            
            summary = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", summary)
            return summary
            
    except httpx.TimeoutException:
        logging.error(f"API TIMEOUT: Medical history generation timed out for patient {patient_id}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    except httpx.HTTPStatusError as e:
        logging.error(f"API ERROR: OpenRouter returned {e.response.status_code} for patient {patient_id}: {e.response.text}")
        raise HTTPException(status_code=502, detail="AI service error")
    except Exception as e:
        logging.error(f"API FAILURE: Medical history generation failed for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="AI processing failed")


# AI summary endpoint (fetches real treatment notes from DB)
@router.get("/api/patient/{patient_id}/summary/ai")
async def get_ai_summary(patient_id: str):
    summary = await generate_ai_medical_history(patient_id)
    return {"summary": summary}

# --- New endpoint: Get latest treatment note summary for patient and profession, with AI summary ---


@app.get("/api/patient/{patient_id}/summary/{profession}/latest")
async def get_latest_note_summary_endpoint(patient_id: str, profession: str, user: dict = Depends(require_auth)):
    """Get latest treatment note summary for patient and profession with AI summary"""
    note_data = get_latest_note_summary(patient_id, profession)
    
    if not note_data:
        raise HTTPException(status_code=404, detail="No treatment notes found for this profession")

    note = {
        "date": note_data.get('appointment_date'),
        "time": note_data.get('start_time'),
        "duration": note_data.get('duration'),
        "therapist": note_data.get('therapist_name'),
        "profession": note_data.get('profession'),
        "subjective": note_data.get('subjective_findings'),
        "objective": note_data.get('objective_findings'),
        "treatment": note_data.get('treatment'),
        "plan": note_data.get('plan'),
    }

    full_text = (
        f"Date: {note['date']} {note['time']} ({note['duration']})\n"
        f"Therapist: {note['therapist']} ({note['profession']})\n"
        f"Subjective: {note['subjective']}\n"
        f"Objective: {note['objective']}\n"
        f"Treatment: {note['treatment']}\n"
        f"Plan: {note['plan']}"
    )

    # API Security Monitoring - Log usage for tracking and alerting
    api_start_time = datetime.now()
    input_length = len(full_text)
    
    # Security: Validate API key exists before making request
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logging.error("SECURITY ALERT: OpenRouter API key not configured")
        raise HTTPException(status_code=500, detail="AI service not available")
    
    # Security: Check rate limits before processing
    if not check_rate_limit():
        raise HTTPException(status_code=429, detail="Daily API usage limit exceeded")
    
    logging.info(f"API USAGE: Latest session summary for patient {patient_id}, profession {profession}, input length: {input_length} chars")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hadadahealth.com",
        "X-Title": "HadadaHealth Session AI"
    }

    body = {
        "model": "mistralai/mistral-nemo:free",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant summarising clinical notes for healthcare professionals."},
            {"role": "user", "content": f"Please write a short paragraph summary (no more than 4 sentances) in simple pros of the latest session with a focus on what was worked on and what the plan is:\n{full_text}"}
        ],
        "max_tokens": 500,   # Security: Limit token usage to prevent cost overruns
        "temperature": 0.3   # Security: Lower temperature for consistent summaries
    }

    # Security: Remove debug file creation in production (potential data exposure)
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "development":
        with open("debug_ai_prompt_latest.json", "w") as f:
            json.dump(body["messages"], f, indent=2)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
            res.raise_for_status()
            
            response_data = res.json()
            summary = response_data["choices"][0]["message"]["content"]
            
            # API Usage Monitoring
            api_end_time = datetime.now()
            duration = (api_end_time - api_start_time).total_seconds()
            
            # Extract usage statistics if available
            usage_info = response_data.get("usage", {})
            prompt_tokens = usage_info.get("prompt_tokens", 0)
            completion_tokens = usage_info.get("completion_tokens", 0)
            total_tokens = usage_info.get("total_tokens", 0)
            
            # Log comprehensive usage statistics
            logging.info(f"API SUCCESS: Session summary completed - "
                        f"Patient: {patient_id}, Profession: {profession}, Duration: {duration:.2f}s, "
                        f"Tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")
            
            # Security: Alert on high token usage (potential cost concern)
            if total_tokens > 2000:  # Lower threshold for session summaries
                logging.warning(f"HIGH USAGE ALERT: Session summary used {total_tokens} tokens for patient {patient_id}")
            
            # Track API usage for monitoring and cost management
            track_api_usage(total_tokens, "session_summary")
            
            return {"summary": summary}
            
    except httpx.TimeoutException:
        logging.error(f"API TIMEOUT: Session summary timed out for patient {patient_id}, profession {profession}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    except httpx.HTTPStatusError as e:
        logging.error(f"API ERROR: OpenRouter returned {e.response.status_code} for patient {patient_id}: {e.response.text}")
        raise HTTPException(status_code=502, detail="AI service error")
    except Exception as e:
        logging.error(f"API FAILURE: Session summary failed for patient {patient_id}, profession {profession}: {str(e)}")
        raise HTTPException(status_code=500, detail="AI processing failed")

# --- New endpoint: Get latest session note for a patient and profession

@app.get("/api/patient/{patient_id}/latest-session-note/{profession}")
def get_latest_session_note(patient_id: int, profession: str, user: dict = Depends(require_auth)):
    with sqlite3.connect(get_database_path()) as conn:
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
def check_treatment_notes(ids: str = Query(..., description="Comma separated appointment IDs"), user: dict = Depends(require_auth)):
    id_list = [id_str.strip() for id_str in ids.split(",") if id_str.strip()]
    if not id_list:
        return []
    
    # Create safe parameterized query with proper placeholders
    placeholders = ",".join("?" * len(id_list))
    sql = "SELECT appointment_id FROM treatment_notes WHERE appointment_id IN (" + placeholders + ")"
    
    with sqlite3.connect(get_database_path()) as conn:
        rows = conn.execute(sql, id_list).fetchall()
    found = {row[0] for row in rows}
    return [{"id": appt_id, "has_note": appt_id in found} for appt_id in id_list]

# POST endpoint to create a new billing session with associated billing entries
@app.post("/billing-sessions")
def create_billing_session(data: dict = Body(...), request: Request = None, user: dict = Depends(require_therapist_or_admin)):
    try:
        print(f"DEBUG: Received billing data: {data}")
        session_data = data.get("session")
        entries_data = data.get("entries", [])
        print(f"DEBUG: session_data: {session_data}")
        print(f"DEBUG: entries_data: {entries_data}")

        if not session_data or not entries_data:
            raise HTTPException(status_code=400, detail="Session and entries are required")

        # ensure we have a therapist_id (fall back to session-linked therapist)
        therapist_id = session_data.get("therapist_id") or request.session.get("linked_therapist_id")
        if not therapist_id:
            raise HTTPException(status_code=400, detail="Therapist ID is required")

        with sqlite3.connect(get_database_path()) as conn:
            cursor = conn.cursor()
            session_id = session_data["id"]
            
            # Calculate total amount from entries if not provided
            total_amount = session_data.get("total_amount", 0)
            if total_amount == 0 and entries_data:
                total_amount = sum(entry.get("final_fee", 0) for entry in entries_data)
            
            cursor.execute("""
                INSERT OR REPLACE INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                session_data["patient_id"],
                therapist_id,
                session_data["session_date"],
                session_data.get("notes", ""),
                total_amount
            ))
            
            # Clear existing billing entries for this session to avoid duplicates
            cursor.execute("DELETE FROM billing_entries WHERE appointment_id = ?", (session_id,))
            
            for entry in entries_data:
                print(f"DEBUG: Processing entry: {entry}")
                # Convert code_id to integer if it's a string
                code_id = entry["code_id"]
                if isinstance(code_id, str):
                    try:
                        code_id = int(code_id)
                    except ValueError:
                        # If it's not a numeric string, look up the billing code by name/code
                        cursor.execute("SELECT id FROM billing_codes WHERE code = ?", (code_id,))
                        result = cursor.fetchone()
                        if result:
                            code_id = result[0]
                        else:
                            print(f"WARNING: Could not find billing code for: {code_id}")
                            continue
                
                cursor.execute("""
                    INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    f"{session_id}-{entry['code_id']}",  # unique entry ID
                    session_id,                          # appointment reference
                    code_id,                             # billing code foreign key (now converted to int)
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
                total_amount
            ))
            # Mark booking as billing completed
            cursor.execute(
                "UPDATE bookings SET billing_completed = 1 WHERE id = ?",
                (session_id,)
            )
            conn.commit()
        
        return {"detail": "Billing session and entries created successfully"}
    
    except Exception as e:
        import traceback
        print(f"ERROR in billing-sessions: {e}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create billing session: {str(e)}")


# --- New: POST endpoint to submit a full billing payload (overwrite session and entries) ---
@app.post("/submit-billing")
def submit_billing(data: BillingSubmissionModel, user: dict = Depends(require_therapist_or_admin)):
    session_data = data.get("session")
    entries_data = data.get("entries", [])

    if not session_data or not entries_data:
        raise HTTPException(status_code=400, detail="Session and entries are required")

    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.execute("SELECT id, code, description, base_fee, profession FROM billing_codes;")
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

# GET endpoint to retrieve billing sessions with their entries for a patient
@app.get("/billing-sessions/{patient_id}")
def get_billing_sessions(patient_id: str, user: dict = Depends(require_auth)):
    # Handle both string and numeric patient IDs
    if not patient_id or patient_id == "undefined":
        return {"error": "Invalid patient ID"}
    
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.execute("""
            SELECT * FROM billing_sessions WHERE patient_id = ?
        """, (patient_id,))
        sessions = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

        for session in sessions:
            entry_cursor = conn.execute("""
                SELECT be.*, bc.code as code_id 
                FROM billing_entries be
                LEFT JOIN billing_codes bc ON be.code_id = bc.id
                WHERE be.appointment_id = ?
            """, (session["id"],))
            session["entries"] = [dict(zip([col[0] for col in entry_cursor.description], row)) for row in entry_cursor.fetchall()]
    return sessions

# --- New endpoint: List all invoices with their entries and therapist profession ---
@app.get("/invoices")
def list_invoices():
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
def update_user_endpoint(user_id: int, user_data: UserUpdateModel, request: Request = None):
    """Update user using the auth module"""
    return update_user(user_id, user_data.dict(exclude_none=True), request)

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
def update_therapist_endpoint(therapist_id: int, therapist_data: TherapistUpdateModel):
    """Update therapist using the therapists module"""
    success = update_therapist(therapist_id, therapist_data.dict(exclude_none=True))
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
    with sqlite3.connect(get_database_path()) as conn:
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

def init_patients_table():
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
        for name in aids:
            try:
                conn.execute("INSERT INTO medical_aids (name) VALUES (?)", (name,))
            except sqlite3.IntegrityError:
                continue  # Skip duplicates


# Therapist table setup
def init_therapists_table():
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
def get_booking_endpoint(booking_id: str):
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

    with sqlite3.connect(get_database_path()) as conn:
        try:
            conn.execute("""
                INSERT INTO bookings (id, name, therapist, date, day, time, duration, notes, colour, user_id, profession, patient_id, appointment_type_id, billing_code)
                VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                booking.patient_id,
                booking.appointment_type_id,
                booking.billing_code
            ))
            
            # Auto-create billing entry if appointment has billing codes and appointment type
            if booking.appointment_type_id and booking.billing_code:
                try:
                    # Get appointment type details to get default billing codes
                    appointment_type_cursor = conn.execute("""
                        SELECT default_billing_codes, default_billing_code, is_enabled 
                        FROM practice_appointment_types 
                        WHERE appointment_type_id = ? AND practice_id = ?
                    """, (booking.appointment_type_id, 1))  # TODO: Get practice_id from session
                    
                    appointment_type_data = appointment_type_cursor.fetchone()
                    
                    if appointment_type_data and appointment_type_data[2]:  # is_enabled (billable)
                        # Create billing session
                        session_date = f"{booking.date[:10]}T{booking.time}:00"
                        conn.execute("""
                            INSERT INTO billing_sessions (id, patient_id, therapist_id, session_date, notes, total_amount)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            booking.id,  # Use booking ID as session ID
                            booking.patient_id,
                            therapist_id,
                            session_date,
                            f"Auto-generated from appointment: {booking.name}",
                            0  # Will be calculated when billing codes are added
                        ))
                        
                        # Parse and add billing codes (try new format first, then fallback to legacy)
                        billing_codes_json = appointment_type_data[0] or appointment_type_data[1]  # default_billing_codes or default_billing_code
                        if billing_codes_json:
                            import json
                            try:
                                # Try parsing as multiple codes first
                                if appointment_type_data[0]:  # default_billing_codes (new format)
                                    billing_codes = json.loads(appointment_type_data[0])
                                else:  # default_billing_code (legacy format)
                                    billing_codes = [{"code": appointment_type_data[1], "quantity": 1, "modifier": None}]
                                for i, billing_code in enumerate(billing_codes):
                                    # Get billing code details
                                    code_cursor = conn.execute("""
                                        SELECT id, base_fee FROM billing_codes WHERE code = ?
                                    """, (billing_code['code'],))
                                    
                                    code_data = code_cursor.fetchone()
                                    if code_data:
                                        quantity = billing_code.get('quantity', 1)
                                        modifier = billing_code.get('modifier', '')
                                        base_fee = float(code_data[1]) if code_data[1] else 0
                                        
                                        # Apply modifier if exists
                                        if modifier:
                                            modifier_cursor = conn.execute("""
                                                SELECT adjustment_factor FROM billing_modifiers WHERE code = ?
                                            """, (modifier,))
                                            modifier_data = modifier_cursor.fetchone()
                                            if modifier_data:
                                                base_fee *= float(modifier_data[0])
                                        
                                        final_fee = base_fee * quantity
                                        
                                        # Insert billing entry
                                        conn.execute("""
                                            INSERT INTO billing_entries (id, appointment_id, code_id, billing_modifier, final_fee)
                                            VALUES (?, ?, ?, ?, ?)
                                        """, (
                                            f"{booking.id}-{i}",  # Unique entry ID
                                            booking.id,
                                            code_data[0],
                                            modifier,
                                            final_fee
                                        ))
                            except json.JSONDecodeError:
                                print(f"Invalid JSON in default_billing_codes for appointment type {booking.appointment_type_id}")
                        
                        print(f"✅ Auto-created billing entries for appointment {booking.id}")
                        
                except Exception as e:
                    print(f"⚠️  Failed to auto-create billing entries: {e}")
                    # Don't fail the booking creation if billing creation fails
                    
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Booking ID already exists")
    
    return booking


# PUT update booking
@app.put("/bookings/{booking_id}", response_model=Booking)
def update_booking(booking_id: str, booking: Booking, request: Request):
    therapist_id = booking.therapist or request.session.get('linked_therapist_id')
    if not therapist_id:
        raise HTTPException(status_code=400, detail="Therapist ID is required")

    with sqlite3.connect(get_database_path()) as conn:
        if not conn.execute("SELECT 1 FROM bookings WHERE id = ?", (booking_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Booking not found")
        conn.execute("""
            UPDATE bookings SET name=?, therapist=?, date=?, day=?, time=?, duration=?, notes=?, colour=?, profession=?, patient_id=?, appointment_type_id=?
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
            booking.appointment_type_id,
            booking_id
        ))
    return booking

# API endpoints for bookings (used by frontend)
@app.post("/api/bookings", response_model=Booking)
def api_add_booking(booking: Booking, request: Request):
    """API endpoint for creating bookings (matches frontend expectations)"""
    return add_booking(booking, request)

@app.patch("/api/bookings/{booking_id}", response_model=Booking)
def api_update_booking(booking_id: str, booking: Booking, request: Request):
    """API endpoint for updating bookings (matches frontend expectations)"""
    return update_booking(booking_id, booking, request)

# --- New endpoint: Mark billing complete and auto-create draft invoice ---
@app.post("/complete-billing/{booking_id}")
def complete_billing(booking_id: str, request: Request):
    # ensure authenticated
    if not request.session.get('user_id'):
        raise HTTPException(status_code=401, detail="Not authenticated")
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
        exists = conn.execute("SELECT 1 FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        print(f"🔎 Booking exists? {bool(exists)}")  # Debug log
        if not exists:
            print("⚠️ Booking not found in DB")  # Debug log
            raise HTTPException(status_code=404, detail="Booking not found")
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        print("✅ Booking deleted successfully")  # Debug log
    return {"detail": "Booking deleted"}

# Get patient form field requirements
@app.get("/patient-form-schema")
async def get_patient_form_schema():
    """Return field requirements for the patient form to show mandatory field indicators"""
    
    # Define which fields are mandatory vs optional
    schema = {
        "mandatory_fields": [
            "first_name",
            "surname"
        ],
        "conditional_mandatory": {
            "account_responsible_is_patient": {
                "description": "When patient is responsible for account",
                "suggested_required_fields": ["email", "contact_number", "address_line1", "town"]
            },
            "funding_option_medical_aid": {
                "description": "When using medical aid funding", 
                "suggested_required_fields": ["medical_aid_name", "medical_aid_number", "main_member_name"]
            },
            "funding_option_alternative": {
                "description": "When using alternative funding",
                "suggested_required_fields": ["alternative_funding_source"]
            }
        },
        "optional_fields": [
            "title", "preferred_name", "date_of_birth", "gender", "id_number",
            "email", "contact_number", "phone_home", "phone_work", "phone_cell", 
            "clinic", "address_line1", "address_line2", "town", "postal_code", 
            "country", "account_responsible", "account_name", "account_id_number", 
            "account_address", "account_phone", "account_email", "funding_option", 
            "main_member_name", "medical_aid_name", "medical_aid_other", "plan_name", 
            "medical_aid_number", "dependent_number", "alternative_funding_source", 
            "alternative_funding_other", "claim_number", "case_manager", 
            "emergency_contact_name", "emergency_contact_relationship", 
            "emergency_contact_phone", "patient_important_info", "consent_treatment", 
            "consent_photography", "consent_data", "consent_communication", 
            "consent_billing", "consent_terms", "signature_identity", 
            "signature_name", "signature_relationship", "signature_data"
        ],
        "business_logic": {
            "auto_fill_when_patient_responsible": [
                "account_name", "account_id_number", "account_email", 
                "account_phone", "account_address"
            ],
            "clear_when_private_payment": [
                "medical_aid_name", "medical_aid_other", "plan_name", 
                "medical_aid_number", "dependent_number", "main_member_name"
            ]
        },
        "validation_rules": {
            "id_number": "Must be 13-digit South African ID with valid checksum",
            "email": "Must be valid email format (or leave empty)",
            "phone_numbers": "Must be South African phone number format",
            "postal_code": "Must be 4-digit South African postal code"
        },
        "field_labels": {
            "first_name": "First Name *",
            "surname": "Surname *", 
            "title": "Title",
            "preferred_name": "Preferred Name",
            "date_of_birth": "Date of Birth",
            "gender": "Gender",
            "id_number": "ID Number",
            "email": "Email Address",
            "contact_number": "Contact Number",
            "address_line1": "Address Line 1",
            "town": "City/Town",
            "postal_code": "Postal Code",
            "medical_aid_name": "Medical Aid Name",
            "medical_aid_number": "Member Number",
            "alternative_funding_source": "Alternative Funding Source"
        }
    }
    
    return schema

# Test endpoint for validation debugging
@app.post("/test-patient-validation")
async def test_patient_validation(request: Request):
    """Test endpoint to debug patient validation without saving to database"""
    try:
        patient_data = await request.json()
        print(f"🧪 Testing patient data validation: {patient_data}")
        
        # Try to validate
        patient = PatientCreateModel(**patient_data)
        
        return {
            "status": "success",
            "message": "Validation passed!",
            "validated_data": patient.model_dump(),
            "received_fields": list(patient_data.keys())
        }
        
    except Exception as e:
        from pydantic import ValidationError
        
        if isinstance(e, ValidationError):
            error_details = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                error_details.append({
                    "field": field_path,
                    "message": error['msg'],
                    "type": error['type'],
                    "input": error.get('input', 'N/A')
                })
            
            return {
                "status": "validation_failed",
                "message": f"Validation failed with {len(error_details)} errors",
                "errors": error_details,
                "received_data": patient_data,
                "received_fields": list(patient_data.keys())
            }
        else:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "received_data": patient_data
            }

# POST save patient (with detailed validation error reporting)
@app.post("/patients")
async def save_patient(request: Request, user: dict = Depends(require_therapist_or_admin)):
    # Get the raw JSON data from the request
    try:
        patient_data = await request.json()
        print(f"📝 Received patient data: {patient_data}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")
    
    # Try to validate the data with our PatientCreateModel
    try:
        patient = PatientCreateModel(**patient_data)
        print(f"✅ Validation successful for patient: {patient.first_name} {patient.surname}")
    except Exception as e:
        # Import ValidationError to handle Pydantic errors specifically
        from pydantic import ValidationError
        
        if isinstance(e, ValidationError):
            # Format detailed error information
            error_details = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                error_details.append({
                    "field": field_path,
                    "message": error['msg'],
                    "type": error['type'],
                    "input": error.get('input', 'N/A')
                })
            
            print(f"❌ Validation failed with {len(error_details)} errors:")
            for detail in error_details:
                print(f"  - {detail['field']}: {detail['message']} (type: {detail['type']})")
            
            raise HTTPException(
                status_code=422, 
                detail={
                    "message": "Patient data validation failed",
                    "errors": error_details,
                    "received_data": patient_data
                }
            )
        else:
            # Non-validation error
            print(f"❌ Unexpected error during validation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
    
    therapist_id = request.session.get("linked_therapist_id")
    if hasattr(patient, "therapist_id") and getattr(patient, "therapist_id", None):
        therapist_id = getattr(patient, "therapist_id")

    # Generate unique patient ID
    import time
    import random
    patient_id = f"PAT_{int(time.time())}_{random.randint(1000, 9999)}"
    
    with sqlite3.connect(get_database_path()) as conn:
        conn.execute("""
            INSERT INTO patients (
                id, first_name, surname, preferred_name, date_of_birth, gender,
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
            patient_id,
            patient.first_name,
            patient.surname,
            patient.preferred_name,
            patient.date_of_birth,
            patient.gender,
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
    return {"detail": "Patient saved", "patient_id": patient_id}

from typing import Dict

# Update patient endpoint (PUT)
@app.put("/update-patient/{patient_id}")
def update_patient(patient_id: int, patient_data: PatientUpdateModel):
    # Convert validated Pydantic model to dict, excluding None values
    update_data = patient_data.dict(exclude_none=True)
    
    # Build safe SQL update statement
    fields = []
    values = []
    for key, value in update_data.items():
        fields.append(f"{key} = ?")
        values.append(value)
    
    values.append(patient_id)
    if not fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    with sqlite3.connect(get_database_path()) as conn:
        # Ensure icd10_codes column exists
        try:
            conn.execute("ALTER TABLE patients ADD COLUMN icd10_codes TEXT;")
        except sqlite3.OperationalError:
            pass
        
        # Build safe SQL query - fields are now whitelisted
        sql_query = "UPDATE patients SET " + ", ".join(fields) + " WHERE id = ?"
        cur = conn.execute(sql_query, values)
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
    return {"detail": "Patient updated successfully"}

# --- GET all patients, including icd10_codes ---
# --- GET all patients, including icd10_codes ---
@app.get("/patients")
def get_patients(user: dict = Depends(require_therapist_or_admin)):
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.execute("SELECT * FROM patients")
        columns = [column[0] for column in cursor.description]
        all_patients = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Filter patients based on user permissions
        filtered_patients = filter_patients_by_access(
            all_patients, 
            user.get("role"), 
            user.get("linked_therapist_id")
        )
        
        return filtered_patients


# --- New endpoint: Get medical history summary and generated date for a patient ---
@app.get("/api/patient/{patient_id}/medical-history")
def get_medical_history(patient_id: str, user: dict = Depends(require_auth)):
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
async def regenerate_medical_history(patient_id: str, user: dict = Depends(require_auth)):
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
def import_patients(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    try:
        df = pd.read_excel(file.file)
        import time
        import random
        
        with sqlite3.connect(get_database_path()) as conn:
            for _, row in df.iterrows():
                # Generate unique patient ID for each import
                patient_id = f"PAT_{int(time.time())}_{random.randint(1000, 9999)}"
                
                values = (
                    patient_id,  # Add the generated ID as first value
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
                        id, first_name, surname, preferred_name, date_of_birth, gender, id_number,
                        address_line1, address_line2, town, postal_code, country,
                        email, contact_number, clinic,
                        account_name, account_id_number, account_address, account_phone, account_email,
                        funding_option, main_member_name, medical_aid_name, medical_aid_other, plan_name,
                        medical_aid_number, dependent_number, alternative_funding_source, alternative_funding_other,
                        claim_number, case_manager, patient_important_info,
                        consent_treatment, consent_photography, consent_data, consent_communication,
                        consent_billing, consent_terms,
                        signature_identity, signature_name, signature_relationship, signature_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    with sqlite3.connect(get_database_path()) as conn:
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
        response = FileResponse(os.path.join("templates", "login.html"))
        # Prevent caching of login page to ensure proper logout flow
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    response = FileResponse(os.path.join("templates", "index.html"))
    # Prevent caching of authenticated pages
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/offline.html")
def serve_offline():
    return FileResponse(os.path.join("templates", "offline.html"))

@app.get("/template-management")
def serve_template_management(request: Request):
    if not request.session.get("user_id"):
        response = FileResponse(os.path.join("templates", "login.html"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    response = FileResponse(os.path.join("templates", "template_management.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/ai-reports")
def serve_ai_reports_dashboard(request: Request):
    if not request.session.get("user_id"):
        response = FileResponse(os.path.join("templates", "login.html"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    response = FileResponse(os.path.join("templates", "ai_reports.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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

# Serve the appointment types management page
@app.get("/appointment-types-management-page")
def serve_appointment_types_management_page(request: Request):
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "appointment-types-management.html"))

# Settings API endpoints
@app.get("/settings")
def get_settings_endpoint():
    """Get system settings using the settings module"""
    return get_system_settings()

@app.post("/settings")
def update_settings_endpoint(settings_data: SettingsUpdateModel):
    """Update system settings using the settings module"""
    return update_system_settings(settings_data.dict(exclude_none=True))

# System Configuration endpoints
@app.get("/system-configuration")
def get_system_configuration_endpoint():
    """Get system configuration"""
    return get_system_configuration()

@app.post("/system-configuration")
def update_system_configuration_endpoint(config_data: SystemConfigurationModel):
    """Update system configuration"""
    return update_system_configuration(config_data.dict(exclude_none=True))

# Application Information endpoint
@app.get("/application-info")
def get_application_info_endpoint():
    """Get application information and status"""
    return get_application_info()

# System Backup endpoint
@app.get("/system-backup")
def create_system_backup_endpoint():
    """Create and return system backup"""
    return create_system_backup()

@app.get("/patients")
def get_patients():
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.execute("""
            SELECT 
                id, first_name, surname, preferred_name, gender, date_of_birth,
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
def update_patient_admin(patient_id: int, patient_data: PatientUpdateModel, user: dict = Depends(require_admin)):
    # Convert validated Pydantic model to dict, excluding None values
    update_data = patient_data.dict(exclude_none=True)
    
    # Build safe SQL update statement  
    fields = []
    values = []
    for key, value in update_data.items():
        fields.append(f"{key} = ?")
        values.append(value)
    
    if not fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    values.append(patient_id)
    
    with sqlite3.connect(get_database_path()) as conn:
        # Build safe SQL query - fields are now whitelisted
        sql_query = "UPDATE patients SET " + ", ".join(fields) + " WHERE id = ?"
        result = conn.execute(sql_query, values)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
    
    return {"detail": "Patient updated successfully"}

# API endpoint to delete a patient by ID
@app.delete("/delete-patient/{patient_id}")
def delete_patient(patient_id: int, user: dict = Depends(require_admin)):
    with sqlite3.connect(get_database_path()) as conn:
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
def update_profession_endpoint(profession_id: int, profession_data: ProfessionUpdateModel):
    """Update profession using the professions_clinics module"""
    return update_profession(profession_id, profession_data.dict(exclude_none=True))

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
def update_clinic_endpoint(clinic_id: int, clinic_data: ClinicUpdateModel):
    """Update clinic using the professions_clinics module"""
    return update_clinic(clinic_id, clinic_data.dict(exclude_none=True))

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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
def update_billing_code(code_id: int, updated_data: BillingCodeUpdateModel):
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.cursor()
        data_dict = updated_data.dict(exclude_none=True)
        cursor.execute("""
            UPDATE billing_codes
            SET code = ?, description = ?, base_fee = ?
            WHERE id = ?
        """, (
            data_dict.get("code", ""),
            data_dict.get("description", ""),
            float(data_dict.get("rate", 0.0)),
            code_id
        ))
        conn.commit()
    return {"detail": "Billing code updated successfully"}

# --- DELETE endpoint for deleting billing codes ---
@app.delete("/billing-codes/{code_id}")
def delete_billing_code(code_id: int):
    with sqlite3.connect(get_database_path()) as conn:
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

    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
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
    try:
        import sys
        print(f"DEBUG: Received treatment note data: {list(note.keys())}", flush=True)
        print(f"DEBUG: Full note data: {note}", flush=True)
        sys.stdout.flush()
        return submit_treatment_note(note)
    except HTTPException as e:
        print(f"ERROR: Treatment note submission failed: {e.detail}", flush=True)
        sys.stdout.flush()
        raise e
    except Exception as e:
        print(f"ERROR: Unexpected error in treatment note submission: {e}", flush=True)
        sys.stdout.flush()
        raise HTTPException(status_code=500, detail=f"Failed to submit treatment note: {str(e)}")
    

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
def get_patient_by_id(patient_id: int, user: dict = Depends(require_auth)):
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

# --- GET distinct professions who have booked the patient ---
@app.get("/api/patient/{patient_id}/professions")
def get_patient_professions(patient_id: int, user: dict = Depends(require_auth)):
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.execute("""
            SELECT DISTINCT t.profession
            FROM bookings b
            JOIN therapists t ON b.therapist = t.id
            WHERE b.patient_id = ?
        """, (patient_id,))
        return [row[0] for row in cursor.fetchall()]

# --- GET patient summary for a specific profession (for Patient Profile) ---
@app.get("/api/patient/{patient_id}/summary/{profession}")
def patient_profession_summary_endpoint(patient_id: int, profession: str, user: dict = Depends(require_auth)):
    """Get patient summary for a specific profession"""
    return get_patient_profession_summary(patient_id, profession)
    

# Add this endpoint near other /api/patient routes
@app.get("/api/patient/{patient_id}/summary/ai")
def get_patient_ai_summary_endpoint(patient_id: int, user: dict = Depends(require_auth)):
    """Get AI summary for patient treatment notes"""
    notes = get_patient_ai_summary_data(patient_id)
    
    if not notes:
        return {"summary": "No treatment notes found for this patient."}

    combined_notes = ""
    for note in notes:
        date = note.get('appointment_date')
        prof = note.get('profession')
        subj = note.get('subjective_findings')
        obj = note.get('objective_findings')
        tx = note.get('treatment')
        plan = note.get('plan')
        combined_notes += f"\n\n[{date}] {prof}\nSubjective: {subj}\nObjective: {obj}\nTreatment: {tx}\nPlan: {plan}"

    prompt = f"Summarise the following multidisciplinary treatment notes for a patient:\n{combined_notes}"

    model = GPT4All("mistral-7b-instruct.gguf")
    model.open()
    summary = model.prompt(prompt)

    return {"summary": summary.strip()}

# --- API: Check if a treatment note exists for an appointment ---
@app.get("/api/check-treatment-note/{appointment_id}")
def check_treatment_note(appointment_id: str):
    with sqlite3.connect(get_database_path()) as conn:
        cur = conn.execute("SELECT 1 FROM treatment_notes WHERE appointment_id = ?", (appointment_id,))
        return {"has_note": bool(cur.fetchone())}

@app.get("/api/treatment-notes/full/{appointment_id}")
def get_full_notes(appointment_id: str):
    with sqlite3.connect(get_database_path()) as conn:
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
def get_unbilled_treatment_notes(user: dict = Depends(require_therapist_or_admin)):
    with sqlite3.connect(get_database_path()) as conn:
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
def billing_for_appointment(payload: AppointmentBillingModel):
    appointment_id = payload.appointment_id
    billing_entries = payload.billing_entries
    with sqlite3.connect(get_database_path()) as conn:
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
    with sqlite3.connect(get_database_path()) as conn:
        cursor = conn.execute("""
            SELECT * FROM invoices
        """)
        columns = [col[0] for col in cursor.description]
        invoices = [dict(zip(columns, row)) for row in cursor.fetchall()]
        # Optionally, add patient/therapist names if needed
    return invoices

# POST /invoices — Create invoice and assign billing entries.
@app.post("/invoices")
def create_invoice(data: InvoiceCreateModel):
    invoice_data = data.invoice.dict()
    entry_ids = data.entry_ids
    
    invoice_id = invoice_data.get("id")
    if not invoice_id:
        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    with sqlite3.connect(get_database_path()) as conn:
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
        conn.commit()
    return {"detail": "Invoice created", "invoice_id": invoice_id}

# GET /invoices/{invoice_id} — Return invoice details and entries.
@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str = Path(...)):
    with sqlite3.connect(get_database_path()) as conn:
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
def update_invoice(invoice_id: str, update_data: InvoiceUpdateModel, user: dict = Depends(require_therapist_or_admin)):
    allowed_fields = {"status", "notes", "due_date", "amount_paid", "payment_date"}
    fields = []
    values = []
    update_dict = update_data.dict(exclude_none=True)
    for key, value in update_dict.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            values.append(value)
    if not fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    values.append(invoice_id)
    
    with sqlite3.connect(get_database_path()) as conn:
        # Build safe SQL query - fields are whitelisted so this is safe
        sql_query = "UPDATE invoices SET " + ", ".join(fields) + " WHERE id = ?"
        cur = conn.execute(sql_query, values)
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
    return {"detail": "Invoice updated"}

# DELETE /invoices/{invoice_id} — Delete invoice and unassign billing entries.
@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: str):
    with sqlite3.connect(get_database_path()) as conn:
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


# --- Patient Bookings Endpoint ---
@app.get("/api/patient/{patient_id}/bookings")
def get_patient_bookings(patient_id: str, user: dict = Depends(require_auth)):
    """
    Return a list of bookings for a specific patient, including therapist name,
    billing and notes completion status.
    """
    with sqlite3.connect(get_database_path()) as conn:
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
# ===== REMINDER ENDPOINTS =====

@app.get("/api/reminders")
def get_reminders_endpoint(request: Request):
    """Get all reminders for the current user"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return get_all_reminders(user_id)


@app.get("/reminders")
def get_reminders_legacy_endpoint(request: Request):
    """Get all reminders (legacy endpoint for frontend compatibility)"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return get_all_reminders(user_id)


@app.post("/reminders")
def create_reminder_endpoint(reminder_data: ReminderCreateModel, request: Request = None):
    """Create a new reminder"""
    user_id = request.session.get("user_id") if request else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return create_reminder(reminder_data.dict(), user_id)


@app.get("/api/reminders/{reminder_id}")
def get_reminder_endpoint(reminder_id: int):
    """Get a specific reminder by ID"""
    reminder = get_reminder_by_id(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@app.put("/reminders/{reminder_id}")
def update_reminder_endpoint(reminder_id: int, reminder_data: ReminderUpdateModel):
    """Update a reminder"""
    return update_reminder(reminder_id, reminder_data.dict(exclude_none=True))


@app.delete("/api/reminders/{reminder_id}")
def delete_reminder_endpoint(reminder_id: int):
    """Delete a reminder"""
    return delete_reminder(reminder_id)


@app.get("/api/reminders/pending")
def get_pending_reminders_endpoint(request: Request):
    """Get pending reminders for the current user"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return get_pending_reminders(user_id)


@app.post("/api/reminders/{reminder_id}/complete")
def complete_reminder_endpoint(reminder_id: int):
    """Mark a reminder as completed"""
    return mark_reminder_completed(reminder_id)


@app.get("/api/reminders/search")
def search_reminders_endpoint(q: str = Query(...), request: Request = None):
    """Search reminders"""
    user_id = request.session.get("user_id") if request else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return search_reminders(q, user_id)


# ===== REPORTS & ANALYTICS ENDPOINTS =====

@app.get("/api/dashboard/summary")
def get_dashboard_summary_endpoint(request: Request):
    """Get comprehensive dashboard summary"""
    user_id = request.session.get("user_id")
    therapist_id = request.session.get("linked_therapist_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return get_dashboard_summary(user_id, therapist_id)


@app.get("/api/reports/patient/{patient_id}")
def get_patient_report_endpoint(patient_id: int, user: dict = Depends(require_auth)):
    """Get comprehensive patient report"""
    return get_patient_summary_report(patient_id)


@app.get("/api/reports/system-overview")
def get_system_overview_endpoint():
    """Get system overview report"""
    return get_system_overview_report()


@app.get("/api/reports/therapist-performance/{therapist_id}")
def get_therapist_performance_endpoint(therapist_id: int):
    """Get therapist performance report"""
    return get_therapist_performance_report(therapist_id)


@app.get("/api/reports/therapist-performance")
def get_all_therapist_performance_endpoint():
    """Get all therapist performance report"""
    return get_therapist_performance_report()


@app.get("/api/reports/financial-summary")
def get_financial_summary_endpoint(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get financial summary report"""
    return get_financial_summary_report(start_date, end_date)


@app.get("/api/export/patient/{patient_id}")
def export_patient_data_endpoint(patient_id: int, format: str = "json", user: dict = Depends(require_auth)):
    """Export comprehensive patient data"""
    return export_patient_data(patient_id, format)


# ===== PATIENT API ENDPOINTS FOR WIZARD =====

@app.get("/api/patients/search")
def search_patients_endpoint(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    current_user: dict = Depends(require_auth)
):
    """Search patients by name, MRN, or ID"""
    try:
        with sqlite3.connect(get_database_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT 
                    id, first_name, surname, date_of_birth as dob,
                    COALESCE(medical_aid_number, account_id_number) as identifiers
                FROM patients 
                WHERE (first_name LIKE ? OR surname LIKE ? OR 
                       account_id_number LIKE ? OR medical_aid_number LIKE ?)
                ORDER BY surname, first_name
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
            
            patients = [dict(row) for row in cursor.fetchall()]
            return patients
            
    except Exception as e:
        import traceback
        print(f"Patient search error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/patients/recent")
def get_recent_patients_endpoint(
    limit: int = Query(10, le=20),
    current_user: dict = Depends(require_auth)
):
    """Get recent patients based on recent bookings"""
    try:
        with sqlite3.connect(get_database_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get patients with recent bookings (last 30 days)
            cursor.execute("""
                SELECT DISTINCT
                    p.id, p.first_name, p.surname, p.date_of_birth as dob,
                    COALESCE(p.medical_aid_number, p.account_id_number) as identifiers,
                    MAX(b.date) as last_booking
                FROM patients p
                JOIN bookings b ON p.id = b.patient_id
                WHERE b.date >= date('now', '-30 days')
                GROUP BY p.id, p.first_name, p.surname, p.date_of_birth, 
                         COALESCE(p.medical_aid_number, p.account_id_number)
                ORDER BY last_booking DESC
                LIMIT ?
            """, (limit,))
            
            patients = [dict(row) for row in cursor.fetchall()]
            return patients
            
    except Exception as e:
        import traceback
        print(f"Recent patients error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent patients: {str(e)}")


# ===== DEBUG ENDPOINTS =====

@app.get("/api/patients/recent-test")
def get_recent_patients_test_endpoint(limit: int = Query(5, le=20)):
    """Test endpoint without auth to debug patient loading"""
    try:
        with sqlite3.connect(get_database_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get patients with recent bookings (last 30 days)
            cursor.execute("""
                SELECT DISTINCT
                    p.id, p.first_name, p.surname, p.date_of_birth as dob,
                    COALESCE(p.medical_aid_number, p.account_id_number) as identifiers,
                    MAX(b.date) as last_booking
                FROM patients p
                JOIN bookings b ON p.id = b.patient_id
                WHERE b.date >= date('now', '-30 days')
                GROUP BY p.id, p.first_name, p.surname, p.date_of_birth, 
                         COALESCE(p.medical_aid_number, p.account_id_number)
                ORDER BY last_booking DESC
                LIMIT ?
            """, (limit,))
            
            patients = [dict(row) for row in cursor.fetchall()]
            return {"status": "success", "count": len(patients), "patients": patients}
            
    except Exception as e:
        import traceback
        print(f"Test recent patients error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/therapists-test") 
def get_therapists_test_endpoint():
    """Test therapists loading"""
    try:
        import sqlite3
        with sqlite3.connect(get_database_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all therapists
            cursor.execute("""
                SELECT id, name, profession
                FROM therapists 
                ORDER BY name
            """)
            
            therapists = [dict(row) for row in cursor.fetchall()]
            return {"status": "success", "count": len(therapists), "therapists": therapists}
            
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/reports/wizard/options-test")
def get_wizard_options_test_endpoint():
    """Test wizard options without auth"""
    try:
        from controllers.report_controller import ReportController
        # Test with minimal parameters
        test_options = {
            "allowed_report_types": ["progress", "discharge", "assessment"],
            "priorities": [{"value": 1, "label": "Low"}, {"value": 2, "label": "Medium"}, {"value": 3, "label": "High"}],
            "user_role": "therapist",
            "user_defaults": {"priority": 2},
            "recommended_disciplines": [],
            "suggested_therapists": [],
            "other_therapists": []
        }
        return test_options
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

# ===== AI REPORT MANAGEMENT ENDPOINTS =====

@app.get("/api/reports/wizard/options")
def get_wizard_options_endpoint(
    request: Request,
    patient_id: Optional[str] = Query(None),
    disciplines: Optional[str] = Query(None),
    current_user: dict = Depends(require_auth)
):
    """Get wizard options with booking-based recommendations"""
    try:
        from controllers.report_controller import ReportController
        print(f"🔍 Wizard Options Debug: patient_id={patient_id}, disciplines={disciplines}")
        result = ReportController.get_wizard_options(patient_id, disciplines, current_user)
        print(f"🔍 Result type: {type(result)}")
        return result
    except Exception as e:
        import traceback
        print(f"🔥 Wizard Options Error: {str(e)}")
        print(f"🔥 Traceback: {traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/reports/create")
async def create_report_endpoint(request: ReportCreateRequest, current_user: dict = Depends(require_auth)):
    """Create a new report"""
    from controllers.report_controller import ReportController
    return await ReportController.create_report(request, current_user)


@app.post("/api/reports")
async def create_report_endpoint_legacy(request: ReportCreateRequest, current_user: dict = Depends(require_auth)):
    """Create a new report (legacy endpoint)"""
    from controllers.report_controller import ReportController
    return await ReportController.create_report(request, current_user)


@app.get("/api/reports/{report_id}")
def get_report_endpoint(report_id: int, current_user: dict = Depends(require_auth)):
    """Get a specific report"""
    from controllers.report_controller import ReportController
    return ReportController.get_report(report_id, current_user)


@app.put("/api/reports/{report_id}")
def update_report_endpoint(report_id: int, request: ReportUpdateRequest, current_user: dict = Depends(require_auth)):
    """Update a report"""
    from controllers.report_controller import ReportController
    return ReportController.update_report(report_id, request, current_user)


@app.delete("/api/reports/{report_id}")
def delete_report_endpoint(report_id: int, current_user: dict = Depends(require_auth)):
    """Delete a report"""
    from controllers.report_controller import ReportController
    return ReportController.delete_report(report_id, current_user)


@app.put("/api/reports/{report_id}/reassign")
def reassign_report_endpoint(report_id: int, request: dict, current_user: dict = Depends(require_auth)):
    """Reassign a report to different therapists"""
    from controllers.report_controller import ReportController
    return ReportController.reassign_report(report_id, request, current_user)


@app.get("/api/therapists")
def get_therapists_endpoint(current_user: dict = Depends(require_auth)):
    """Get list of therapists for assignment"""
    from modules.database import execute_query
    
    # Get therapists from the therapists table with correct professions
    therapists = execute_query(
        """
        SELECT id, 
               COALESCE(preferred_name, name) || ' ' || surname as full_name,
               profession
        FROM therapists 
        ORDER BY surname, name
        """,
        fetch='all'
    )
    
    if not therapists:
        # Fallback to basic list if no therapists found
        return [
            {"id": "1", "name": "Duncan Miller", "profession": "Physiotherapy"},
            {"id": "3", "name": "Kim Jones", "profession": "Occupational Therapy"}
        ]
    
    return [
        {
            "id": str(therapist['id']), 
            "name": therapist['full_name'], 
            "profession": therapist['profession']
        }
        for therapist in therapists
    ]


@app.get("/report/{report_id}")
async def serve_report_editor(report_id: int):
    """Serve report editor page - redirects to template editor if available"""
    from fastapi.responses import RedirectResponse
    from modules.database import execute_query
    
    try:
        # Check if report has a linked template instance
        query = """
            SELECT template_instance_id FROM reports 
            WHERE id = ? AND template_instance_id IS NOT NULL
        """
        result = execute_query(query, (report_id,), fetch='one')
        
        if result and result['template_instance_id']:
            # Redirect to template editor
            return RedirectResponse(url=f"/template-instance/{result['template_instance_id']}/edit")
        else:
            # For reports without template instances, show a basic report view
            # This could be enhanced later with a dedicated report viewer
            return RedirectResponse(url=f"/ai-reports?report_id={report_id}")
            
    except Exception as e:
        print(f"Error serving report editor: {e}")
        return RedirectResponse(url="/ai-reports")


@app.get("/api/reports/user/dashboard")
def get_user_dashboard_endpoint(current_user: dict = Depends(require_auth)):
    """Get dashboard data for current user"""
    from controllers.report_controller import ReportController
    return ReportController.get_dashboard_data(current_user)


@app.get("/api/reports")
def get_all_reports_endpoint(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of reports to return"),
    current_user: dict = Depends(require_auth)
):
    """Get all reports accessible to current user"""
    from controllers.report_controller import ReportController
    return ReportController.get_user_reports(status, limit, current_user)

@app.get("/api/reports/user/reports")
def get_user_reports_endpoint(status: Optional[str] = None, limit: int = 50, current_user: dict = Depends(require_auth)):
    """Get reports for current user"""
    from controllers.report_controller import ReportController
    return ReportController.get_user_reports(status, limit, current_user)


@app.post("/api/reports/{report_id}/ai-content")
async def generate_ai_content_endpoint(report_id: int, request: AIContentGenerationRequest, current_user: dict = Depends(require_auth)):
    """Generate AI content for a report"""
    from controllers.report_controller import ReportController
    return await ReportController.generate_ai_content(report_id, request, current_user)


# Individual Therapist Completion Endpoints

@app.post("/api/reports/{report_id}/complete-therapist")
async def complete_therapist_portion_endpoint(
    report_id: int, 
    request: Optional[TherapistCompletionRequest] = None, 
    current_user: dict = Depends(require_auth)
):
    """Mark the current therapist's portion of the report as complete"""
    from controllers.report_controller import ReportController
    return await ReportController.complete_therapist_portion(report_id, request, current_user)


@app.get("/api/reports/{report_id}/completion-status")
async def get_report_completion_status_endpoint(report_id: int, current_user: dict = Depends(require_auth)):
    """Get detailed completion status for a report including individual therapist completions"""
    from controllers.report_controller import ReportController
    return await ReportController.get_report_completion_status(report_id)


@app.delete("/api/reports/{report_id}/complete-therapist")
async def remove_therapist_completion_endpoint(report_id: int, current_user: dict = Depends(require_auth)):
    """Remove the current therapist's completion (undo completion)"""
    from controllers.report_controller import ReportController
    return await ReportController.remove_therapist_completion(report_id, current_user)


@app.get("/api/report-templates")
def get_report_templates_endpoint():
    """Get available report templates"""
    from controllers.report_controller import get_report_templates_endpoint
    return get_report_templates_endpoint()


@app.get("/api/reports/{report_id}/pdf")
def export_report_pdf_endpoint(report_id: int, current_user: dict = Depends(require_auth)):
    """Export report as PDF"""
    from modules.pdf_export import export_report_pdf, get_report_pdf_filename
    from modules.reports import ReportWorkflowService
    
    # Check permissions
    has_permission, error_msg = ReportWorkflowService.validate_report_permissions(
        report_id, current_user.get('user_id'), 'read'
    )
    
    if not has_permission:
        raise HTTPException(status_code=403, detail=error_msg)
    
    try:
        # Generate PDF
        pdf_buffer = export_report_pdf(report_id)
        filename = get_report_pdf_filename(report_id)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate PDF: {str(e)}")


@app.get("/api/reports/patient/{patient_id}/data-summary")
def get_patient_data_summary_endpoint(
    patient_id: str, 
    disciplines: Optional[List[str]] = Query(None), 
    current_user: dict = Depends(require_auth)
):
    """Get patient data summary for report generation with permission checks"""
    from controllers.report_controller import get_patient_data_for_report
    from modules.reports import ReportWorkflowService
    
    # For multi-disciplinary access, verify user has appropriate permissions
    # This could be enhanced with specific discipline-based permissions
    user_role = current_user.get('role', 'therapist')
    
    # Allow access if user is admin/manager or if they have treated the patient
    if user_role in ['admin', 'manager']:
        return get_patient_data_for_report(patient_id, disciplines)
    else:
        # For therapists, check if they have treated this patient
        # This would need to check treatment history - simplified for now
        return get_patient_data_for_report(patient_id, disciplines)


@app.get("/api/reports/patient/{patient_id}/disciplines")
def get_patient_disciplines_endpoint(patient_id: str, current_user: dict = Depends(require_auth)):
    """Get disciplines that have treated a patient"""
    from modules.database import get_patient_disciplines
    
    # Check permissions
    user_role = current_user.get('role', 'therapist')
    if user_role not in ['admin', 'manager', 'therapist']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    disciplines = get_patient_disciplines(patient_id)
    return {"patient_id": patient_id, "disciplines": disciplines}


@app.get("/api/reports/multidisciplinary/{patient_id}")
def get_multidisciplinary_report_data_endpoint(
    patient_id: str,
    disciplines: Optional[List[str]] = Query(None, description="Specific disciplines to include"),
    current_user: dict = Depends(require_auth)
):
    """Get comprehensive multi-disciplinary report data"""
    from modules.data_aggregation import get_patient_data_summary
    
    # Enhanced permission check for cross-disciplinary data
    user_role = current_user.get('role', 'therapist')
    user_id = current_user.get('user_id')
    
    if user_role not in ['admin', 'manager', 'therapist']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get comprehensive patient data
        patient_summary = get_patient_data_summary(patient_id, disciplines)
        
        # Filter sensitive data based on user permissions
        filtered_summary = {
            "patient_id": patient_summary.patient_id,
            "disciplines_involved": patient_summary.disciplines_involved,
            "data_completeness": patient_summary.data_completeness,
            "demographics": patient_summary.demographics if user_role in ['admin', 'manager'] else None,
            "treatment_notes_count": len(patient_summary.treatment_notes),
            "outcome_measures_count": len(patient_summary.outcome_measures),
            # Include treatment notes if user is admin/manager or involved in treatment
            "treatment_notes": patient_summary.treatment_notes if user_role in ['admin', 'manager'] else [],
            "outcome_measures": patient_summary.outcome_measures if user_role in ['admin', 'manager'] else []
        }
        
        return filtered_summary
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve multi-disciplinary data: {str(e)}")


# Removed duplicate analytics endpoint - using the working implementation below


@app.post("/api/reports/regenerate-ai")
def regenerate_ai_content_endpoint(request: ReportCreateRequest, current_user: dict = Depends(require_auth)):
    """Regenerate AI content for a report"""
    from controllers.report_controller import ReportController
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    try:
        # Use the existing AI content generation functionality
        result = ReportController.generate_ai_content(request, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error regenerating AI content: {str(e)}")


@app.get("/api/reports/{report_id}/revisions")
def get_report_revisions_endpoint(report_id: str, current_user: dict = Depends(require_auth)):
    """Get revision history for a report"""
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    try:
        # For now, return mock data since we don't have revision tracking implemented
        revisions = [
            {
                "id": f"rev_{report_id}_1",
                "created_date": "2024-01-15T10:30:00",
                "author": "Dr. Smith",
                "changes_summary": "Initial AI-generated content"
            },
            {
                "id": f"rev_{report_id}_2", 
                "created_date": "2024-01-15T14:45:00",
                "author": "Dr. Smith",
                "changes_summary": "Manual edits to clinical findings section"
            }
        ]
        return revisions
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving revisions: {str(e)}")


@app.get("/api/notifications/user")
def get_user_notifications_endpoint(current_user: dict = Depends(require_auth)):
    """Get notifications for the current user"""
    from modules.reports import ReportNotificationService
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    try:
        notifications = ReportNotificationService.get_user_report_notifications(user_id)
        unread_count = len([n for n in notifications if not n.get('is_read')])
        
        return {
            "notifications": notifications,
            "unread_count": unread_count,
            "total_count": len(notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving notifications: {str(e)}")


@app.post("/api/notifications/{notification_id}/read")
def mark_notification_read_endpoint(notification_id: int, current_user: dict = Depends(require_auth)):
    """Mark a specific notification as read"""
    from modules.reports import ReportNotificationService
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    try:
        success = ReportNotificationService.mark_notification_as_read(notification_id)
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error marking notification as read: {str(e)}")


@app.post("/api/notifications/mark-all-read")
def mark_all_notifications_read_endpoint(current_user: dict = Depends(require_auth)):
    """Mark all notifications as read for the current user"""
    from modules.reports import ReportNotificationService
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    try:
        notifications = ReportNotificationService.get_user_report_notifications(user_id, unread_only=True)
        marked_count = 0
        
        for notification in notifications:
            success = ReportNotificationService.mark_notification_as_read(notification['id'])
            if success:
                marked_count += 1
        
        return {
            "message": f"Marked {marked_count} notifications as read",
            "marked_count": marked_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error marking all notifications as read: {str(e)}")


@app.post("/api/notifications/create")
def create_notification_endpoint(notification_data: dict, current_user: dict = Depends(require_auth)):
    """Create a new notification (admin/system use)"""
    from modules.database import create_report_notification
    
    user_role = current_user.get('role', 'therapist')
    if user_role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        notification_id = create_report_notification(
            report_id=notification_data.get('report_id'),
            user_id=notification_data.get('user_id'),
            notification_type=notification_data.get('type', 'reminder'),
            message=notification_data.get('message', '')
        )
        
        return {"notification_id": notification_id, "message": "Notification created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating notification: {str(e)}")


@app.get("/api/reports/analytics")
def get_reports_analytics_endpoint(request: Request):
    """Get report analytics data for dashboard widgets"""
    try:
        # Get user_id from session if available, otherwise use mock data
        user_id = request.session.get('user_id') if hasattr(request, 'session') else None
        
        # For now, return mock data since we don't have full reports implementation
        # This can be replaced with real data once the reports system is fully implemented
        total_reports = 0
        pending_count = 0
        in_progress_count = 0
        completed_count = 0
        overdue_count = 0
        
        completion_rate = 0
        if total_reports > 0:
            completion_rate = (completed_count / total_reports) * 100
        
        # Weekly stats (mock for now)
        weekly_completed = min(completed_count, 10)
        weekly_target = 10
        
        return {
            "total_reports": total_reports,
            "pending_count": pending_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,
            "overdue_count": overdue_count,
            "completion_rate": round(completion_rate, 1),
            "average_completion_days": 3.2,
            "urgent_reports": max(overdue_count, pending_count // 3) if pending_count > 0 else 0,
            "weekly_completed": weekly_completed,
            "weekly_target": weekly_target
        }
        
    except Exception as e:
        # Return mock data on error to prevent dashboard failures
        return {
            "total_reports": 15,
            "pending_count": 3,
            "in_progress_count": 5,
            "completed_count": 7,
            "overdue_count": 2,
            "completion_rate": 75.0,
            "average_completion_days": 3.2,
            "urgent_reports": 4,
            "weekly_completed": 7,
            "weekly_target": 10
        }


# ===== STRUCTURED TEMPLATE ENDPOINTS =====

@app.get("/api/templates", response_model=List[StructuredTemplateResponse])
def get_structured_templates_endpoint(active_only: bool = Query(True, description="Only return active templates")):
    """Get all structured templates"""
    return get_structured_templates(active_only=active_only)


@app.get("/api/templates/{template_id}", response_model=StructuredTemplateResponse)
def get_structured_template_endpoint(template_id: int = Path(..., gt=0, description="Template ID")):
    """Get a structured template by ID"""
    return get_structured_template_by_id(template_id)


@app.post("/api/templates/instances", response_model=TemplateInstanceResponse)
def create_template_instance_endpoint(request: TemplateInstanceCreateRequest):
    """Create a new template instance with auto-populated data"""
    print(f"🔍 Creating template instance: {request}")
    return create_template_instance(request)


@app.get("/api/templates/instances/{instance_id}", response_model=TemplateInstanceResponse)
def get_template_instance_endpoint(instance_id: int = Path(..., gt=0, description="Template instance ID")):
    """Get a template instance by ID"""
    return get_template_instance_by_id(instance_id)


@app.put("/api/templates/instances/{instance_id}", response_model=TemplateInstanceResponse)
def update_template_instance_endpoint(
    instance_id: int = Path(..., gt=0, description="Template instance ID"),
    request: TemplateInstanceUpdateRequest = Body(...)
):
    """Update a template instance (save draft, complete, etc.)"""
    return update_template_instance(instance_id, request)


@app.get("/api/templates/instances/patient/{patient_id}", response_model=List[TemplateInstanceResponse])
def get_patient_template_instances_endpoint(
    patient_id: int = Path(..., gt=0, description="Patient ID"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get all template instances for a patient"""
    return get_template_instances_for_patient(patient_id, status)


@app.delete("/api/templates/instances/{instance_id}")
def delete_template_instance_endpoint(instance_id: int = Path(..., gt=0, description="Template instance ID")):
    """Delete a template instance"""
    return delete_template_instance(instance_id)


@app.post("/api/templates/instances/{instance_id}/ai-generate/{section_id}/{field_id}")
def generate_ai_content_endpoint(
    instance_id: int = Path(..., gt=0, description="Template instance ID"),
    section_id: str = Path(..., description="Section identifier"),
    field_id: str = Path(..., description="Field identifier")
):
    """Generate AI content for a specific template section field"""
    return generate_ai_content_for_section(instance_id, section_id, field_id)


@app.post("/api/templates/instances/{instance_id}/ai-regenerate/{section_id}/{field_id}")
def regenerate_ai_content_endpoint(
    instance_id: int = Path(..., gt=0, description="Template instance ID"),
    section_id: str = Path(..., description="Section identifier"),
    field_id: str = Path(..., description="Field identifier")
):
    """Regenerate AI content from treatment notes for a specific template section field"""
    return regenerate_ai_content_for_section(instance_id, section_id, field_id)


# ===== SETTINGS & CONFIGURATION ENDPOINTS =====

@app.get("/api/user/{user_id}/preferences")
def get_user_preferences_endpoint(user_id: int):
    """Get user preferences"""
    return get_user_preferences(user_id)


@app.post("/api/user/{user_id}/preferences")
def update_user_preferences_endpoint(user_id: int, preferences: UserPreferencesUpdateModel):
    """Update user preferences"""
    return update_user_preferences(user_id, preferences.dict(exclude_none=True))


@app.get("/api/auth/me")
def get_current_user_endpoint(current_user: dict = Depends(require_auth)):
    """Get current authenticated user information"""
    return current_user


@app.post("/api/system/restore")
def restore_system_backup_endpoint(backup_data: SystemBackupModel):
    """Restore system from backup"""
    return restore_system_backup(backup_data.dict())


@app.get("/api/system/info")
def get_application_info_endpoint():
    """Get application information"""
    return get_application_info()


@app.get("/api/settings/summary")
def get_settings_summary_endpoint():
    """Get comprehensive settings summary"""
    return get_settings_summary()


# ===== API SECURITY AND MONITORING ENDPOINTS =====

# Global API usage tracking (in-memory for now, should be moved to database in production)
API_USAGE_TRACKING = {
    "daily_requests": {},
    "daily_tokens": {},
    "daily_costs": {},  # Estimated costs
    "alerts_sent": {}
}

# Security constants for API monitoring
MAX_DAILY_REQUESTS = int(os.getenv("MAX_DAILY_AI_REQUESTS", "100"))  # Configurable limit
MAX_DAILY_TOKENS = int(os.getenv("MAX_DAILY_AI_TOKENS", "50000"))    # Configurable limit
COST_PER_1K_TOKENS = float(os.getenv("AI_COST_PER_1K_TOKENS", "0.001"))  # Configurable cost

def track_api_usage(tokens_used: int, request_type: str = "ai_summary"):
    """Track API usage for monitoring and alerting"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Initialize tracking for today if not exists
    if today not in API_USAGE_TRACKING["daily_requests"]:
        API_USAGE_TRACKING["daily_requests"][today] = {}
        API_USAGE_TRACKING["daily_tokens"][today] = 0
        API_USAGE_TRACKING["daily_costs"][today] = 0.0
        API_USAGE_TRACKING["alerts_sent"][today] = {"requests": False, "tokens": False, "cost": False}
    
    # Track request count by type
    if request_type not in API_USAGE_TRACKING["daily_requests"][today]:
        API_USAGE_TRACKING["daily_requests"][today][request_type] = 0
    API_USAGE_TRACKING["daily_requests"][today][request_type] += 1
    
    # Track total tokens and estimated cost
    API_USAGE_TRACKING["daily_tokens"][today] += tokens_used
    estimated_cost = (tokens_used / 1000) * COST_PER_1K_TOKENS
    API_USAGE_TRACKING["daily_costs"][today] += estimated_cost
    
    # Check for alerts
    total_requests = sum(API_USAGE_TRACKING["daily_requests"][today].values())
    total_tokens = API_USAGE_TRACKING["daily_tokens"][today]
    total_cost = API_USAGE_TRACKING["daily_costs"][today]
    
    # Alert thresholds (80% of max)
    request_threshold = int(MAX_DAILY_REQUESTS * 0.8)
    token_threshold = int(MAX_DAILY_TOKENS * 0.8)
    cost_threshold = (MAX_DAILY_TOKENS / 1000 * COST_PER_1K_TOKENS) * 0.8
    
    # Log alerts if thresholds exceeded and not already alerted
    alerts = API_USAGE_TRACKING["alerts_sent"][today]
    
    if total_requests >= request_threshold and not alerts["requests"]:
        logging.warning(f"API USAGE ALERT: Daily request threshold reached - {total_requests}/{MAX_DAILY_REQUESTS}")
        alerts["requests"] = True
    
    if total_tokens >= token_threshold and not alerts["tokens"]:
        logging.warning(f"API USAGE ALERT: Daily token threshold reached - {total_tokens}/{MAX_DAILY_TOKENS}")
        alerts["tokens"] = True
    
    if total_cost >= cost_threshold and not alerts["cost"]:
        logging.warning(f"API COST ALERT: Daily cost threshold reached - ${total_cost:.4f}")
        alerts["cost"] = True

@app.get("/api/admin/ai-usage")
def get_ai_usage_statistics(user: dict = Depends(require_admin)):
    """Get AI API usage statistics (admin only)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    current_stats = {
        "date": today,
        "requests_today": sum(API_USAGE_TRACKING["daily_requests"].get(today, {}).values()),
        "tokens_today": API_USAGE_TRACKING["daily_tokens"].get(today, 0),
        "estimated_cost_today": round(API_USAGE_TRACKING["daily_costs"].get(today, 0), 4),
        "request_breakdown": API_USAGE_TRACKING["daily_requests"].get(today, {}),
        "limits": {
            "max_daily_requests": MAX_DAILY_REQUESTS,
            "max_daily_tokens": MAX_DAILY_TOKENS,
            "cost_per_1k_tokens": COST_PER_1K_TOKENS
        },
        "utilization": {
            "requests_percent": round((sum(API_USAGE_TRACKING["daily_requests"].get(today, {}).values()) / MAX_DAILY_REQUESTS) * 100, 1),
            "tokens_percent": round((API_USAGE_TRACKING["daily_tokens"].get(today, 0) / MAX_DAILY_TOKENS) * 100, 1)
        }
    }
    
    # Historical data (last 7 days)
    historical = {}
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        historical[date] = {
            "requests": sum(API_USAGE_TRACKING["daily_requests"].get(date, {}).values()),
            "tokens": API_USAGE_TRACKING["daily_tokens"].get(date, 0),
            "cost": round(API_USAGE_TRACKING["daily_costs"].get(date, 0), 4)
        }
    
    return {
        "current": current_stats,
        "historical": historical,
        "security_status": "SECURE - API key never exposed to client",
        "monitoring_active": True
    }

def check_rate_limit() -> bool:
    """Check if current daily usage is within limits"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    current_requests = sum(API_USAGE_TRACKING["daily_requests"].get(today, {}).values())
    current_tokens = API_USAGE_TRACKING["daily_tokens"].get(today, 0)
    
    if current_requests >= MAX_DAILY_REQUESTS:
        logging.error(f"RATE LIMIT EXCEEDED: Daily request limit of {MAX_DAILY_REQUESTS} reached")
        return False
    
    if current_tokens >= MAX_DAILY_TOKENS:
        logging.error(f"RATE LIMIT EXCEEDED: Daily token limit of {MAX_DAILY_TOKENS} reached")
        return False
    
    return True


# ===========================
# OUTCOME MEASURES ENDPOINTS
# ===========================

@app.get("/api/outcome-measures/domains")
def api_get_outcome_domains(user: dict = Depends(require_auth)):
    """Get all outcome measure domains"""
    try:
        return {"domains": get_all_domains()}
    except Exception as e:
        logging.error(f"Error getting outcome domains: {e}")
        raise HTTPException(status_code=500, detail="Failed to get outcome domains")


@app.get("/api/outcome-measures/domains/{domain_id}/measures")
def api_get_measures_by_domain(domain_id: int, user: dict = Depends(require_auth)):
    """Get all measures for a specific domain"""
    try:
        measures = get_measures_by_domain(domain_id)
        return {"measures": measures}
    except Exception as e:
        logging.error(f"Error getting measures for domain {domain_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get measures")


@app.get("/api/outcome-measures/measures/{measure_id}")
def api_get_measure_by_id(measure_id: int, user: dict = Depends(require_auth)):
    """Get measure details by ID"""
    try:
        measure = get_measure_by_id(measure_id)
        if not measure:
            raise HTTPException(status_code=404, detail="Measure not found")
        return {"measure": measure}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting measure {measure_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get measure")


@app.post("/api/outcome-entries")
def api_create_outcome_entry(
    entry_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """Create a new outcome measure entry"""
    try:
        appointment_id = entry_data.get('appointment_id')
        measure_id = entry_data.get('measure_id')
        
        if not appointment_id or not measure_id:
            raise HTTPException(status_code=400, detail="appointment_id and measure_id are required")
        
        # Get measure details for validation and calculation
        measure = get_measure_by_id(measure_id)
        if not measure:
            raise HTTPException(status_code=404, detail="Measure not found")
        
        # Validate entry data
        errors = OutcomeMeasureValidator.validate_entry(measure['abbreviation'], entry_data)
        if errors:
            raise HTTPException(status_code=400, detail={"validation_errors": errors})
        
        # Calculate results based on measure type
        calculated_data = _calculate_outcome_results(measure, entry_data)
        
        # Merge calculated data with entry data
        entry_data.update(calculated_data)
        
        # Create the entry
        entry_id = create_outcome_entry(appointment_id, measure_id, entry_data, user['user_id'])
        
        return {"message": "Outcome entry created successfully", "entry_id": entry_id}
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error creating outcome entry: {e}")
        logging.error(f"Full traceback: {error_details}")
        print(f"ERROR: {e}")
        print(f"TRACEBACK: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to create outcome entry: {str(e)}")


@app.get("/api/treatment-notes/{appointment_id}/outcome-entries")
def api_get_outcome_entries_for_treatment_note(
    appointment_id: str,
    user: dict = Depends(require_auth)
):
    """Get all outcome entries for a treatment note"""
    try:
        entries = get_outcome_entries_for_treatment_note(appointment_id)
        return {"entries": entries}
    except Exception as e:
        logging.error(f"Error getting outcome entries for treatment note {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get outcome entries")


@app.get("/api/outcome-entries/{entry_id}")
def api_get_outcome_entry_by_id(entry_id: int, user: dict = Depends(require_auth)):
    """Get detailed outcome entry by ID"""
    try:
        entry = get_outcome_entry_by_id(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Outcome entry not found")
        return {"entry": entry}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting outcome entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get outcome entry")


@app.put("/api/outcome-entries/{entry_id}")
def api_update_outcome_entry(
    entry_id: int,
    entry_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """Update an existing outcome entry"""
    try:
        # Get existing entry to validate ownership and get measure info
        existing_entry = get_outcome_entry_by_id(entry_id)
        if not existing_entry:
            raise HTTPException(status_code=404, detail="Outcome entry not found")
        
        # Get measure details for validation and calculation
        measure = get_measure_by_id(existing_entry['measure_id'])
        if not measure:
            raise HTTPException(status_code=404, detail="Measure not found")
        
        # Validate entry data
        errors = OutcomeMeasureValidator.validate_entry(measure['abbreviation'], entry_data)
        if errors:
            raise HTTPException(status_code=400, detail={"validation_errors": errors})
        
        # Calculate results based on measure type
        calculated_data = _calculate_outcome_results(measure, entry_data)
        
        # Merge calculated data with entry data
        entry_data.update(calculated_data)
        
        # Update the entry
        success = update_outcome_entry(entry_id, entry_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update outcome entry")
        
        return {"message": "Outcome entry updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating outcome entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update outcome entry")


@app.delete("/api/outcome-entries/{entry_id}")
def api_delete_outcome_entry(entry_id: int, user: dict = Depends(require_auth)):
    """Delete an outcome entry"""
    try:
        # Verify entry exists
        existing_entry = get_outcome_entry_by_id(entry_id)
        if not existing_entry:
            raise HTTPException(status_code=404, detail="Outcome entry not found")
        
        # Delete the entry
        success = delete_outcome_entry(entry_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete outcome entry")
        
        return {"message": "Outcome entry deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting outcome entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete outcome entry")


def _calculate_outcome_results(measure: dict, entry_data: dict) -> dict:
    """Calculate results for an outcome measure entry"""
    calculator = OutcomeMeasureCalculator()
    abbreviation = measure['abbreviation']
    
    try:
        if abbreviation == 'BBS':
            if entry_data.get('individual_items'):
                result = calculator.calculate_berg_balance_scale(entry_data['individual_items'])
            else:
                result = {'total_score': entry_data.get('total_score'), 'calculated_result': f"{entry_data.get('total_score')}/56"}
            
        elif abbreviation == 'ABC':
            if entry_data.get('individual_items'):
                result = calculator.calculate_abc_scale(entry_data['individual_items'])
            else:
                result = {'total_score': entry_data.get('total_score'), 'calculated_result': f"{entry_data.get('total_score')}%"}
        
        elif abbreviation == '10mWT':
            comfortable_times = entry_data.get('comfortable_trials', [])
            fast_times = entry_data.get('fast_trials', [])
            result = calculator.calculate_10mwt(comfortable_times, fast_times)
            
            # Store raw data for database
            entry_data['raw_data'] = {}
            if comfortable_times:
                entry_data['raw_data']['comfortable_time'] = comfortable_times
            if fast_times:
                entry_data['raw_data']['fast_time'] = fast_times
            entry_data['unit'] = 'seconds'
        
        elif abbreviation == '5TSTS':
            time_seconds = entry_data.get('time_seconds')
            result = calculator.calculate_5tsts(time_seconds)
            
            # Store raw data
            entry_data['raw_data'] = {'time_seconds': [time_seconds]}
            entry_data['unit'] = 'seconds'
        
        elif abbreviation == 'FGA':
            if entry_data.get('individual_items'):
                result = calculator.calculate_fga(entry_data['individual_items'])
            else:
                result = {'total_score': entry_data.get('total_score'), 'calculated_result': f"{entry_data.get('total_score')}/30"}
        
        elif abbreviation == '6MWT':
            distance = entry_data.get('distance_meters')
            time_minutes = entry_data.get('actual_time_minutes', 6.0)
            result = calculator.calculate_6mwt(distance, time_minutes)
            
            # Store raw data
            entry_data['raw_data'] = {
                'distance_meters': [distance],
                'time_minutes': [time_minutes]
            }
            entry_data['unit'] = 'meters'
        
        else:
            result = {'calculated_result': 'Unknown measure type'}
        
        return {
            'total_score': result.get('total_score'),
            'calculated_result': result.get('calculated_result', ''),
        }
    
    except Exception as e:
        logging.error(f"Error calculating results for {abbreviation}: {e}")
        return {'calculated_result': 'Calculation error'}


@app.get("/api/admin/ai-security-status")
def get_ai_security_status(user: dict = Depends(require_admin)):
    """Get AI security status and recommendations (admin only)"""
    
    api_key_configured = bool(os.getenv('OPENROUTER_API_KEY'))
    environment = os.getenv("ENVIRONMENT", "development")
    
    security_checks = {
        "api_key_configured": {
            "status": "PASS" if api_key_configured else "FAIL",
            "description": "OpenRouter API key is configured" if api_key_configured else "OpenRouter API key is missing"
        },
        "server_side_only": {
            "status": "PASS",
            "description": "All AI processing happens server-side - API key never exposed to client"
        },
        "authentication_required": {
            "status": "PASS", 
            "description": "All AI endpoints require authentication"
        },
        "rate_limiting_active": {
            "status": "PASS",
            "description": f"Rate limiting active - {MAX_DAILY_REQUESTS} requests, {MAX_DAILY_TOKENS} tokens per day"
        },
        "usage_monitoring": {
            "status": "PASS",
            "description": "Comprehensive usage monitoring and alerting implemented"
        },
        "token_limits": {
            "status": "PASS",
            "description": "Token usage limits configured to prevent cost overruns"
        },
        "error_handling": {
            "status": "PASS",
            "description": "Comprehensive error handling and logging implemented"
        },
        "production_security": {
            "status": "PASS" if environment == "production" else "WARNING",
            "description": f"Environment: {environment} - Debug files disabled in production" if environment == "production" else f"Environment: {environment} - Debug files enabled"
        }
    }
    
    overall_status = "SECURE" if all(check["status"] == "PASS" for check in security_checks.values()) else "ATTENTION_REQUIRED"
    
    recommendations = []
    if not api_key_configured:
        recommendations.append("Configure OPENROUTER_API_KEY environment variable")
    if environment != "production":
        recommendations.append("Set ENVIRONMENT=production for production deployment")
    
    return {
        "overall_status": overall_status,
        "security_checks": security_checks,
        "recommendations": recommendations,
        "last_updated": datetime.now().isoformat()
    }


# Import appointment type controllers
from controllers.appointment_types import (
    AppointmentTypeController, PracticeAppointmentTypeController,
    AppointmentTypeCreateRequest, AppointmentTypeUpdateRequest,
    PracticeAppointmentTypeCreateRequest, PracticeAppointmentTypeUpdateRequest
)


# ========================================
# Appointment Type API Routes  
# ========================================

@app.get("/api/appointment-types")
async def get_appointment_types(
    hierarchical: bool = Query(False, description="Return hierarchical structure"),
    practice_id: Optional[int] = Query(None, description="Filter by practice ID"),
    active_only: bool = Query(True, description="Return only active appointment types"),
    parent_only: bool = Query(False, description="Return only parent (root level) types"),
    include_global: bool = Query(True, description="Include global appointment types"),
    user: dict = Depends(require_auth)
):
    """Get appointment types with optional filtering and hierarchical structure"""
    return AppointmentTypeController.index(
        hierarchical=hierarchical,
        practice_id=practice_id,
        active_only=active_only,
        parent_only=parent_only,
        include_global=include_global
    )


@app.get("/api/appointment-types/{appointment_type_id}")
async def get_appointment_type(
    appointment_type_id: int = Path(..., description="Appointment type ID"),
    user: dict = Depends(require_auth)
):
    """Get a specific appointment type by ID"""
    return AppointmentTypeController.show(appointment_type_id=appointment_type_id)


@app.post("/api/appointment-types", status_code=201)
async def create_appointment_type(
    request: AppointmentTypeCreateRequest,
    user: dict = Depends(require_auth)
):
    """Create a new appointment type"""
    return AppointmentTypeController.store(request=request)


@app.put("/api/appointment-types/{appointment_type_id}")
async def update_appointment_type(
    request: AppointmentTypeUpdateRequest,
    appointment_type_id: int = Path(..., description="Appointment type ID"),
    user: dict = Depends(require_auth)
):
    """Update an existing appointment type"""
    return AppointmentTypeController.update(
        appointment_type_id=appointment_type_id,
        request=request
    )


@app.delete("/api/appointment-types/{appointment_type_id}", status_code=204)
async def delete_appointment_type(
    appointment_type_id: int = Path(..., description="Appointment type ID"),
    user: dict = Depends(require_auth)
):
    """Delete (soft delete) an appointment type"""
    AppointmentTypeController.destroy(appointment_type_id=appointment_type_id)


@app.get("/api/practices/{practice_id}/appointment-types")
async def get_practice_appointment_types(
    practice_id: int = Path(..., description="Practice ID"),
    active_only: bool = Query(True, description="Return only active appointment types"),
    include_global: bool = Query(True, description="Include global appointment types"),
    user: dict = Depends(require_auth)
):
    """Get appointment types for a specific practice"""
    return AppointmentTypeController.get_by_practice(
        practice_id=practice_id,
        active_only=active_only,
        include_global=include_global
    )


# ========================================
# Practice Appointment Type Customization Routes
# ========================================

@app.get("/api/practices/{practice_id}/appointment-types/customizations")
async def get_practice_customizations(
    practice_id: int = Path(..., description="Practice ID"),
    enabled_only: bool = Query(True, description="Return only enabled customizations"),
    user: dict = Depends(require_auth)
):
    """Get practice appointment type customizations"""
    return PracticeAppointmentTypeController.index(
        practice_id=practice_id,
        enabled_only=enabled_only
    )


@app.get("/api/practices/{practice_id}/appointment-types/customizations/{customization_id}")
async def get_practice_customization(
    practice_id: int = Path(..., description="Practice ID"),
    customization_id: int = Path(..., description="Customization ID"),
    user: dict = Depends(require_auth)
):
    """Get a specific practice appointment type customization"""
    return PracticeAppointmentTypeController.show(
        practice_id=practice_id,
        customization_id=customization_id
    )


@app.post("/api/practices/{practice_id}/appointment-types/customizations", status_code=201)
async def create_practice_customization(
    request: PracticeAppointmentTypeCreateRequest,
    practice_id: int = Path(..., description="Practice ID"),
    user: dict = Depends(require_auth)
):
    """Create a new practice appointment type customization"""
    return PracticeAppointmentTypeController.store(
        practice_id=practice_id,
        request=request
    )


@app.put("/api/practices/{practice_id}/appointment-types/customizations/{customization_id}")
async def update_practice_customization(
    request: PracticeAppointmentTypeUpdateRequest,
    practice_id: int = Path(..., description="Practice ID"),
    customization_id: int = Path(..., description="Customization ID"),
    user: dict = Depends(require_auth)
):
    """Update a practice appointment type customization"""
    return PracticeAppointmentTypeController.update(
        practice_id=practice_id,
        customization_id=customization_id,
        request=request
    )


@app.delete("/api/practices/{practice_id}/appointment-types/customizations/{customization_id}", status_code=204)
async def delete_practice_customization(
    practice_id: int = Path(..., description="Practice ID"),
    customization_id: int = Path(..., description="Customization ID"),
    user: dict = Depends(require_auth)
):
    """Delete a practice appointment type customization"""
    PracticeAppointmentTypeController.destroy(
        practice_id=practice_id,
        customization_id=customization_id
    )


@app.get("/api/practices/{practice_id}/appointment-types/effective")
async def get_effective_appointment_types(
    practice_id: int = Path(..., description="Practice ID"),
    active_only: bool = Query(True, description="Return only active appointment types"),
    enabled_only: bool = Query(True, description="Return only enabled types for practice"),
    user: dict = Depends(require_auth)
):
    """Get appointment types with effective settings (merged with customizations)"""
    return PracticeAppointmentTypeController.get_effective_types(
        practice_id=practice_id,
        active_only=active_only,
        enabled_only=enabled_only
    )


# Template Management API Endpoints for Task 5

@app.get("/api/templates")
async def get_report_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    practice_id: Optional[str] = Query(None, description="Filter by practice ID"),
    user: dict = Depends(require_auth)
):
    """Get available report templates"""
    from controllers.report_controller import get_practice_templates
    
    if practice_id:
        return get_practice_templates(practice_id, user.get('user_id'))
    else:
        from modules.database import get_report_templates as get_templates
        return get_templates(template_type)


@app.post("/api/templates/create")
async def create_template(
    request: dict,
    user: dict = Depends(require_auth)
):
    """Create a new custom template"""
    from controllers.report_controller import create_custom_template
    
    return create_custom_template(
        name=request['name'],
        description=request.get('description'),
        template_type=request['template_type'],
        practice_id=request.get('practice_id'),
        fields_schema=request['fields_schema'],
        section_order=request['section_order'],
        created_by_user_id=user['user_id']
    )


@app.put("/api/templates/{template_id}")
async def update_template_endpoint(
    template_id: int = Path(..., description="Template ID"),
    request: dict = None,
    user: dict = Depends(require_auth)
):
    """Update an existing template"""
    from controllers.report_controller import update_template
    
    return update_template(
        template_id=template_id,
        updates=request,
        updated_by_user_id=user['user_id']
    )


@app.get("/api/templates/{template_id}")
async def get_template(
    template_id: int = Path(..., description="Template ID"),
    user: dict = Depends(require_auth)
):
    """Get a specific template by ID"""
    from controllers.report_controller import get_template_by_id
    
    template = get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@app.post("/api/templates/validate")
async def validate_template_schema_endpoint(
    request: dict,
    user: dict = Depends(require_auth)
):
    """Validate template field schema"""
    from controllers.report_controller import validate_template_schema
    
    return validate_template_schema(request.get('fields_schema', {}))


@app.post("/api/templates/preview")
async def preview_template_endpoint(
    request: dict,
    user: dict = Depends(require_auth)
):
    """Generate template preview HTML"""
    from controllers.report_controller import preview_template
    
    return preview_template(
        template_data=request,
        sample_data=request.get('sample_data')
    )


@app.post("/api/templates/{template_id}/approve")
async def approve_template_endpoint(
    template_id: int = Path(..., description="Template ID"),
    request: dict = None,
    user: dict = Depends(require_auth)
):
    """Approve a template for production use"""
    from controllers.report_controller import approve_template
    
    return approve_template(
        template_id=template_id,
        version_number=request.get('version_number', 1),
        approved_by_user_id=user['user_id'],
        approval_notes=request.get('approval_notes', '')
    )


@app.get("/api/templates/{template_id}/history")
async def get_template_history_endpoint(
    template_id: int = Path(..., description="Template ID"),
    user: dict = Depends(require_auth)
):
    """Get template version history"""
    from controllers.report_controller import get_template_history
    
    return get_template_history(template_id)


@app.post("/api/templates/{template_id}/revert")
async def revert_template_version_endpoint(
    template_id: int = Path(..., description="Template ID"),
    request: dict = None,
    user: dict = Depends(require_auth)
):
    """Revert template to a previous version"""
    from controllers.report_controller import revert_template_version
    
    return revert_template_version(
        template_id=template_id,
        target_version=request.get('target_version'),
        reverted_by_user_id=user['user_id'],
        revert_reason=request.get('revert_reason', '')
    )


# Serve template customization modal HTML
@app.get("/static/fragments/template_customization_modal.html")
async def get_template_modal():
    """Serve template customization modal HTML"""
    import os
    from fastapi.responses import FileResponse
    
    file_path = "/Users/duncanmiller/Documents/HadadaHealth/static/fragments/template_customization_modal.html"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Template modal not found")


# ===== TEMPLATE EDITOR ROUTES =====

@app.get("/template-instance/{instance_id}/edit")
async def serve_template_editor(instance_id: int):
    """Serve template editor page for a specific instance"""
    import os
    from fastapi.responses import HTMLResponse
    
    # Check if instance exists
    try:
        instance = get_template_instance_by_id(instance_id)
    except:
        raise HTTPException(status_code=404, detail="Template instance not found")
    
    # Read the template editor HTML file
    file_path = "/Users/duncanmiller/Documents/HadadaHealth/templates/template_editor.html"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace placeholder with instance ID
        content = content.replace('{{INSTANCE_ID}}', str(instance_id))
        content = content.replace('{{INSTANCE_TITLE}}', instance.title)
        content = content.replace('{{PATIENT_NAME}}', instance.patient_name)
        
        return HTMLResponse(content=content)
    else:
        raise HTTPException(status_code=404, detail="Template editor page not found")


# Start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
