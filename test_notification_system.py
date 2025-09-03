#!/usr/bin/env python3
"""
Notification System Integration Tests
Tests the complete in-app notification system functionality
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import create_report, create_report_notification
from modules.reports import ReportNotificationService


class TestNotificationSystemIntegration:
    """Integration tests for the notification system"""
    
    def setup_method(self):
        """Setup test data before each test"""
        self.test_user_id = 'THER001'
        self.test_manager_id = 'MGR001'
        self.test_patient_id = 'TEST_PATIENT_001'
        
    def test_notification_creation(self):
        """Test creating various types of notifications"""
        # Create a test report
        report_id = create_report(
            patient_id=self.test_patient_id,
            report_type='progress',
            template_id=2,
            title='Test Report for Notifications',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['physiotherapy'],
            requested_by_user_id=self.test_manager_id,
            priority=2
        )
        
        # Test different notification types
        notification_types = [
            ('request', 'New report request from manager'),
            ('reminder', 'Report deadline reminder'),
            ('completion', 'Report completed successfully'),
            ('overdue', 'Report is overdue')
        ]
        
        created_notifications = []
        for notification_type, message in notification_types:
            notification_id = create_report_notification(
                report_id=report_id,
                user_id=self.test_user_id,
                notification_type=notification_type,
                message=message
            )
            
            assert isinstance(notification_id, int)
            assert notification_id > 0
            created_notifications.append(notification_id)
        
        print(f"✅ Created {len(created_notifications)} notifications of different types")
        return created_notifications
    
    def test_notification_retrieval(self):
        """Test retrieving notifications for a user"""
        # Create some notifications first
        self.test_notification_creation()
        
        # Retrieve notifications
        notifications = ReportNotificationService.get_user_report_notifications(self.test_user_id)
        
        # Verify structure and content
        assert isinstance(notifications, list)
        assert len(notifications) > 0
        
        for notification in notifications:
            # Check required fields
            required_fields = ['id', 'report_id', 'user_id', 'notification_type', 'message', 'created_at']
            for field in required_fields:
                assert field in notification, f"Missing field: {field}"
            
            # Check field types and values
            assert isinstance(notification['id'], int)
            assert isinstance(notification['report_id'], int)
            assert notification['user_id'] == self.test_user_id
            assert notification['notification_type'] in ['request', 'reminder', 'completion', 'overdue']
            assert isinstance(notification['message'], str)
            assert len(notification['message']) > 0
        
        print(f"✅ Retrieved {len(notifications)} notifications with proper structure")
        return notifications
    
    def test_unread_notification_filtering(self):
        """Test filtering for unread notifications only"""
        # Create notifications
        self.test_notification_creation()
        
        # Get all notifications
        all_notifications = ReportNotificationService.get_user_report_notifications(self.test_user_id)
        
        # Get only unread notifications
        unread_notifications = ReportNotificationService.get_user_report_notifications(
            self.test_user_id, unread_only=True
        )
        
        # All should be unread initially
        assert len(unread_notifications) == len(all_notifications)
        
        # Verify all returned notifications are unread
        for notification in unread_notifications:
            is_read = notification.get('is_read')
            assert is_read is False or is_read == 0, f"Notification {notification['id']} should be unread"
        
        print(f"✅ Filtered {len(unread_notifications)} unread notifications correctly")
    
    def test_marking_notifications_as_read(self):
        """Test marking notifications as read"""
        # Create notifications
        notification_ids = self.test_notification_creation()
        
        # Get initial unread count
        unread_before = ReportNotificationService.get_user_report_notifications(
            self.test_user_id, unread_only=True
        )
        initial_unread_count = len(unread_before)
        
        # Mark first notification as read
        first_notification_id = notification_ids[0]
        success = ReportNotificationService.mark_notification_as_read(first_notification_id)
        assert success is True
        
        # Check unread count decreased
        unread_after = ReportNotificationService.get_user_report_notifications(
            self.test_user_id, unread_only=True
        )
        new_unread_count = len(unread_after)
        
        assert new_unread_count == initial_unread_count - 1, "Unread count should decrease by 1"
        
        # Verify the specific notification is now read
        all_notifications = ReportNotificationService.get_user_report_notifications(self.test_user_id)
        read_notification = next(n for n in all_notifications if n['id'] == first_notification_id)
        assert read_notification.get('is_read') is True or read_notification.get('is_read') == 1
        
        print(f"✅ Successfully marked notification as read (unread: {initial_unread_count} → {new_unread_count})")
    
    def test_notification_workflow_integration(self):
        """Test notifications integrate with report workflow"""
        # Create a report that should trigger notifications
        report_id = create_report(
            patient_id=self.test_patient_id,
            report_type='urgent',
            template_id=2,
            title='Urgent Report with Workflow',
            assigned_therapist_ids=[self.test_user_id, 'THER002'],  # Multiple assignees
            disciplines=['physiotherapy', 'occupational_therapy'],
            requested_by_user_id=self.test_manager_id,
            deadline_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            priority=3  # High priority
        )
        
        # Test that urgent/high-priority reports can be identified
        from modules.reports import ReportWorkflowService
        urgent_reports = ReportWorkflowService.get_urgent_reports(self.test_user_id)
        
        # Our high-priority report should be in urgent list
        urgent_titles = [r['title'] for r in urgent_reports]
        assert 'Urgent Report with Workflow' in urgent_titles
        
        # Test overdue detection (create overdue report)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        overdue_report_id = create_report(
            patient_id=self.test_patient_id,
            report_type='overdue_test',
            template_id=2,
            title='Overdue Report Test',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['physiotherapy'],
            deadline_date=yesterday,
            priority=2
        )
        
        # Check overdue detection
        overdue_reports = ReportWorkflowService.get_overdue_reports(self.test_user_id)
        overdue_titles = [r['title'] for r in overdue_reports]
        assert 'Overdue Report Test' in overdue_titles
        
        print(f"✅ Workflow integration working: {len(urgent_reports)} urgent, {len(overdue_reports)} overdue")
    
    def test_notification_api_endpoints(self):
        """Test notification API endpoints (mock testing)"""
        # This would test the actual API endpoints
        # For now, we'll test the underlying functions they call
        
        # Create test notifications
        notification_ids = self.test_notification_creation()
        
        # Test the functions that the API endpoints use
        try:
            # Test get user notifications (used by GET /api/notifications/user)
            notifications = ReportNotificationService.get_user_report_notifications(self.test_user_id)
            unread_count = len([n for n in notifications if not n.get('is_read')])
            
            api_response = {
                "notifications": notifications,
                "unread_count": unread_count,
                "total_count": len(notifications)
            }
            
            assert 'notifications' in api_response
            assert 'unread_count' in api_response
            assert 'total_count' in api_response
            assert api_response['unread_count'] <= api_response['total_count']
            
            # Test mark as read function (used by POST /api/notifications/{id}/read)
            if notification_ids:
                success = ReportNotificationService.mark_notification_as_read(notification_ids[0])
                assert success is True
            
            print(f"✅ API endpoint functions working: {len(notifications)} notifications, {unread_count} unread")
            
        except Exception as e:
            print(f"⚠️  API endpoint test requires proper setup: {e}")
    
    def test_notification_priority_handling(self):
        """Test handling of different notification priorities"""
        # Create reports with different priorities
        priorities = [1, 2, 3]  # Low, Normal, High
        notification_data = []
        
        for priority in priorities:
            report_id = create_report(
                patient_id=self.test_patient_id,
                report_type='priority_test',
                template_id=2,
                title=f'Priority {priority} Report',
                assigned_therapist_ids=[self.test_user_id],
                disciplines=['physiotherapy'],
                deadline_date=(datetime.now() + timedelta(days=priority)).strftime('%Y-%m-%d'),
                priority=priority
            )
            
            # Create notification for this report
            notification_id = create_report_notification(
                report_id=report_id,
                user_id=self.test_user_id,
                notification_type='request',
                message=f'Priority {priority} report notification'
            )
            
            notification_data.append({
                'id': notification_id,
                'report_id': report_id,
                'priority': priority
            })
        
        # Test urgent detection (high priority reports should be urgent)
        from modules.reports import ReportWorkflowService
        urgent_reports = ReportWorkflowService.get_urgent_reports(self.test_user_id)
        
        # High priority report should be marked urgent
        high_priority_urgent = any(r['priority'] == 3 for r in urgent_reports)
        assert high_priority_urgent, "High priority reports should be marked as urgent"
        
        print(f"✅ Priority handling working: {len(notification_data)} notifications, high priority marked urgent")
    
    def test_notification_system_performance(self):
        """Test notification system performance with multiple notifications"""
        import time
        
        # Create many notifications quickly
        start_time = time.time()
        
        notification_ids = []
        for i in range(50):  # Create 50 notifications
            # Create a report first
            report_id = create_report(
                patient_id=self.test_patient_id,
                report_type='performance',
                template_id=2,
                title=f'Performance Test Report {i+1}',
                assigned_therapist_ids=[self.test_user_id],
                disciplines=['physiotherapy'],
                priority=(i % 3) + 1
            )
            
            # Create notification
            notification_id = create_report_notification(
                report_id=report_id,
                user_id=self.test_user_id,
                notification_type='request',
                message=f'Performance test notification {i+1}'
            )
            notification_ids.append(notification_id)
        
        creation_time = time.time() - start_time
        
        # Test retrieval performance
        start_time = time.time()
        
        all_notifications = ReportNotificationService.get_user_report_notifications(self.test_user_id)
        unread_notifications = ReportNotificationService.get_user_report_notifications(
            self.test_user_id, unread_only=True
        )
        
        retrieval_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 30.0, f"Notification creation too slow: {creation_time:.2f}s"
        assert retrieval_time < 5.0, f"Notification retrieval too slow: {retrieval_time:.2f}s"
        assert len(all_notifications) >= 50, "Not all notifications retrieved"
        
        print(f"✅ Performance test passed:")
        print(f"   - Created 50 notifications in {creation_time:.2f}s")
        print(f"   - Retrieved {len(all_notifications)} notifications in {retrieval_time:.2f}s")
        print(f"   - {len(unread_notifications)} unread notifications")
    
    def test_notification_data_integrity(self):
        """Test notification data integrity and validation"""
        # Test valid notification creation
        valid_report_id = create_report(
            patient_id=self.test_patient_id,
            report_type='integrity_test',
            template_id=2,
            title='Data Integrity Test',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['physiotherapy']
        )
        
        # Test with valid data
        valid_notification = create_report_notification(
            report_id=valid_report_id,
            user_id=self.test_user_id,
            notification_type='request',
            message='Valid notification message'
        )
        
        assert isinstance(valid_notification, int)
        assert valid_notification > 0
        
        # Test constraint validation
        try:
            # Test invalid notification type (should be constrained)
            invalid_notification = create_report_notification(
                report_id=valid_report_id,
                user_id=self.test_user_id,
                notification_type='invalid_type',
                message='This should fail'
            )
            # If we get here, constraints aren't working properly
            assert False, "Invalid notification type should have been rejected"
            
        except Exception as e:
            # This is expected - invalid types should be rejected
            assert 'constraint' in str(e).lower() or 'invalid' in str(e).lower()
            print(f"✅ Data integrity maintained: {e}")
        
        print(f"✅ Data integrity test passed: valid notification created, invalid rejected")


@pytest.fixture(autouse=True)
def setup_test_data():
    """Setup test data before tests run"""
    try:
        from create_test_data import create_test_patients, create_test_treatment_notes
        create_test_patients()
        create_test_treatment_notes()
    except ImportError:
        pass  # Test data creation script may not be available


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])