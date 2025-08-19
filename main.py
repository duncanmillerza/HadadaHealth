"""
HadadaHealth - Practice Management System
Main application file with organized module imports
"""

# Standard library imports
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any

# Third-party imports
import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Request, Response, Query, Body, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Local module imports
from modules import auth, patients, billing, appointments, database

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="HadadaHealth", description="Practice Management System")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "SUPER_SECRET_KEY"))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")

# Security setup
security = HTTPBasic()


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.post("/signup")
def signup(
    username: str = Body(...),
    password: str = Body(...),
    role: str = Body(...),
    permissions: List[str] = Body(default=[])
):
    """User signup endpoint"""
    return auth.create_user(username, password, role, permissions)


@app.post("/create-user")
def create_user(
    username: str = Body(...),
    password: str = Body(...),
    role: str = Body(...),
    permissions: List[str] = Body(default=[]),
    linked_therapist_id: int = Body(default=None)
):
    """Create user endpoint with therapist linking"""
    return auth.create_user(username, password, role, permissions, linked_therapist_id)


@app.post("/login")
def login(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    """User login endpoint"""
    return auth.login_user(request, credentials)


@app.get("/logout")
def logout(request: Request, response: Response):
    """User logout endpoint"""
    return auth.logout_user(request, response)


@app.get("/check-login")
def check_login(request: Request):
    """Check if user is logged in"""
    return auth.check_login_status(request)


@app.get("/users")
def get_users():
    """Get all users"""
    return auth.get_users()


@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    username: str = Body(default=None),
    password: str = Body(default=None),
    role: str = Body(default=None),
    permissions: List[str] = Body(default=None),
    linked_therapist_id: int = Body(default=None)
):
    """Update user endpoint"""
    return auth.update_user(user_id, username, password, role, permissions, linked_therapist_id)


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete user endpoint"""
    return auth.delete_user(user_id)


# ============================================================================
# PATIENT ROUTES
# ============================================================================

@app.post("/patients")
def save_patient(patient: patients.Patient, request: Request):
    """Save a new patient"""
    return patients.save_patient(patient, request)


@app.get("/patients")
def get_patients():
    """Get all patients"""
    return patients.get_patients()


@app.get("/api/patient/{patient_id}")
def get_patient(patient_id: int):
    """Get specific patient by ID"""
    return patients.get_patient_by_id(patient_id)


@app.put("/update-patient/{patient_id}")
def update_patient(patient_id: int, updates: Dict[str, Any] = Body(...)):
    """Update patient information"""
    return patients.update_patient(patient_id, updates)


@app.delete("/delete-patient/{patient_id}")
def delete_patient(patient_id: int):
    """Delete a patient"""
    return patients.delete_patient(patient_id)


@app.get("/api/patient/{patient_id}/alerts")
def get_patient_alerts(patient_id: str):
    """Get alerts for a patient"""
    return patients.get_patient_alerts(patient_id)


@app.put("/api/patient/{patient_id}/alerts/{appointment_id}/resolve")
def toggle_alert_resolution(patient_id: str, appointment_id: str, payload: dict = Body(...)):
    """Toggle alert resolution status"""
    return patients.toggle_alert_resolution(patient_id, appointment_id, payload)


@app.get("/api/patient/{patient_id}/medical-history")
def get_patient_medical_history(patient_id: int):
    """Get patient's medical history"""
    return patients.get_patient_medical_history(patient_id)


@app.post("/api/patient/{patient_id}/medical-history/regenerate")
async def regenerate_medical_history(patient_id: int):
    """Regenerate AI medical history for patient"""
    return await patients.generate_medical_history_ai(patient_id)


@app.get("/api/patient/{patient_id}/professions")
def get_patient_professions(patient_id: int):
    """Get professions that have treated this patient"""
    return patients.get_patient_professions(patient_id)


@app.get("/api/patient/{patient_id}/bookings")
def get_patient_bookings(patient_id: int):
    """Get all bookings for a patient"""
    return patients.get_patient_bookings(patient_id)


@app.post("/import-patients")
def import_patients(file: UploadFile = File(...)):
    """Import patients from CSV file"""
    return patients.import_patients_csv(file)


# ============================================================================
# BILLING ROUTES
# ============================================================================

@app.post("/billing-sessions")
def create_billing_session(data: dict, request: Request):
    """Create a new billing session"""
    return billing.create_billing_session(data, request)


@app.post("/submit-billing")
def submit_billing(data: dict):
    """Submit billing data"""
    return billing.submit_billing(data)


@app.get("/api/billing_codes")
def get_billing_codes():
    """Get all billing codes"""
    return billing.get_billing_codes()


@app.get("/api/billing-codes")
def get_billing_codes_api(profession: Optional[str] = Query(None)):
    """Get billing codes with optional profession filter"""
    if profession:
        return billing.get_billing_codes_for_profession(profession)
    return billing.get_billing_codes()


@app.get("/billing-codes-for-profession")
def get_billing_codes_for_profession(profession: str = Query(...)):
    """Get billing codes for a specific profession"""
    return billing.get_billing_codes_for_profession(profession)


@app.get("/api/billing_modifiers")
def get_billing_modifiers():
    """Get all billing modifiers"""
    return billing.get_billing_modifiers()


@app.put("/billing-codes/{code_id}")
def update_billing_code(code_id: int, updates: Dict[str, Any] = Body(...)):
    """Update a billing code"""
    return billing.update_billing_code(code_id, updates)


@app.delete("/billing-codes/{code_id}")
def delete_billing_code(code_id: int):
    """Delete a billing code"""
    return billing.delete_billing_code(code_id)


@app.get("/billing-sessions/{patient_id}")
def get_billing_sessions(patient_id: int):
    """Get billing sessions for a patient"""
    return billing.get_billing_sessions(patient_id)


@app.post("/complete-billing/{booking_id}")
def complete_billing(booking_id: int):
    """Mark billing as completed for a booking"""
    return billing.complete_billing(booking_id)


@app.get("/api/unbilled-treatment-notes")
def get_unbilled_treatment_notes():
    """Get treatment notes that haven't been billed"""
    return billing.get_unbilled_treatment_notes()


@app.post("/api/billing-for-appointment")
def create_billing_for_appointment(appointment_data: dict = Body(...)):
    """Create billing for a specific appointment"""
    return billing.create_billing_for_appointment(appointment_data)


# Invoice endpoints
@app.get("/invoices")
def get_invoices():
    """Get all invoices"""
    return billing.get_invoices()


@app.post("/invoices")
def create_invoice(invoice_data: dict = Body(...)):
    """Create a new invoice"""
    return billing.create_invoice(invoice_data)


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    """Get specific invoice by ID"""
    return billing.get_invoice_by_id(invoice_id)


@app.put("/invoices/{invoice_id}")
def update_invoice(invoice_id: int, updates: Dict[str, Any] = Body(...)):
    """Update an invoice"""
    return billing.update_invoice(invoice_id, updates)


@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int):
    """Delete an invoice"""
    return billing.delete_invoice(invoice_id)


@app.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int):
    """Generate PDF for an invoice"""
    pdf_content = billing.generate_invoice_pdf(invoice_id)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"}
    )


# ============================================================================
# APPOINTMENT/BOOKING ROUTES
# ============================================================================

@app.get("/bookings")
def get_bookings(
    therapist_id: Optional[int] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None)
):
    """Get all bookings, optionally filtered by therapist and date range"""
    return appointments.get_bookings(therapist_id, start, end)


@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str):
    """Get specific booking by ID"""
    return appointments.get_booking_by_id(booking_id)


@app.post("/bookings")
def create_booking(booking: appointments.Booking):
    """Create a new booking"""
    return appointments.create_booking(booking)


@app.put("/bookings/{booking_id}")
def update_booking(booking_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a booking"""
    return appointments.update_booking(booking_id, updates)


@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    """Delete a booking"""
    return appointments.delete_booking(booking_id)


@app.get("/bookings-for-day-for-therapists")
def get_bookings_for_day_for_therapists(
    date: str = Query(...),
    therapist_ids: str = Query(...)
):
    """Get bookings for specific therapists on a specific day"""
    therapist_id_list = [int(id.strip()) for id in therapist_ids.split(',') if id.strip()]
    return appointments.get_bookings_for_day_for_therapists(date, therapist_id_list)


@app.get("/session-info")
def get_session_info(request: Request):
    """Get session information for current user"""
    return appointments.get_session_info(request)


@app.get("/therapist-stats")
def get_therapist_stats():
    """Get statistics for all therapists"""
    return appointments.get_therapist_stats()


@app.get("/api/check-treatment-notes")
def check_treatment_notes(ids: str = Query(..., description="Comma separated appointment IDs")):
    """Check which appointments have treatment notes"""
    appointment_ids = [id.strip() for id in ids.split(',') if id.strip()]
    return appointments.check_treatment_notes(appointment_ids)


@app.get("/api/check-treatment-note/{appointment_id}")
def check_treatment_note(appointment_id: str):
    """Check if specific appointment has treatment note"""
    return appointments.check_treatment_note(appointment_id)


@app.get("/api/treatment-notes/full/{appointment_id}")
def get_treatment_note_full(appointment_id: str):
    """Get full treatment note for an appointment"""
    return appointments.get_treatment_note_full(appointment_id)


# ============================================================================
# STATIC PAGE ROUTES (with authentication)
# ============================================================================

@app.get("/")
def serve_index(request: Request):
    """Main dashboard route with authentication"""
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return FileResponse(os.path.join("templates", "index.html"))


def require_auth(request: Request):
    """Helper function to check authentication"""
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return None


@app.get("/add-patient-page")
def serve_add_patient_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "add-patient.html"))


@app.get("/therapists-page")
def serve_therapists_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "therapists.html"))


@app.get("/week-calendar-page")
def serve_week_calendar_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "week-calendar.html"))


@app.get("/patient-profile-page")
def serve_patient_profile_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "Patient Profile.html"))


@app.get("/medical-aid-page")
def serve_medical_aid_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "medical-aid.html"))


@app.get("/billing-page")
def serve_billing_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "billing.html"))


@app.get("/treatment-notes-page")
def serve_treatment_notes_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "treatment-notes.html"))


@app.get("/patient-dash-page")
def serve_patient_dash_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "Patient Dash.html"))


@app.get("/test-calendar-page")
def serve_test_calendar_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "test-calendar.html"))


@app.get("/patients-page")
def serve_patients_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "patients.html"))


@app.get("/settings-page")
def serve_settings_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "settings.html"))


@app.get("/manage-users-page")
def serve_manage_users_page(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "manage-users.html"))


@app.get("/therapist-calendar")
def serve_therapist_calendar(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "therapist-calendar.html"))


@app.get("/mdt-calendar")
def serve_mdt_calendar(request: Request):
    auth_response = require_auth(request)
    if auth_response:
        return auth_response
    return FileResponse(os.path.join("templates", "mdt-calendar.html"))


@app.get("/login-page")
def serve_login_page():
    """Serve login page"""
    return FileResponse(os.path.join("templates", "login.html"))


@app.get("/favicon.ico")
def favicon():
    """Serve favicon"""
    return FileResponse(os.path.join("static", "favicon.ico"))


# ============================================================================
# REMAINING ENDPOINTS (to be organized into modules later)
# ============================================================================

# Note: The following endpoints still need to be organized into appropriate modules
# This includes therapists management, medical aids, settings, treatment notes, etc.
# For now, they remain as placeholder endpoints to maintain functionality

# TODO: Create therapists.py module
# TODO: Create medical_aids.py module  
# TODO: Create settings.py module
# TODO: Create treatment_notes.py module
# TODO: Create outcome_measures.py module

# Placeholder endpoints
@app.get("/therapists")
def get_therapists():
    """Get all therapists - TODO: move to therapists module"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        therapists = cursor.execute("SELECT * FROM therapists ORDER BY name").fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, therapist)) for therapist in therapists]


@app.get("/medical_aids")
def get_medical_aids():
    """Get all medical aids - TODO: move to medical_aids module"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        aids = cursor.execute("SELECT DISTINCT name FROM medical_aids ORDER BY name").fetchall()
        return [aid[0] for aid in aids]


@app.get("/medical_aids_full")
def get_medical_aids_full():
    """Get all medical aids with full details"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        aids = cursor.execute("SELECT * FROM medical_aids ORDER BY name").fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, aid)) for aid in aids]


@app.get("/settings")
def get_settings():
    """Get application settings"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        settings = cursor.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        if not settings:
            # Return default settings if none exist
            return {
                "start_time": "08:00",
                "end_time": "17:00", 
                "slot_duration": 15,
                "weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "dark_mode": False,
                "billing_mode": "therapist"
            }
        
        return {
            "id": settings[0],
            "start_time": settings[1],
            "end_time": settings[2],
            "slot_duration": settings[3],
            "weekdays": settings[4].split(",") if settings[4] else [],
            "dark_mode": bool(settings[5]),
            "billing_mode": settings[6]
        }


@app.get("/therapist/{therapist_id}")
def get_therapist(therapist_id: int):
    """Get specific therapist by ID"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        therapist = cursor.execute("SELECT * FROM therapists WHERE id = ?", (therapist_id,)).fetchone()
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, therapist))


@app.get("/reminders")
def get_reminders():
    """Get all reminders"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        reminders = cursor.execute("SELECT * FROM reminders ORDER BY due_date").fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, reminder)) for reminder in reminders]


@app.post("/reminders")
def create_reminder(data: dict = Body(...)):
    """Create a new reminder"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (title, description, due_date, colour, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.get("title", ""),
            data.get("description", ""),
            data.get("due_date"),
            data.get("colour", "#2D6356"),
            data.get("priority", "normal")
        ))
        conn.commit()
    return {"detail": "Reminder created successfully"}


@app.post("/submit-treatment-note")
def submit_treatment_note(note: dict = Body(...)):
    """Submit a treatment note"""
    required_fields = [
        "appointment_id", "appointment_date", "start_time", "duration", "patient_name",
        "patient_id", "profession", "therapist_name", "therapist_id",
        "subjective_findings", "objective_findings", "treatment", "plan", "note_to_patient"
    ]

    for field in required_fields:
        if field not in note:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    with database.get_db_connection() as conn:
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


@app.get("/api/patient/{patient_id}/summary/{profession}")
def get_patient_summary(patient_id: int, profession: str):
    """Get patient summary for specific profession"""
    return patients.get_patient_summary(patient_id, profession)


@app.get("/api/patient/{patient_id}/summary/{profession}/latest")
def get_patient_summary_latest(patient_id: int, profession: str, appointment_id: Optional[str] = Query(None)):
    """Get latest patient summary for specific profession"""
    return patients.get_patient_summary(patient_id, profession)


@app.get("/api/patient/{patient_id}/latest-session-note/{profession}")
def get_latest_session_note(patient_id: int, profession: str):
    """Get latest session note for patient and profession"""
    return patients.get_latest_session_note(patient_id, profession)


@app.get("/api/patient/{patient_id}/summary/ai")
def get_patient_ai_summary(patient_id: int):
    """Get AI-generated patient summary"""
    return patients.get_patient_ai_summary(patient_id)


@app.post("/api/treatment-notes/{booking_id}/supplementary_note")
def add_supplementary_note(booking_id: str, note_data: dict = Body(...)):
    """Add supplementary note to existing treatment note"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO supplementary_notes (appointment_id, user_id, note, timestamp)
            VALUES (?, ?, ?, ?)
        """, (booking_id, 1, note_data.get("note", ""), datetime.utcnow().isoformat()))
        conn.commit()
    return {"detail": "Supplementary note added successfully"}


@app.get("/api/outcome-measure-types/categories")
def get_outcome_measure_categories():
    """Get outcome measure categories"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        categories = cursor.execute("""
            SELECT DISTINCT category FROM outcome_measure_types 
            ORDER BY category
        """).fetchall()
        return [cat[0] for cat in categories if cat[0]]


@app.get("/api/outcome-measures")
def get_outcome_measures(patient_id: Optional[int] = Query(None)):
    """Get outcome measures, optionally filtered by patient"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        if patient_id:
            measures = cursor.execute("""
                SELECT om.*, omt.name as measure_name, omt.category
                FROM outcome_measures om
                JOIN outcome_measure_types omt ON om.measure_type_id = omt.id
                WHERE om.patient_id = ?
                ORDER BY om.date_administered DESC
            """, (patient_id,)).fetchall()
        else:
            measures = cursor.execute("""
                SELECT om.*, omt.name as measure_name, omt.category
                FROM outcome_measures om
                JOIN outcome_measure_types omt ON om.measure_type_id = omt.id
                ORDER BY om.date_administered DESC
            """).fetchall()
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, measure)) for measure in measures]


# More endpoints would be added here...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)