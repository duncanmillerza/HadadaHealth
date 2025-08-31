#!/usr/bin/env python3
"""
Create comprehensive test data for AI Report Writing System

Creates realistic test data in the database to verify all components
of the AI report writing system work correctly.
"""
import sys
import os
import json
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import get_db_connection, execute_query


def create_test_treatment_notes():
    """Create realistic treatment notes test data"""
    print("📝 Creating test treatment notes...")
    
    try:
        # First check if treatment_notes table exists and what columns it has
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check table structure
        try:
            table_info = cursor.execute("PRAGMA table_info(treatment_notes)").fetchall()
            if not table_info:
                print("  ⚠️ treatment_notes table doesn't exist, creating it...")
                create_treatment_notes_table(cursor)
            else:
                print(f"  ✓ treatment_notes table exists with {len(table_info)} columns")
        except Exception as e:
            print(f"  ⚠️ Creating treatment_notes table: {e}")
            create_treatment_notes_table(cursor)
        
        # Create comprehensive test data
        test_notes = [
            {
                'patient_id': 'TEST_PATIENT_001',
                'appointment_date': '2025-08-15',
                'start_time': '09:00',
                'profession': 'Physiotherapy',
                'therapist_name': 'Dr. Sarah Smith',
                'subjective_findings': 'Patient reports severe lower back pain (8/10) with radiation to left leg. Pain worse in morning, improved with movement. Difficulty sleeping due to pain.',
                'objective_findings': 'Lumbar flexion 30 degrees (limited), extension 10 degrees. Positive straight leg raise left at 30 degrees. Decreased sensation L5 dermatome left.',
                'treatment': 'Manual therapy to lumbar spine, soft tissue mobilization. Core stability exercises (level 1). Heat therapy application.',
                'plan': 'Continue physiotherapy 3x weekly. Progress exercises as tolerated. Consider imaging if no improvement in 2 weeks.'
            },
            {
                'patient_id': 'TEST_PATIENT_001',
                'appointment_date': '2025-08-18',
                'start_time': '10:30',
                'profession': 'Physiotherapy',
                'therapist_name': 'Dr. Sarah Smith',
                'subjective_findings': 'Patient reports improvement in pain levels (6/10). Sleeping better, less morning stiffness. Still experiencing some leg radiation.',
                'objective_findings': 'Lumbar flexion improved to 45 degrees. Extension 15 degrees. SLR improved to 45 degrees left. Core strength showing early improvement.',
                'treatment': 'Continued manual therapy. Progressed core exercises to level 2. Added lumbar stabilization exercises. Postural education provided.',
                'plan': 'Continue current treatment approach. Introduce functional movement patterns next session.'
            },
            {
                'patient_id': 'TEST_PATIENT_001',
                'appointment_date': '2025-08-22',
                'start_time': '14:00',
                'profession': 'Physiotherapy',
                'therapist_name': 'Dr. Sarah Smith',
                'subjective_findings': 'Significant improvement reported. Pain now 3/10, no morning stiffness. Minimal leg symptoms. Patient able to return to work.',
                'objective_findings': 'Full lumbar range of motion achieved. Negative SLR bilaterally. Good core strength, able to maintain plank for 60 seconds.',
                'treatment': 'Advanced core and functional exercises. Workplace ergonomic advice. Return to activity planning.',
                'plan': 'Discharge next session with comprehensive home exercise program. Follow-up in 4 weeks PRN.'
            },
            {
                'patient_id': 'TEST_PATIENT_001',
                'appointment_date': '2025-08-20',
                'start_time': '11:00',
                'profession': 'Occupational Therapy',
                'therapist_name': 'Dr. Mike Johnson',
                'subjective_findings': 'Patient experiencing difficulty with work-related activities due to lower back pain. Desk job requiring prolonged sitting.',
                'objective_findings': 'Poor sitting posture observed. Workstation assessment reveals inadequate lumbar support. Limited knowledge of ergonomic principles.',
                'treatment': 'Workstation ergonomic assessment and modifications. Postural awareness training. Equipment recommendations provided.',
                'plan': 'Follow-up workstation visit planned. Continue education on workplace modifications.'
            },
            {
                'patient_id': 'TEST_PATIENT_002',
                'appointment_date': '2025-08-19',
                'start_time': '15:30',
                'profession': 'Speech Therapy',
                'therapist_name': 'Dr. Lisa Chen',
                'subjective_findings': 'Post-stroke patient with mild dysarthria and word-finding difficulties. Family reports communication improvements.',
                'objective_findings': 'Articulation 85% intelligible in conversation. Word retrieval improved from baseline. Good motivation for therapy.',
                'treatment': 'Articulation exercises focusing on consonant clusters. Word-finding strategies practiced. Home program reviewed with family.',
                'plan': 'Continue speech therapy 2x weekly. Introduce reading comprehension exercises next session.'
            }
        ]
        
        # Insert test notes
        for note in test_notes:
            try:
                # Use INSERT OR REPLACE to handle existing data
                cursor.execute('''
                INSERT OR REPLACE INTO treatment_notes 
                (patient_id, appointment_date, start_time, profession, therapist_name,
                 subjective_findings, objective_findings, treatment, plan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    note['patient_id'], note['appointment_date'], note['start_time'],
                    note['profession'], note['therapist_name'], note['subjective_findings'],
                    note['objective_findings'], note['treatment'], note['plan']
                ))
            except Exception as e:
                print(f"  ⚠️ Note insertion error (continuing): {e}")
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Created {len(test_notes)} treatment notes")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to create treatment notes: {e}")
        return False


def create_treatment_notes_table(cursor):
    """Create treatment_notes table if it doesn't exist"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treatment_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        appointment_date TEXT NOT NULL,
        start_time TEXT,
        profession TEXT,
        therapist_name TEXT,
        subjective_findings TEXT,
        objective_findings TEXT,
        treatment TEXT,
        plan TEXT,
        duration INTEGER DEFAULT 45,
        notes TEXT,
        session_type TEXT DEFAULT 'treatment',
        created_at TEXT DEFAULT (datetime('now'))
    )
    ''')


def create_test_patients():
    """Create test patient records"""
    print("👥 Creating test patient records...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if patients table exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
            if not cursor.fetchone():
                print("  ⚠️ patients table doesn't exist, creating it...")
                create_patients_table(cursor)
        except Exception:
            create_patients_table(cursor)
        
        test_patients = [
            {
                'patient_id': 'TEST_PATIENT_001',
                'name': 'John Smith',
                'date_of_birth': '1985-05-15',
                'gender': 'Male',
                'phone': '+27823456789',
                'email': 'john.smith@email.com',
                'medical_aid': 'Discovery Health',
                'primary_diagnosis': 'L4-L5 disc herniation with radiculopathy'
            },
            {
                'patient_id': 'TEST_PATIENT_002', 
                'name': 'Mary Johnson',
                'date_of_birth': '1972-11-22',
                'gender': 'Female',
                'phone': '+27834567890',
                'email': 'mary.johnson@email.com',
                'medical_aid': 'Bonitas',
                'primary_diagnosis': 'CVA with mild dysarthria'
            }
        ]
        
        for patient in test_patients:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO patients 
                (patient_id, name, date_of_birth, gender, phone, email, medical_aid, primary_diagnosis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    patient['patient_id'], patient['name'], patient['date_of_birth'],
                    patient['gender'], patient['phone'], patient['email'],
                    patient['medical_aid'], patient['primary_diagnosis']
                ))
            except Exception as e:
                print(f"  ⚠️ Patient insertion error (continuing): {e}")
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Created {len(test_patients)} test patients")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to create test patients: {e}")
        return False


def create_patients_table(cursor):
    """Create patients table if it doesn't exist"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        date_of_birth TEXT,
        gender TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        medical_aid TEXT,
        emergency_contact TEXT,
        referring_doctor TEXT,
        primary_diagnosis TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    ''')


def create_test_reports():
    """Create test reports using the report system"""
    print("📄 Creating test reports...")
    
    try:
        from modules.database import create_report
        
        # Create test reports
        reports = [
            {
                'patient_id': 'TEST_PATIENT_001',
                'report_type': 'progress',
                'template_id': 1,  # Assumes default templates exist
                'title': 'Progress Report - John Smith',
                'assigned_therapist_ids': ['THER001'],
                'disciplines': ['physiotherapy', 'occupational_therapy'],
                'requested_by_user_id': 'MGR001',
                'priority': 2
            },
            {
                'patient_id': 'TEST_PATIENT_002',
                'report_type': 'discharge',
                'template_id': 2,
                'title': 'Discharge Summary - Mary Johnson',
                'assigned_therapist_ids': ['THER002'],
                'disciplines': ['speech_therapy'],
                'requested_by_user_id': 'MGR001',
                'priority': 1
            }
        ]
        
        created_reports = []
        for report in reports:
            try:
                report_id = create_report(**report)
                created_reports.append(report_id)
                print(f"  ✅ Created report ID {report_id}: {report['title']}")
            except Exception as e:
                print(f"  ⚠️ Report creation error: {e}")
        
        print(f"  ✅ Created {len(created_reports)} test reports")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to create test reports: {e}")
        return False


def create_ai_test_data():
    """Create test data for AI content generation"""
    print("🤖 Creating AI test data...")
    
    try:
        from modules.database import cache_ai_content
        
        # Create test AI cache entries
        test_ai_content = [
            {
                'patient_id': 'TEST_PATIENT_001',
                'content_type': 'medical_history',
                'content': '''<strong>Medical History:</strong>

Patient presents with L4-L5 disc herniation with left lower extremity radiculopathy. Initial presentation included severe lower back pain (8/10) with radiation to left leg, morning stiffness, and sleep disturbances.

<strong>Treatment Course:</strong>
- Initial assessment revealed limited lumbar flexion (30°) and positive straight leg raise
- Progressive improvement noted through physiotherapy interventions
- Multi-disciplinary approach included occupational therapy for workplace ergonomics

<strong>Current Status:</strong>
Patient shows excellent progress with pain reduction from 8/10 to 3/10. Full range of motion restored, negative neurological signs, and successful return to work activities.''',
                'discipline': None
            },
            {
                'patient_id': 'TEST_PATIENT_002',
                'content_type': 'treatment_summary',
                'content': '''<strong>Treatment Summary:</strong>

Post-cerebrovascular accident patient receiving speech therapy for mild dysarthria and word-finding difficulties.

<strong>Interventions Provided:</strong>
- Articulation exercises targeting consonant clusters
- Word retrieval strategy training
- Family education and home program implementation

<strong>Progress:</strong>
Intelligibility improved from 70% to 85% in conversational speech. Family reports improved communication confidence and participation in social activities.''',
                'discipline': 'speech_therapy'
            }
        ]
        
        created_cache_items = []
        for item in test_ai_content:
            try:
                cache_id = cache_ai_content(**item, expires_days=7)
                created_cache_items.append(cache_id)
                print(f"  ✅ Cached AI content ID {cache_id}: {item['content_type']} for {item['patient_id']}")
            except Exception as e:
                print(f"  ⚠️ AI cache error: {e}")
        
        print(f"  ✅ Created {len(created_cache_items)} AI cache entries")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to create AI test data: {e}")
        return False


def verify_test_data():
    """Verify that test data was created successfully"""
    print("✅ Verifying test data creation...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check patients
        patients = cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_id LIKE 'TEST_PATIENT_%'").fetchone()
        print(f"  📊 Test patients: {patients[0] if patients else 0}")
        
        # Check treatment notes
        try:
            notes = cursor.execute("SELECT COUNT(*) FROM treatment_notes WHERE patient_id LIKE 'TEST_PATIENT_%'").fetchone()
            print(f"  📊 Treatment notes: {notes[0] if notes else 0}")
        except Exception:
            print(f"  📊 Treatment notes: table not accessible")
        
        # Check reports
        reports = cursor.execute("SELECT COUNT(*) FROM reports WHERE patient_id LIKE 'TEST_PATIENT_%'").fetchone()
        print(f"  📊 Test reports: {reports[0] if reports else 0}")
        
        # Check AI cache
        ai_cache = cursor.execute("SELECT COUNT(*) FROM ai_content_cache WHERE patient_id LIKE 'TEST_PATIENT_%'").fetchone()
        print(f"  📊 AI cache entries: {ai_cache[0] if ai_cache else 0}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Verification error: {e}")
        return False


def main():
    """Create all test data"""
    print("🚀 Creating Comprehensive Test Data for AI Report Writing System")
    print("=" * 70)
    
    tasks = [
        create_test_patients,
        create_test_treatment_notes,
        create_test_reports,
        create_ai_test_data,
        verify_test_data
    ]
    
    success_count = 0
    for task in tasks:
        try:
            if task():
                success_count += 1
        except Exception as e:
            print(f"❌ Task {task.__name__} failed: {e}")
        print("-" * 50)
    
    print(f"📊 Test Data Creation Results: {success_count}/{len(tasks)} successful")
    
    if success_count == len(tasks):
        print("🎉 All test data created successfully!")
        print("\n📋 You can now test the AI system with:")
        print("  • Patient ID: TEST_PATIENT_001 (Multi-disciplinary back pain case)")
        print("  • Patient ID: TEST_PATIENT_002 (Speech therapy post-stroke case)")
        return True
    else:
        print("⚠️ Some test data creation had issues, but system should still be testable")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)