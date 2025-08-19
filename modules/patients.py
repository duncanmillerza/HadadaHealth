"""
Patient management module for HadadaHealth
"""
import sqlite3
import pandas as pd
import httpx
import json
import os
from typing import List, Optional, Dict, Any
from fastapi import Request, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv

from .database import get_db_connection

load_dotenv()


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


def save_patient(patient: Patient, request: Request):
    """Save a new patient to the database"""
    therapist_id = request.session.get("linked_therapist_id")
    if hasattr(patient, "therapist_id") and getattr(patient, "therapist_id", None):
        therapist_id = getattr(patient, "therapist_id")

    with get_db_connection() as conn:
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
            patient.first_name, patient.surname, patient.preferred_name, patient.date_of_birth,
            patient.gender, patient.id_number, patient.address_line1, patient.address_line2,
            patient.town, patient.postal_code, patient.country, patient.email, patient.contact_number,
            patient.clinic, patient.account_name, patient.account_id_number, patient.account_address,
            patient.account_phone, patient.account_email, patient.funding_option, patient.main_member_name,
            patient.medical_aid_name, patient.medical_aid_other, patient.plan_name, patient.medical_aid_number,
            patient.dependent_number, patient.alternative_funding_source, patient.alternative_funding_other,
            patient.claim_number, patient.case_manager, patient.patient_important_info,
            patient.consent_treatment, patient.consent_photography, patient.consent_data,
            patient.consent_communication, patient.consent_billing, patient.consent_terms,
            patient.signature_identity, patient.signature_name, patient.signature_relationship, 
            patient.signature_data
        ))
    return {"detail": "Patient saved"}


def update_patient(patient_id: int, updates: Dict[str, Any]):
    """Update patient information"""
    with get_db_connection() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        
        for field, value in updates.items():
            update_fields.append(f"{field} = ?")
            params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(patient_id)
        query = f"UPDATE patients SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
    
    return {"detail": "Patient updated successfully"}


def get_patients():
    """Get all patients"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        patients = cursor.execute("""
            SELECT id, first_name, surname, preferred_name, date_of_birth, gender,
                   email, contact_number, medical_aid_name, plan_name
            FROM patients
            ORDER BY surname, first_name
        """).fetchall()
        
        return [
            {
                "id": p[0], "first_name": p[1], "surname": p[2], "preferred_name": p[3],
                "date_of_birth": p[4], "gender": p[5], "email": p[6], "contact_number": p[7],
                "medical_aid_name": p[8], "plan_name": p[9]
            }
            for p in patients
        ]


def get_patient_by_id(patient_id: int):
    """Get a specific patient by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        patient = cursor.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Convert to dict for easier handling
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, patient))


def delete_patient(patient_id: int):
    """Delete a patient"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
    
    return {"detail": "Patient deleted successfully"}


def get_patient_alerts(patient_id: str):
    """Get alerts for a patient"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        alerts = cursor.execute("""
            SELECT b.id as appointment_id, b.date, b.time, b.patient_name as name,
                   t.name as therapist_name, t.profession,
                   CASE WHEN tn.appointment_id IS NULL THEN 0 ELSE 1 END as has_note,
                   b.billing_completed,
                   COALESCE(ra.resolved, 0) as alert_resolved
            FROM bookings b
            JOIN therapists t ON b.therapist_id = t.id
            LEFT JOIN treatment_notes tn ON b.id = tn.appointment_id
            LEFT JOIN resolved_alerts ra ON b.id = ra.appointment_id AND ra.patient_id = ?
            WHERE b.patient_id = ? AND b.date < date('now')
              AND (tn.appointment_id IS NULL OR b.billing_completed = 0)
            ORDER BY b.date DESC, b.time DESC
        """, (patient_id, patient_id)).fetchall()
        
        return [
            {
                "appointment_id": alert[0], "date": alert[1], "time": alert[2], "name": alert[3],
                "therapist_name": alert[4], "profession": alert[5], "has_note": bool(alert[6]),
                "billing_completed": bool(alert[7]), "alert_resolved": bool(alert[8])
            }
            for alert in alerts
        ]


def toggle_alert_resolution(patient_id: str, appointment_id: str, payload: dict):
    """Toggle alert resolution status"""
    resolved = payload.get("resolved", False)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO resolved_alerts (patient_id, appointment_id, resolved)
            VALUES (?, ?, ?)
        """, (patient_id, appointment_id, resolved))
        
    return {"detail": "Alert resolution status updated"}


async def generate_medical_history_ai(patient_id: int):
    """Generate AI medical history summary for a patient"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all treatment notes for the patient
            notes = cursor.execute("""
                SELECT tn.full_text, b.date, t.profession
                FROM treatment_notes tn
                JOIN bookings b ON tn.appointment_id = b.id
                JOIN therapists t ON b.therapist_id = t.id
                WHERE b.patient_id = ?
                ORDER BY b.date ASC
            """, (patient_id,)).fetchall()
            
            if not notes:
                return {"medical_history": "No treatment notes available"}
            
            # Combine all notes
            combined_notes = "\n\n".join([
                f"Date: {note[1]}, Profession: {note[2]}\n{note[0]}" 
                for note in notes
            ])
            
            # Call AI API
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-3.5-sonnet",
                        "messages": [
                            {"role": "user", "content": f"Please extract the medical history and level of function from the following notes:\n{combined_notes}. Never make anything up, only use the information provided. If there is not enough information, say 'No information available'. For headings please use html strong text"}
                        ]
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    medical_history = result['choices'][0]['message']['content']
                    
                    # Store in database
                    cursor.execute("""
                        INSERT OR REPLACE INTO patient_medical_history (patient_id, medical_history)
                        VALUES (?, ?)
                    """, (patient_id, medical_history))
                    
                    return {"medical_history": medical_history}
                else:
                    raise HTTPException(status_code=500, detail=f"AI API error: {response.text}")
                    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating medical history: {str(e)}")


def get_patient_medical_history(patient_id: int):
    """Get patient's medical history"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            "SELECT medical_history FROM patient_medical_history WHERE patient_id = ?",
            (patient_id,)
        ).fetchone()
        
        if result:
            return {"medical_history": result[0]}
        else:
            return {"medical_history": "No medical history available"}


def get_patient_professions(patient_id: int):
    """Get professions that have treated this patient"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        professions = cursor.execute("""
            SELECT DISTINCT t.profession
            FROM bookings b
            JOIN therapists t ON b.therapist = t.id
            WHERE b.patient_id = ?
        """, (patient_id,)).fetchall()
        
        return [p[0] for p in professions]


def get_patient_bookings(patient_id: int):
    """Get all bookings for a patient"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        bookings = cursor.execute("""
            SELECT b.*, t.name as therapist_name, t.profession
            FROM bookings b
            JOIN therapists t ON b.therapist = t.id
            WHERE b.patient_id = ?
            ORDER BY b.date DESC, b.time DESC
        """, (patient_id,)).fetchall()
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, booking)) for booking in bookings]


def import_patients_csv(file: UploadFile):
    """Import patients from CSV file"""
    try:
        # Read the uploaded file
        df = pd.read_csv(file.file)
        
        # Validate required columns
        required_columns = ['first_name', 'surname', 'date_of_birth', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        with get_db_connection() as conn:
            for index, row in df.iterrows():
                try:
                    # Insert patient with available data
                    conn.execute("""
                        INSERT INTO patients (first_name, surname, preferred_name, date_of_birth, 
                                            gender, email, contact_number, medical_aid_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('first_name', ''),
                        row.get('surname', ''),
                        row.get('preferred_name', ''),
                        row.get('date_of_birth', ''),
                        row.get('gender', ''),
                        row.get('email', ''),
                        row.get('contact_number', ''),
                        row.get('medical_aid_name', '')
                    ))
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
        
        result = {"imported": imported_count}
        if errors:
            result["errors"] = errors
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importing patients: {str(e)}")


def get_patient_summary(patient_id: int, profession: str):
    """Get patient summary for specific profession"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get latest treatment notes for this profession
        notes = cursor.execute("""
            SELECT subjective_findings, objective_findings, treatment, plan
            FROM treatment_notes 
            WHERE patient_id = ? AND profession = ?
            ORDER BY note_completed_at DESC
            LIMIT 5
        """, (patient_id, profession)).fetchall()
        
        if not notes:
            return {"summary": "No treatment history found for this profession."}
        
        # Simple summary generation from notes
        summary_parts = []
        for note in notes:
            if note[0]:  # subjective_findings
                summary_parts.append(f"Subjective: {note[0]}")
            if note[1]:  # objective_findings  
                summary_parts.append(f"Objective: {note[1]}")
            if note[2]:  # treatment
                summary_parts.append(f"Treatment: {note[2]}")
            if note[3]:  # plan
                summary_parts.append(f"Plan: {note[3]}")
        
        return {"summary": " | ".join(summary_parts[:3]) if summary_parts else "No detailed notes available."}


def get_latest_session_note(patient_id: int, profession: str):
    """Get latest session note for patient and profession"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        note = cursor.execute("""
            SELECT * FROM treatment_notes 
            WHERE patient_id = ? AND profession = ?
            ORDER BY note_completed_at DESC
            LIMIT 1
        """, (patient_id, profession)).fetchone()
        
        if not note:
            return {"note": "No session notes found for this profession."}
        
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, note))


def get_patient_ai_summary(patient_id: int):
    """Get AI-generated patient summary"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get existing AI summary from medical history
        summary = cursor.execute("""
            SELECT summary, generated_at FROM medical_history
            WHERE patient_id = ?
            ORDER BY generated_at DESC
            LIMIT 1
        """, (patient_id,)).fetchone()
        
        if not summary:
            return {"summary": "No AI summary available. Please generate medical history first."}
        
        return {"summary": summary[0], "generated_at": summary[1]}