"""
Patient management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, UploadFile
import pandas as pd
import json
from .database import get_db_connection, execute_query
import sqlite3


def get_patient_by_id(patient_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a patient by ID
    
    Args:
        patient_id: The patient ID
        
    Returns:
        Patient data dictionary or None if not found
    """
    query = "SELECT * FROM patients WHERE id = ?"
    result = execute_query(query, (patient_id,), fetch='one')
    return dict(result) if result else None


def get_all_patients() -> List[Dict[str, Any]]:
    """
    Get all patients with their basic information
    
    Returns:
        List of patient dictionaries
    """
    query = """
        SELECT p.*, ma.name as medical_aid_name 
        FROM patients p
        LEFT JOIN medical_aids ma ON p.medical_aid_id = ma.id
        ORDER BY p.first_name, p.surname
    """
    results = execute_query(query, fetch='all')
    return [dict(row) for row in results] if results else []


def create_patient(patient_data: Dict[str, Any]) -> int:
    """
    Create a new patient
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        The ID of the newly created patient
        
    Raises:
        HTTPException: If creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Extract and prepare patient data
        fields = [
            'first_name', 'surname', 'date_of_birth', 'gender', 'phone_number',
            'email', 'address', 'emergency_contact_name', 'emergency_contact_phone',
            'medical_aid_id', 'medical_aid_number', 'icd10_codes', 'clinic'
        ]
        
        # Build dynamic query
        available_fields = [f for f in fields if f in patient_data and patient_data[f] is not None]
        placeholders = ', '.join(['?' for _ in available_fields])
        field_names = ', '.join(available_fields)
        values = [patient_data[f] for f in available_fields]
        
        query = f"INSERT INTO patients ({field_names}) VALUES ({placeholders})"
        cursor.execute(query, values)
        patient_id = cursor.lastrowid
        conn.commit()
        
        return patient_id
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")
    finally:
        conn.close()


def update_patient(patient_id: int, patient_data: Dict[str, Any]) -> bool:
    """
    Update an existing patient
    
    Args:
        patient_id: The patient ID to update
        patient_data: Dictionary containing updated patient information
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If update fails
    """
    conn = get_db_connection()
    try:
        # Check if patient exists
        existing = get_patient_by_id(patient_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Build update query
        fields = [
            'first_name', 'surname', 'date_of_birth', 'gender', 'phone_number',
            'email', 'address', 'emergency_contact_name', 'emergency_contact_phone',
            'medical_aid_id', 'medical_aid_number', 'icd10_codes', 'clinic'
        ]
        
        update_fields = [f for f in fields if f in patient_data]
        if not update_fields:
            return True  # No fields to update
            
        set_clause = ', '.join([f"{field} = ?" for field in update_fields])
        values = [patient_data[field] for field in update_fields] + [patient_id]
        
        query = f"UPDATE patients SET {set_clause} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update patient: {str(e)}")
    finally:
        conn.close()


def delete_patient(patient_id: int) -> bool:
    """
    Delete a patient
    
    Args:
        patient_id: The patient ID to delete
        
    Returns:
        True if successful
        
    Raises:
        HTTPException: If deletion fails
    """
    conn = get_db_connection()
    try:
        # Check if patient exists
        existing = get_patient_by_id(patient_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
            
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete patient: {str(e)}")
    finally:
        conn.close()


def get_patient_alerts(patient_id: str) -> List[Dict[str, Any]]:
    """
    Get alerts for a specific patient
    
    Args:
        patient_id: The patient ID
        
    Returns:
        List of alert dictionaries
    """
    query = """
        SELECT tn.*, b.name as patient_name, b.date, b.time
        FROM treatment_notes tn
        LEFT JOIN bookings b ON tn.appointment_id = b.id
        WHERE tn.patient_id = ? AND tn.alert_resolved != 'Yes'
        ORDER BY b.date DESC, b.time DESC
    """
    
    results = execute_query(query, (patient_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def get_patient_medical_history(patient_id: int) -> Optional[str]:
    """
    Get medical history summary for a patient
    
    Args:
        patient_id: The patient ID
        
    Returns:
        Medical history summary string or None
    """
    query = "SELECT medical_history_summary FROM patients WHERE id = ?"
    result = execute_query(query, (patient_id,), fetch='one')
    return result[0] if result else None


def update_patient_medical_history(patient_id: int, summary: str) -> bool:
    """
    Update medical history summary for a patient
    
    Args:
        patient_id: The patient ID
        summary: The medical history summary
        
    Returns:
        True if successful
    """
    query = "UPDATE patients SET medical_history_summary = ? WHERE id = ?"
    execute_query(query, (summary, patient_id))
    return True


def get_patient_professions(patient_id: int) -> List[str]:
    """
    Get list of professions that have treated this patient
    
    Args:
        patient_id: The patient ID
        
    Returns:
        List of profession names
    """
    query = """
        SELECT DISTINCT t.profession 
        FROM bookings b
        JOIN therapists t ON b.therapist_id = t.id
        WHERE b.patient_id = ?
        ORDER BY t.profession
    """
    
    results = execute_query(query, (patient_id,), fetch='all')
    return [row[0] for row in results] if results else []


def get_patient_bookings(patient_id: int) -> List[Dict[str, Any]]:
    """
    Get all bookings for a patient
    
    Args:
        patient_id: The patient ID
        
    Returns:
        List of booking dictionaries
    """
    query = """
        SELECT b.*, t.name as therapist_name, t.profession
        FROM bookings b
        LEFT JOIN therapists t ON b.therapist_id = t.id
        WHERE b.patient_id = ?
        ORDER BY b.date DESC, b.time DESC
    """
    
    results = execute_query(query, (patient_id,), fetch='all')
    return [dict(row) for row in results] if results else []


def import_patients_from_excel(file: UploadFile) -> Dict[str, Any]:
    """
    Import patients from Excel file
    
    Args:
        file: The uploaded Excel file
        
    Returns:
        Import results summary
        
    Raises:
        HTTPException: If import fails
    """
    try:
        # Read Excel file
        df = pd.read_excel(file.file)
        
        # Validate required columns
        required_columns = ['first_name', 'surname']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Convert row to dict and handle NaN values
                patient_data = row.to_dict()
                patient_data = {k: (v if pd.notna(v) else None) for k, v in patient_data.items()}
                
                # Handle ICD10 codes if present
                if 'icd10_codes' in patient_data and patient_data['icd10_codes']:
                    if isinstance(patient_data['icd10_codes'], str):
                        # Convert comma-separated string to JSON array
                        codes = [code.strip() for code in patient_data['icd10_codes'].split(',')]
                        patient_data['icd10_codes'] = json.dumps(codes)
                
                create_patient(patient_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return {
            "imported_count": imported_count,
            "total_rows": len(df),
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")


def resolve_patient_alert(patient_id: str, appointment_id: str, resolved: bool) -> bool:
    """
    Resolve or unresolve a patient alert
    
    Args:
        patient_id: The patient ID
        appointment_id: The appointment ID
        resolved: Whether the alert is resolved
        
    Returns:
        True if successful
    """
    query = """
        UPDATE treatment_notes
        SET alert_resolved = ?
        WHERE patient_id = ? AND appointment_id = ?
    """
    
    execute_query(query, ("Yes" if resolved else "No", patient_id, appointment_id))
    return True