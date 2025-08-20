"""
Reports and analytics functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime, timedelta
import sqlite3
from .database import get_db_connection, execute_query
from .therapists import get_therapist_stats
from .auth import get_user_statistics
from .medical_aids import get_medical_aids_statistics
from .outcome_measures import get_outcome_measures_statistics
from .professions_clinics import get_profession_clinic_statistics
from .reminders import get_reminders_statistics


# ===== DASHBOARD ANALYTICS =====

def get_dashboard_summary(user_id: Optional[int] = None, therapist_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get comprehensive dashboard summary combining data from all modules
    
    Args:
        user_id: Optional user ID for user-specific data
        therapist_id: Optional therapist ID for therapist-specific data
        
    Returns:
        Dashboard summary dictionary
    """
    summary = {}
    
    try:
        # Get statistics from all modules
        if user_id:
            summary['user_stats'] = get_user_statistics_safe(user_id)
            summary['reminder_stats'] = get_reminders_statistics(user_id)
        
        if therapist_id:
            therapist_stats = get_therapist_stats()
            summary['therapist_stats'] = next((s for s in therapist_stats if s.get('therapist_id') == therapist_id), {})
        
        # Get general statistics
        summary['medical_aid_stats'] = get_medical_aids_statistics()
        summary['outcome_measure_stats'] = get_outcome_measures_statistics()
        summary['profession_clinic_stats'] = get_profession_clinic_statistics()
        
        # Get appointment statistics
        summary['appointment_stats'] = get_appointment_statistics()
        
        # Get recent activity
        summary['recent_activity'] = get_recent_activity(user_id)
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {str(e)}")


def get_user_statistics_safe(user_id: int) -> Dict[str, Any]:
    """
    Get user statistics with error handling
    
    Args:
        user_id: User ID
        
    Returns:
        User statistics dictionary
    """
    try:
        # Create a mock request object for the auth module function
        class MockRequest:
            def __init__(self, user_id):
                self.session = {'user_id': user_id, 'role': 'Admin'}
        
        mock_request = MockRequest(user_id)
        return get_user_statistics(mock_request)
    except Exception:
        return {}


def get_appointment_statistics() -> Dict[str, Any]:
    """
    Get appointment-related statistics
    
    Returns:
        Appointment statistics dictionary
    """
    conn = get_db_connection()
    try:
        stats = {}
        
        # Total appointments
        total_result = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()
        stats['total_appointments'] = total_result[0] if total_result else 0
        
        # Appointments by status
        status_results = conn.execute("""
            SELECT status, COUNT(*) FROM bookings GROUP BY status
        """).fetchall()
        stats['appointments_by_status'] = {}
        for status, count in status_results:
            stats['appointments_by_status'][status or 'no_status'] = count
        
        # Appointments this month
        current_month = datetime.now().strftime('%Y-%m')
        monthly_result = conn.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE strftime('%Y-%m', date) = ?
        """, (current_month,)).fetchone()
        stats['appointments_this_month'] = monthly_result[0] if monthly_result else 0
        
        # Appointments this week
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        weekly_result = conn.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE date >= ?
        """, (week_ago,)).fetchone()
        stats['appointments_this_week'] = weekly_result[0] if weekly_result else 0
        
        # Appointments by profession
        profession_results = conn.execute("""
            SELECT profession, COUNT(*) FROM bookings 
            WHERE profession IS NOT NULL
            GROUP BY profession
            ORDER BY COUNT(*) DESC
        """).fetchall()
        stats['appointments_by_profession'] = {}
        for profession, count in profession_results:
            stats['appointments_by_profession'][profession] = count
        
        return stats
        
    finally:
        conn.close()


def get_recent_activity(user_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent activity across the system
    
    Args:
        user_id: Optional user ID to filter by
        limit: Maximum number of activities to return
        
    Returns:
        List of recent activity dictionaries
    """
    activities = []
    
    try:
        conn = get_db_connection()
        
        # Recent bookings
        booking_query = """
            SELECT 'booking' as type, date, time, patient_id, profession, therapist_id, timestamp as created_at
            FROM bookings 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        booking_results = conn.execute(booking_query, (limit,)).fetchall()
        
        for row in booking_results:
            activities.append({
                'type': 'booking',
                'title': f"Appointment booked - {row[3]} with {row[4]}",
                'date': row[1],
                'time': row[2],
                'patient_id': row[3],
                'profession': row[4],
                'therapist_id': row[5],
                'created_at': row[6]
            })
        
        # Recent treatment notes
        note_query = """
            SELECT 'treatment_note' as type, appointment_date, patient_id, profession, therapist_name, timestamp as created_at
            FROM treatment_notes 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        note_results = conn.execute(note_query, (limit,)).fetchall()
        
        for row in note_results:
            activities.append({
                'type': 'treatment_note',
                'title': f"Treatment note completed - {row[2]} by {row[4]}",
                'date': row[1],
                'patient_id': row[2],
                'profession': row[3],
                'therapist_name': row[4],
                'created_at': row[5]
            })
        
        # Recent reminders (if user_id provided)
        if user_id:
            reminder_query = """
                SELECT 'reminder' as type, title, due_date, patient_id, therapist_id, timestamp as created_at
                FROM reminders 
                WHERE created_by_user_id = ? OR visibility IN ('team', 'patient')
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            reminder_results = conn.execute(reminder_query, (user_id, limit)).fetchall()
            
            for row in reminder_results:
                activities.append({
                    'type': 'reminder',
                    'title': f"Reminder created: {row[1]}",
                    'due_date': row[2],
                    'patient_id': row[3],
                    'therapist_id': row[4],
                    'created_at': row[5]
                })
        
        conn.close()
        
        # Sort all activities by created_at and limit
        activities.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return activities[:limit]
        
    except Exception as e:
        return []


# ===== PATIENT REPORTS =====

def get_patient_summary_report(patient_id: int) -> Dict[str, Any]:
    """
    Get comprehensive patient summary report
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Patient summary report dictionary
    """
    conn = get_db_connection()
    try:
        report = {
            'patient_id': patient_id,
            'generated_at': datetime.now().isoformat(),
            'appointments': {},
            'treatment_notes': {},
            'outcome_measures': {},
            'reminders': {}
        }
        
        # Get patient appointments summary
        appointment_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_appointments,
                COUNT(CASE WHEN date < DATE('now') THEN 1 END) as past_appointments,
                COUNT(CASE WHEN date >= DATE('now') THEN 1 END) as future_appointments
            FROM bookings 
            WHERE patient_id = ?
        """, (str(patient_id),)).fetchone()
        
        if appointment_stats:
            report['appointments'] = {
                'total': appointment_stats[0],
                'past': appointment_stats[1],
                'future': appointment_stats[2]
            }
        
        # Get appointments by profession
        profession_stats = conn.execute("""
            SELECT profession, COUNT(*) 
            FROM bookings 
            WHERE patient_id = ? AND profession IS NOT NULL
            GROUP BY profession
        """, (str(patient_id),)).fetchall()
        
        report['appointments']['by_profession'] = {}
        for profession, count in profession_stats:
            report['appointments']['by_profession'][profession] = count
        
        # Get treatment notes summary
        notes_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_notes,
                COUNT(DISTINCT profession) as professions_seen,
                MIN(appointment_date) as first_appointment,
                MAX(appointment_date) as last_appointment
            FROM treatment_notes 
            WHERE patient_id = ?
        """, (str(patient_id),)).fetchone()
        
        if notes_stats:
            report['treatment_notes'] = {
                'total': notes_stats[0],
                'professions_seen': notes_stats[1],
                'first_appointment': notes_stats[2],
                'last_appointment': notes_stats[3]
            }
        
        # Get outcome measures for patient
        outcomes_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_measures,
                COUNT(DISTINCT outcome_measure_type_id) as measure_types_used
            FROM outcome_measures 
            WHERE patient_id = ?
        """, (str(patient_id),)).fetchone()
        
        if outcomes_stats:
            report['outcome_measures'] = {
                'total': outcomes_stats[0],
                'types_used': outcomes_stats[1]
            }
        
        # Get reminders for patient
        reminders_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_reminders,
                COUNT(CASE WHEN completed = 1 THEN 1 END) as completed_reminders,
                COUNT(CASE WHEN completed = 0 THEN 1 END) as pending_reminders
            FROM reminders 
            WHERE patient_id = ?
        """, (patient_id,)).fetchone()
        
        if reminders_stats:
            report['reminders'] = {
                'total': reminders_stats[0],
                'completed': reminders_stats[1],
                'pending': reminders_stats[2]
            }
        
        return report
        
    finally:
        conn.close()


def get_patient_profession_summary(patient_id: int, profession: str) -> Dict[str, Any]:
    """
    Get patient summary for a specific profession
    
    Args:
        patient_id: Patient ID
        profession: Profession name
        
    Returns:
        Patient profession summary dictionary
    """
    conn = get_db_connection()
    try:
        # Last session info with appointment_id and therapist_id for optional linking
        cursor = conn.execute("""
            SELECT appointment_date, start_time, therapist_name, appointment_id, therapist_id
            FROM treatment_notes
            WHERE patient_id = ? AND LOWER(profession) = LOWER(?)
            ORDER BY appointment_date DESC, start_time DESC
            LIMIT 1
        """, (str(patient_id), profession))
        
        row = cursor.fetchone()
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
        past_bookings_result = conn.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE patient_id = ? AND LOWER(profession) = LOWER(?) AND date < DATE('now')
        """, (str(patient_id), profession)).fetchone()
        past_bookings = past_bookings_result[0] if past_bookings_result else 0
        
        future_bookings_result = conn.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE patient_id = ? AND LOWER(profession) = LOWER(?) AND date >= DATE('now')
        """, (str(patient_id), profession)).fetchone()
        future_bookings = future_bookings_result[0] if future_bookings_result else 0

        return {
            "last_session": last_session,
            "appointment_id": appointment_id,
            "therapist_id": therapist_id,
            "past_bookings": past_bookings,
            "future_bookings": future_bookings
        }
        
    finally:
        conn.close()


def get_patient_ai_summary_data(patient_id: int) -> List[Dict[str, Any]]:
    """
    Get patient treatment notes data for AI summary generation
    
    Args:
        patient_id: Patient ID
        
    Returns:
        List of treatment note dictionaries for AI processing
    """
    query = """
        SELECT appointment_date, profession, subjective_findings, objective_findings, treatment, plan
        FROM treatment_notes
        WHERE patient_id = ?
        ORDER BY appointment_date DESC, start_time DESC
    """
    
    results = execute_query(query, (str(patient_id),), fetch='all')
    return [dict(row) for row in results] if results else []


def get_latest_note_summary(patient_id: str, profession: str) -> Optional[Dict[str, Any]]:
    """
    Get latest treatment note summary for patient and profession
    
    Args:
        patient_id: Patient ID
        profession: Profession name
        
    Returns:
        Latest treatment note summary dictionary or None
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
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
        if row:
            return {
                'appointment_date': row[0],
                'start_time': row[1],
                'duration': row[2],
                'therapist_name': row[3],
                'profession': row[4],
                'subjective_findings': row[5],
                'objective_findings': row[6],
                'treatment': row[7],
                'plan': row[8]
            }
        return None
        
    finally:
        conn.close()


# ===== SYSTEM REPORTS =====

def get_system_overview_report() -> Dict[str, Any]:
    """
    Get comprehensive system overview report
    
    Returns:
        System overview report dictionary
    """
    report = {
        'generated_at': datetime.now().isoformat(),
        'system_stats': {},
        'module_stats': {}
    }
    
    try:
        # Get basic system statistics
        conn = get_db_connection()
        
        # Count main entities
        stats = {}
        
        # Appointments
        appointments_result = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()
        stats['total_appointments'] = appointments_result[0] if appointments_result else 0
        
        # Treatment notes
        notes_result = conn.execute("SELECT COUNT(*) FROM treatment_notes").fetchone()
        stats['total_treatment_notes'] = notes_result[0] if notes_result else 0
        
        # Patients (unique patient_ids from bookings)
        patients_result = conn.execute("SELECT COUNT(DISTINCT patient_id) FROM bookings").fetchone()
        stats['total_patients'] = patients_result[0] if patients_result else 0
        
        # Therapists
        therapists_result = conn.execute("SELECT COUNT(*) FROM therapists").fetchone()
        stats['total_therapists'] = therapists_result[0] if therapists_result else 0
        
        report['system_stats'] = stats
        conn.close()
        
        # Get module-specific statistics
        report['module_stats'] = {
            'medical_aids': get_medical_aids_statistics(),
            'outcome_measures': get_outcome_measures_statistics(),
            'professions_clinics': get_profession_clinic_statistics(),
            'appointments': get_appointment_statistics()
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate system overview report: {str(e)}")


def get_therapist_performance_report(therapist_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get therapist performance report
    
    Args:
        therapist_id: Optional specific therapist ID
        
    Returns:
        Therapist performance report dictionary
    """
    therapist_stats = get_therapist_stats()
    
    if therapist_id:
        # Filter for specific therapist
        specific_stats = next((s for s in therapist_stats if s.get('therapist_id') == therapist_id), None)
        if not specific_stats:
            raise HTTPException(status_code=404, detail="Therapist not found")
        return {
            'generated_at': datetime.now().isoformat(),
            'therapist_id': therapist_id,
            'stats': specific_stats
        }
    else:
        # Return all therapist stats
        return {
            'generated_at': datetime.now().isoformat(),
            'all_therapists': therapist_stats
        }


def get_financial_summary_report(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get financial summary report
    
    Args:
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        
    Returns:
        Financial summary report dictionary
    """
    conn = get_db_connection()
    try:
        report = {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {}
        }
        
        # Build date filter
        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = "WHERE i.invoice_date BETWEEN ? AND ?"
            params = [start_date, end_date]
        elif start_date:
            date_filter = "WHERE i.invoice_date >= ?"
            params = [start_date]
        elif end_date:
            date_filter = "WHERE i.invoice_date <= ?"
            params = [end_date]
        
        # Get invoice statistics
        invoice_query = f"""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(i.amount) as total_amount,
                AVG(i.amount) as average_amount,
                MIN(i.amount) as min_amount,
                MAX(i.amount) as max_amount
            FROM invoices i
            {date_filter}
        """
        
        invoice_result = conn.execute(invoice_query, params).fetchone()
        if invoice_result:
            report['summary'] = {
                'total_invoices': invoice_result[0] or 0,
                'total_amount': invoice_result[1] or 0.0,
                'average_amount': invoice_result[2] or 0.0,
                'min_amount': invoice_result[3] or 0.0,
                'max_amount': invoice_result[4] or 0.0
            }
        
        # Get invoices by status
        status_query = f"""
            SELECT status, COUNT(*), SUM(amount)
            FROM invoices i
            {date_filter}
            GROUP BY status
        """
        
        status_results = conn.execute(status_query, params).fetchall()
        report['by_status'] = {}
        for status, count, amount in status_results:
            report['by_status'][status or 'no_status'] = {
                'count': count,
                'total_amount': amount or 0.0
            }
        
        return report
        
    finally:
        conn.close()


# ===== EXPORT FUNCTIONS =====

def export_patient_data(patient_id: int, format: str = 'json') -> Dict[str, Any]:
    """
    Export comprehensive patient data
    
    Args:
        patient_id: Patient ID
        format: Export format ('json' or 'csv')
        
    Returns:
        Exported patient data dictionary
    """
    if format not in ['json', 'csv']:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    # Get comprehensive patient data
    patient_data = {
        'patient_id': patient_id,
        'exported_at': datetime.now().isoformat(),
        'summary': get_patient_summary_report(patient_id),
        'treatment_notes': get_patient_ai_summary_data(patient_id)
    }
    
    # Add reminders for patient
    conn = get_db_connection()
    try:
        reminder_results = conn.execute("""
            SELECT title, description, due_date, priority, visibility, completed, completed_at, timestamp
            FROM reminders 
            WHERE patient_id = ?
            ORDER BY timestamp DESC
        """, (patient_id,)).fetchall()
        
        patient_data['reminders'] = [dict(row) for row in reminder_results]
        
        # Add outcome measures
        outcome_results = conn.execute("""
            SELECT om.*, omt.name as measure_type_name
            FROM outcome_measures om
            JOIN outcome_measure_types omt ON om.outcome_measure_type_id = omt.id
            WHERE om.patient_id = ?
            ORDER BY om.date DESC
        """, (str(patient_id),)).fetchall()
        
        patient_data['outcome_measures'] = [dict(row) for row in outcome_results]
        
    finally:
        conn.close()
    
    return patient_data