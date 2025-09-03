#!/usr/bin/env python3
"""
Test script for report writing database helper functions

Tests the database helper functions for the AI Report Writing System.
"""
import sys
import os
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import (
    create_report, get_reports_for_user, update_report_status,
    get_report_templates, cache_ai_content, get_cached_ai_content,
    create_report_notification, get_user_notifications, mark_notification_read,
    get_patient_disciplines
)


def test_database_helpers():
    """Test all report writing database helper functions"""
    print("🧪 Testing report writing database helpers...")
    
    try:
        # Test 1: Create a report
        print("  Testing create_report...")
        report_id = create_report(
            patient_id="PAT001",
            report_type="progress",
            template_id=1,
            title="Test Progress Report",
            assigned_therapist_ids=["THER001", "THER002"],
            disciplines=["physiotherapy", "occupational_therapy"],
            requested_by_user_id="MGR001",
            priority=2
        )
        
        assert report_id is not None and report_id > 0
        print("    ✅ create_report working correctly")
        
        # Test 2: Get reports for user
        print("  Testing get_reports_for_user...")
        reports = get_reports_for_user("THER001")
        
        assert isinstance(reports, list)
        if reports:
            # Check that JSON fields are properly parsed
            assert isinstance(reports[0]['assigned_therapist_ids'], list)
            assert isinstance(reports[0]['disciplines'], list)
        print("    ✅ get_reports_for_user working correctly")
        
        # Test 3: Update report status
        print("  Testing update_report_status...")
        content = {
            "patient_info": {"name": "John Doe", "age": 45},
            "assessment": {"pain_level": 7, "mobility": "limited"}
        }
        
        success = update_report_status(report_id, "in_progress", content, "THER001")
        assert success is True
        print("    ✅ update_report_status working correctly")
        
        # Test 4: Get report templates (placeholder test since we need seed data)
        print("  Testing get_report_templates...")
        templates = get_report_templates()
        
        assert isinstance(templates, list)
        print("    ✅ get_report_templates working correctly")
        
        # Test 5: Cache AI content
        print("  Testing cache_ai_content...")
        cache_id = cache_ai_content(
            patient_id="PAT001",
            content_type="medical_history",
            content="Patient presents with chronic lower back pain...",
            discipline="physiotherapy"
        )
        
        assert cache_id is not None and cache_id > 0
        print("    ✅ cache_ai_content working correctly")
        
        # Test 6: Get cached AI content
        print("  Testing get_cached_ai_content...")
        cached_content = get_cached_ai_content("PAT001", "medical_history", "physiotherapy")
        
        assert cached_content is not None
        assert cached_content['content'] == "Patient presents with chronic lower back pain..."
        assert cached_content['usage_count'] >= 0  # Usage count should be present
        print("    ✅ get_cached_ai_content working correctly")
        
        # Test 7: Create notification
        print("  Testing create_report_notification...")
        notification_id = create_report_notification(
            report_id=report_id,
            user_id="THER001",
            notification_type="request",
            message="New report requested for Patient PAT001"
        )
        
        assert notification_id is not None and notification_id > 0
        print("    ✅ create_report_notification working correctly")
        
        # Test 8: Get user notifications
        print("  Testing get_user_notifications...")
        notifications = get_user_notifications("THER001")
        
        assert isinstance(notifications, list)
        if notifications:
            assert 'report_title' in notifications[0]
            assert 'patient_id' in notifications[0]
        print("    ✅ get_user_notifications working correctly")
        
        # Test 9: Mark notification as read
        print("  Testing mark_notification_read...")
        success = mark_notification_read(notification_id)
        assert success is True
        print("    ✅ mark_notification_read working correctly")
        
        # Test 10: Get patient disciplines (placeholder)
        print("  Testing get_patient_disciplines...")
        disciplines = get_patient_disciplines("PAT001")
        
        assert isinstance(disciplines, list)
        assert len(disciplines) > 0
        assert 'discipline' in disciplines[0]
        print("    ✅ get_patient_disciplines working correctly")
        
        print("✅ All database helper tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database helper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run database helper tests"""
    print("🚀 Testing AI Report Writing Database Helpers")
    print("=" * 50)
    
    success = test_database_helpers()
    
    if success:
        print("\n🎉 All database helper tests passed!")
        return True
    else:
        print("\n💥 Some database helper tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)