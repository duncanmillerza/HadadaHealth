#!/usr/bin/env python3
"""
Database integration tests for AI Report Writing System

Tests the complete database schema for reports, templates, AI content cache,
notifications, and all related functionality.
"""
import sys
import os
import sqlite3
import json
import time
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import get_db_connection, execute_query


def setup_test_tables():
    """Create test tables for report writing system"""
    print("🔧 Setting up test tables...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create reports table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            template_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_by_user_id TEXT,
            assigned_therapist_ids TEXT NOT NULL,
            deadline_date TEXT,
            disciplines TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            completed_at TEXT,
            content TEXT,
            ai_generated_sections TEXT,
            last_ai_generation_date TEXT,
            notes TEXT,
            CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue')),
            CHECK (priority IN (1, 2, 3))
        )
        ''')
        
        # Create report_templates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            template_type TEXT NOT NULL,
            practice_id TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_system_default BOOLEAN DEFAULT 0,
            fields_schema TEXT NOT NULL,
            section_order TEXT NOT NULL,
            created_by_user_id TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            version INTEGER DEFAULT 1,
            CHECK (template_type IN ('discharge', 'progress', 'insurance', 'outcome_summary', 'assessment', 'custom'))
        )
        ''')
        
        # Create report_content_versions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_content_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            ai_generated_sections TEXT,
            created_by_user_id TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            change_summary TEXT,
            is_ai_generated BOOLEAN DEFAULT 0,
            FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
            UNIQUE (report_id, version_number)
        )
        ''')
        
        # Create ai_content_cache table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_content_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            content_type TEXT NOT NULL,
            discipline TEXT,
            content TEXT NOT NULL,
            source_data_hash TEXT NOT NULL,
            generated_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used_at TEXT,
            is_valid BOOLEAN DEFAULT 1,
            CHECK (content_type IN ('medical_history', 'treatment_summary', 'assessment_summary', 'outcome_summary'))
        )
        ''')
        
        # Create report_notifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            read_at TEXT,
            FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
            CHECK (notification_type IN ('request', 'reminder', 'completion', 'overdue'))
        )
        ''')
        
        conn.commit()
        print("✅ Test tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test tables: {e}")
        return False
    finally:
        conn.close()


def test_reports_table_operations():
    """Test reports table CRUD operations"""
    print("🧪 Testing reports table operations...")
    
    try:
        # Test creating a report
        unique_title = f"Test Progress Report {int(time.time())}"
        report_data = {
            'patient_id': 'PAT001',
            'report_type': 'progress',
            'template_id': 1,
            'title': unique_title,
            'assigned_therapist_ids': '["THER001", "THER002"]',
            'disciplines': '["physiotherapy", "occupational_therapy"]',
            'deadline_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'requested_by_user_id': 'MGR001',
            'priority': 2
        }
        
        # Insert test report
        insert_query = '''
        INSERT INTO reports (patient_id, report_type, template_id, title, assigned_therapist_ids, 
                           disciplines, deadline_date, requested_by_user_id, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, (
            report_data['patient_id'], report_data['report_type'], report_data['template_id'],
            report_data['title'], report_data['assigned_therapist_ids'], report_data['disciplines'],
            report_data['deadline_date'], report_data['requested_by_user_id'], report_data['priority']
        ))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Test retrieving the report
        report = execute_query(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
            fetch='one'
        )
        
        assert report is not None
        assert report['title'] == unique_title
        assert report['patient_id'] == 'PAT001'
        assert report['status'] == 'pending'  # Default value
        assert report['priority'] == 2
        
        # Test updating report status
        execute_query(
            "UPDATE reports SET status = ?, updated_at = datetime('now') WHERE id = ?",
            ('in_progress', report_id)
        )
        
        updated_report = execute_query(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
            fetch='one'
        )
        
        assert updated_report['status'] == 'in_progress'
        
        print("✅ Reports table operations successful")
        return True
        
    except Exception as e:
        print(f"❌ Reports table operations failed: {e}")
        return False


def test_report_templates_table_operations():
    """Test report templates table operations"""
    print("🧪 Testing report templates table operations...")
    
    try:
        unique_name = f"Test Template {int(time.time())}"
        fields_schema = json.dumps({
            "patient_info": {"type": "auto", "required": True},
            "medical_history": {"type": "ai_paragraph", "required": True, "editable": True},
            "assessment_findings": {"type": "paragraph", "required": True}
        })
        section_order = json.dumps(["patient_info", "medical_history", "assessment_findings"])
        
        # Insert test template
        template_data = (
            unique_name,
            "Test template for progress reports",
            "progress",
            "PRAC001",
            1,  # is_active
            0,  # is_system_default
            fields_schema,
            section_order,
            "USER001"
        )
        
        insert_query = '''
        INSERT INTO report_templates (name, description, template_type, practice_id, 
                                    is_active, is_system_default, fields_schema, 
                                    section_order, created_by_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, template_data)
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Test retrieving the template
        template = execute_query(
            "SELECT * FROM report_templates WHERE id = ?",
            (template_id,),
            fetch='one'
        )
        
        assert template is not None
        assert template['name'] == unique_name
        assert template['template_type'] == 'progress'
        assert template['is_active'] == 1
        assert json.loads(template['fields_schema'])['medical_history']['type'] == 'ai_paragraph'
        
        print("✅ Report templates table operations successful")
        return True
        
    except Exception as e:
        print(f"❌ Report templates table operations failed: {e}")
        return False


def test_ai_content_cache_operations():
    """Test AI content cache table operations"""
    print("🧪 Testing AI content cache operations...")
    
    try:
        # Test caching medical history
        cache_data = {
            'patient_id': 'PAT001',
            'content_type': 'medical_history',
            'discipline': 'physiotherapy',
            'content': 'Patient presents with chronic lower back pain...',
            'source_data_hash': 'abc123def456',
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        insert_query = '''
        INSERT INTO ai_content_cache (patient_id, content_type, discipline, content, 
                                    source_data_hash, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, (
            cache_data['patient_id'], cache_data['content_type'], cache_data['discipline'],
            cache_data['content'], cache_data['source_data_hash'], cache_data['expires_at']
        ))
        cache_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Test retrieving cached content
        cached_content = execute_query(
            "SELECT * FROM ai_content_cache WHERE id = ?",
            (cache_id,),
            fetch='one'
        )
        
        assert cached_content is not None
        assert cached_content['patient_id'] == 'PAT001'
        assert cached_content['content_type'] == 'medical_history'
        assert cached_content['usage_count'] == 0
        assert cached_content['is_valid'] == 1
        
        # Test updating usage count
        execute_query(
            "UPDATE ai_content_cache SET usage_count = usage_count + 1, last_used_at = datetime('now') WHERE id = ?",
            (cache_id,)
        )
        
        updated_cache = execute_query(
            "SELECT * FROM ai_content_cache WHERE id = ?",
            (cache_id,),
            fetch='one'
        )
        
        assert updated_cache['usage_count'] == 1
        assert updated_cache['last_used_at'] is not None
        
        print("✅ AI content cache operations successful")
        return True
        
    except Exception as e:
        print(f"❌ AI content cache operations failed: {e}")
        return False


def test_foreign_key_relationships():
    """Test foreign key relationships and referential integrity"""
    print("🧪 Testing foreign key relationships...")
    
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Create a test report first
        cursor.execute('''
        INSERT INTO reports (patient_id, report_type, template_id, title, assigned_therapist_ids, disciplines)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ('PAT002', 'assessment', 1, 'Test FK Report', '["THER001"]', '["physiotherapy"]'))
        
        report_id = cursor.lastrowid
        
        # Create report content version
        cursor.execute('''
        INSERT INTO report_content_versions (report_id, version_number, content, created_by_user_id)
        VALUES (?, ?, ?, ?)
        ''', (report_id, 1, '{"section1": "content"}', 'USER001'))
        
        # Create notification
        cursor.execute('''
        INSERT INTO report_notifications (report_id, user_id, notification_type, message)
        VALUES (?, ?, ?, ?)
        ''', (report_id, 'USER001', 'request', 'New report requested'))
        
        conn.commit()
        
        # Test that related records exist
        versions = cursor.execute(
            "SELECT COUNT(*) FROM report_content_versions WHERE report_id = ?",
            (report_id,)
        ).fetchone()[0]
        
        notifications = cursor.execute(
            "SELECT COUNT(*) FROM report_notifications WHERE report_id = ?",
            (report_id,)
        ).fetchone()[0]
        
        assert versions == 1
        assert notifications == 1
        
        # Test cascade delete
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
        
        # Verify related records are deleted
        versions_after = cursor.execute(
            "SELECT COUNT(*) FROM report_content_versions WHERE report_id = ?",
            (report_id,)
        ).fetchone()[0]
        
        notifications_after = cursor.execute(
            "SELECT COUNT(*) FROM report_notifications WHERE report_id = ?",
            (report_id,)
        ).fetchone()[0]
        
        assert versions_after == 0
        assert notifications_after == 0
        
        conn.close()
        
        print("✅ Foreign key relationships working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Foreign key relationship test failed: {e}")
        return False


def test_json_data_handling():
    """Test JSON data storage and retrieval"""
    print("🧪 Testing JSON data handling...")
    
    try:
        # Test storing and retrieving JSON data in reports
        json_content = {
            "patient_demographics": {
                "name": "John Doe",
                "age": 45,
                "diagnosis": "Lower back pain"
            },
            "assessment": {
                "findings": "Limited range of motion",
                "pain_score": 7
            }
        }
        
        disciplines_json = ["physiotherapy", "occupational_therapy"]
        ai_sections_json = ["medical_history", "treatment_summary"]
        
        # Insert report with JSON data
        insert_query = '''
        INSERT INTO reports (patient_id, report_type, template_id, title, assigned_therapist_ids,
                           disciplines, content, ai_generated_sections)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, (
            'PAT003',
            'progress',
            1,
            'JSON Test Report',
            '["THER001"]',
            json.dumps(disciplines_json),
            json.dumps(json_content),
            json.dumps(ai_sections_json)
        ))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Retrieve and verify JSON data
        report = execute_query(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
            fetch='one'
        )
        
        retrieved_content = json.loads(report['content'])
        retrieved_disciplines = json.loads(report['disciplines'])
        retrieved_ai_sections = json.loads(report['ai_generated_sections'])
        
        assert retrieved_content['patient_demographics']['name'] == "John Doe"
        assert retrieved_disciplines == disciplines_json
        assert retrieved_ai_sections == ai_sections_json
        
        print("✅ JSON data handling successful")
        return True
        
    except Exception as e:
        print(f"❌ JSON data handling failed: {e}")
        return False


def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clean up test data (keep tables for migration testing)
        cursor.execute("DELETE FROM report_notifications WHERE message LIKE '%Test%'")
        cursor.execute("DELETE FROM report_content_versions WHERE change_summary LIKE '%test%'")
        cursor.execute("DELETE FROM ai_content_cache WHERE patient_id LIKE 'PAT%'")
        cursor.execute("DELETE FROM reports WHERE title LIKE '%Test%'")
        cursor.execute("DELETE FROM report_templates WHERE name LIKE '%Test%'")
        
        conn.commit()
        conn.close()
        
        print("✅ Test data cleaned up")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False


def main():
    """Run all database tests"""
    print("🚀 Starting AI Report Writing System Database Tests")
    print("=" * 60)
    
    tests = [
        setup_test_tables,
        test_reports_table_operations,
        test_report_templates_table_operations,
        test_ai_content_cache_operations,
        test_foreign_key_relationships,
        test_json_data_handling,
        cleanup_test_data
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print("-" * 40)
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All database tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)