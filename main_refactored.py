"""
HadadaHealth FastAPI Application - Refactored
Clean, organized version with modular structure
"""

# Standard library imports
import json
import logging
import os
from datetime import datetime
from typing import List, Optional

# Third-party imports
import pandas as pd
from dotenv import load_dotenv
from fastapi import (
    FastAPI, HTTPException, Depends, Request, Query, Body, 
    UploadFile, File, Form
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from starlette.middleware.sessions import SessionMiddleware

# Local module imports
from modules.database import get_db_connection
from modules.auth import (
    login_user, logout_user, check_login_status, serve_login_page,
    require_auth, require_admin, security
)
from modules.patients import (
    get_all_patients, get_patient_by_id, create_patient, 
    update_patient, delete_patient, get_patient_alerts,
    import_patients_from_excel, resolve_patient_alert,
    get_patient_medical_history, get_patient_professions,
    get_patient_bookings
)
from modules.billing import (
    get_billing_codes, get_billing_codes_for_profession,
    get_billing_modifiers, create_billing_session,
    submit_billing, get_billing_sessions, get_all_invoices,
    create_invoice, get_invoice_by_id, update_invoice,
    delete_invoice, generate_invoice_pdf, update_billing_code,
    delete_billing_code, complete_appointment_billing,
    get_billing_for_appointment
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="HadadaHealth",
    description="Healthcare practice management system",
    version="2.0.0"
)

# Add middleware
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === ROUTE DEFINITIONS ===

@app.get("/favicon.ico")
async def favicon():
    """Silence favicon 404s"""
    return Response(status_code=204)

# === AUTHENTICATION ROUTES ===

@app.post("/login")
def login(request: Request, credentials=Depends(security)):
    """User login endpoint"""
    return login_user(request, credentials)

@app.get("/login-page")
def login_page():
    """Serve login page"""
    return serve_login_page()

@app.get("/logout")
def logout(request: Request, response: Response):
    """User logout endpoint"""
    return logout_user(request, response)

@app.get("/check-login")
def check_login(request: Request):
    """Check login status"""
    return check_login_status(request)

# === PATIENT ROUTES ===

@app.get("/patients")
def get_patients():
    """Get all patients"""
    return get_all_patients()

@app.post("/patients")
def create_new_patient(patient_data: dict):
    """Create a new patient"""
    patient_id = create_patient(patient_data)
    return {"id": patient_id, "message": "Patient created successfully"}

@app.put("/update-patient/{patient_id}")
def update_existing_patient(patient_id: int, patient_data: dict):
    """Update an existing patient"""
    success = update_patient(patient_id, patient_data)
    return {"success": success, "message": "Patient updated successfully"}

@app.delete("/delete-patient/{patient_id}")
def delete_existing_patient(patient_id: int):
    """Delete a patient"""
    success = delete_patient(patient_id)
    return {"success": success, "message": "Patient deleted successfully"}

@app.get("/api/patient/{patient_id}")
def get_patient_details(patient_id: int):
    """Get patient details by ID"""
    patient = get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.get("/api/patient/{patient_id}/alerts")
def get_patient_alerts_endpoint(patient_id: str):
    """Get alerts for a patient"""
    return get_patient_alerts(patient_id)

@app.put("/api/patient/{patient_id}/alerts/{appointment_id}/resolve")
def resolve_alert(patient_id: str, appointment_id: str, payload: dict = Body(...)):
    """Resolve or unresolve a patient alert"""
    resolved = payload.get("resolved", False)
    if isinstance(resolved, str):
        resolved = resolved.lower() == "true"
    
    success = resolve_patient_alert(patient_id, appointment_id, resolved)
    return {"status": "updated", "success": success}

@app.get("/api/patient/{patient_id}/professions")
def get_patient_professions_endpoint(patient_id: int):
    """Get professions that have treated this patient"""
    return get_patient_professions(patient_id)

@app.get("/api/patient/{patient_id}/bookings")
def get_patient_bookings_endpoint(patient_id: int):
    """Get all bookings for a patient"""
    return get_patient_bookings(patient_id)

@app.post("/import-patients")
def import_patients(file: UploadFile = File(...)):
    """Import patients from Excel file"""
    return import_patients_from_excel(file)

# === BILLING ROUTES ===

@app.get("/api/billing_codes")
def get_billing_codes_endpoint():
    """Get all billing codes"""
    return get_billing_codes()

@app.get("/billing-codes-for-profession")
def get_billing_codes_for_profession_endpoint(profession: str = Query(...)):
    """Get billing codes for specific profession"""
    return get_billing_codes_for_profession(profession)

@app.get("/api/billing_modifiers")
def get_billing_modifiers_endpoint():
    """Get all billing modifiers"""
    return get_billing_modifiers()

@app.post("/billing-sessions")
def create_billing_session_endpoint(data: dict):
    """Create a new billing session"""
    session_id = create_billing_session(data)
    return {"id": session_id, "message": "Billing session created successfully"}

@app.post("/submit-billing")
def submit_billing_endpoint(data: dict):
    """Submit billing for an appointment"""
    success = submit_billing(data)
    return {"success": success, "message": "Billing submitted successfully"}

@app.get("/billing-sessions/{patient_id}")
def get_patient_billing_sessions(patient_id: int):
    """Get billing sessions for a patient"""
    return get_billing_sessions(patient_id)

@app.get("/invoices")
def get_invoices():
    """Get all invoices"""
    return get_all_invoices()

@app.post("/invoices")
def create_new_invoice(invoice_data: dict):
    """Create a new invoice"""
    invoice_id = create_invoice(invoice_data)
    return {"id": invoice_id, "message": "Invoice created successfully"}

@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    """Get invoice by ID"""
    invoice = get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@app.put("/invoices/{invoice_id}")
def update_existing_invoice(invoice_id: int, invoice_data: dict):
    """Update an existing invoice"""
    success = update_invoice(invoice_id, invoice_data)
    return {"success": success, "message": "Invoice updated successfully"}

@app.delete("/invoices/{invoice_id}")
def delete_existing_invoice(invoice_id: int):
    """Delete an invoice"""
    success = delete_invoice(invoice_id)
    return {"success": success, "message": "Invoice deleted successfully"}

@app.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int):
    """Generate and download invoice PDF"""
    pdf_buffer = generate_invoice_pdf(invoice_id)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"}
    )

@app.put("/billing-codes/{code_id}")
def update_existing_billing_code(code_id: int, code_data: dict):
    """Update a billing code"""
    success = update_billing_code(code_id, code_data)
    return {"success": success, "message": "Billing code updated successfully"}

@app.delete("/billing-codes/{code_id}")
def delete_existing_billing_code(code_id: int):
    """Delete a billing code"""
    success = delete_billing_code(code_id)
    return {"success": success, "message": "Billing code deleted successfully"}

@app.post("/complete-billing/{booking_id}")
def complete_billing(booking_id: int):
    """Mark appointment billing as completed"""
    success = complete_appointment_billing(booking_id)
    return {"success": success, "message": "Billing completed successfully"}

@app.post("/api/billing-for-appointment")
def get_appointment_billing(data: dict = Body(...)):
    """Get billing entries for an appointment"""
    appointment_id = data.get('appointment_id')
    if not appointment_id:
        raise HTTPException(status_code=400, detail="appointment_id required")
    return get_billing_for_appointment(appointment_id)

# === PAGE ROUTES ===

@app.get("/")
def serve_index():
    """Serve main dashboard page"""
    return FileResponse("templates/index.html")

@app.get("/patients-page")
def serve_patients_page():
    """Serve patients page"""
    return FileResponse("templates/patients.html")

@app.get("/add-patient-page")
def serve_add_patient_page():
    """Serve add patient page"""
    return FileResponse("templates/add-patient.html")

@app.get("/billing-page")
def serve_billing_page():
    """Serve billing page"""
    return FileResponse("templates/billing.html")

@app.get("/week-calendar-page")
def serve_calendar_page():
    """Serve weekly calendar page"""
    return FileResponse("templates/week-calendar.html")

# === ERROR HANDLERS ===

@app.exception_handler(404)
def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return {"error": "Not found", "detail": str(exc.detail)}

@app.exception_handler(500)
def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    logging.error(f"Internal server error: {exc.detail}")
    return {"error": "Internal server error", "detail": "An unexpected error occurred"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)