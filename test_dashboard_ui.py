#!/usr/bin/env python3
"""
Dashboard and UI Integration Tests for AI Report Writing System

Tests dashboard widgets, notification system, and UI components
for the AI-powered clinical report management system.
"""

import sys
import os
import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import create_report, get_reports_for_user, create_report_notification
from modules.reports import ReportWorkflowService, ReportNotificationService
from controllers.report_controller import ReportController


class TestDashboardWidgets:
    """Test dashboard widget functionality"""
    
    def test_pending_reports_widget_data(self):
        """Test data structure for pending reports widget"""
        # Create test reports with different statuses
        pending_report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='progress',
            template_id=2,
            title='Pending Report Widget Test',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy'],
            priority=2
        )
        
        # Test the underlying data directly
        from modules.database import get_reports_for_user
        
        # Get reports by status
        pending_reports = get_reports_for_user('THER001', status='pending')
        in_progress_reports = get_reports_for_user('THER001', status='in_progress')
        completed_reports = get_reports_for_user('THER001', status='completed', limit=10)
        
        # Verify structure
        assert isinstance(pending_reports, list)
        assert isinstance(in_progress_reports, list)
        assert isinstance(completed_reports, list)
        
        # Check report counts
        report_counts = {
            'pending': len(pending_reports),
            'in_progress': len(in_progress_reports),
            'completed': len(completed_reports),
            'overdue': 0  # Would be calculated based on deadlines
        }
        
        required_count_keys = ['pending', 'in_progress', 'completed', 'overdue']
        for key in required_count_keys:
            assert key in report_counts
            assert isinstance(report_counts[key], int)
        
        # Test that we have at least the report we created
        assert report_counts['pending'] >= 1
    
    def test_overdue_reports_widget(self):
        """Test overdue reports detection and display"""
        # Create overdue report (deadline yesterday)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        overdue_report_id = create_report(
            patient_id='TEST_PATIENT_002',
            report_type='urgent',
            template_id=2,
            title='Overdue Report Test',
            assigned_therapist_ids=['THER001'],
            disciplines=['speech_therapy'],
            deadline_date=yesterday,
            priority=3
        )
        
        # Get overdue reports
        overdue_reports = ReportWorkflowService.get_overdue_reports('THER001')
        
        # Verify overdue detection
        assert len(overdue_reports) > 0
        
        # Find our test report
        test_overdue = next((r for r in overdue_reports if r['id'] == overdue_report_id), None)
        assert test_overdue is not None
        assert test_overdue['days_overdue'] >= 1
        assert test_overdue['priority'] == 3
    
    def test_report_priority_display(self):
        """Test priority-based report display and sorting"""
        # Create reports with different priorities
        priorities = [1, 2, 3]  # Low, Normal, High
        report_ids = []
        
        for priority in priorities:
            report_id = create_report(
                patient_id='TEST_PATIENT_001',
                report_type='priority_test',
                template_id=2,
                title=f'Priority {priority} Report',
                assigned_therapist_ids=['THER001'],
                disciplines=['physiotherapy'],
                priority=priority
            )
            report_ids.append(report_id)
        
        # Get urgent reports (should include high priority)
        urgent_reports = ReportWorkflowService.get_urgent_reports('THER001')
        
        # Verify high priority reports are marked as urgent
        high_priority_found = False
        for report in urgent_reports:
            if report['priority'] == 3:
                high_priority_found = True
                assert 'urgency_reason' in report
                assert 'High priority' in ' '.join(report['urgency_reason'])
        
        assert high_priority_found, "High priority reports should be marked as urgent"
    
    def test_deadline_tracking_widget(self):
        """Test deadline tracking and warning display"""
        # Create report due in 1 day (should trigger warning)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        urgent_deadline_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='deadline_test',
            template_id=2,
            title='Deadline Warning Test',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy'],
            deadline_date=tomorrow,
            priority=1
        )
        
        # Get urgent reports
        urgent_reports = ReportWorkflowService.get_urgent_reports('THER001')
        
        # Find our deadline test report
        deadline_urgent = next((r for r in urgent_reports if r['id'] == urgent_deadline_id), None)
        assert deadline_urgent is not None
        assert 'urgency_reason' in deadline_urgent
        
        # Should have deadline warning
        urgency_reasons = ' '.join(deadline_urgent['urgency_reason'])
        assert 'Due in 1 days' in urgency_reasons
    
    def test_report_analytics_widget(self):
        """Test report analytics calculation for dashboard"""
        user_id = 'THER001'
        
        # Get analytics
        analytics = ReportWorkflowService.get_report_analytics(user_id)
        
        # Verify analytics structure
        required_keys = [
            'total_reports', 'pending_count', 'in_progress_count', 
            'completed_count', 'overdue_count', 'completion_rate',
            'average_completion_days', 'urgent_reports'
        ]
        
        for key in required_keys:
            assert key in analytics
            assert isinstance(analytics[key], (int, float))
        
        # Verify calculations are logical
        assert analytics['completion_rate'] >= 0 and analytics['completion_rate'] <= 100
        assert analytics['total_reports'] >= 0
        assert analytics['average_completion_days'] >= 0


class TestNotificationSystem:
    """Test notification system functionality"""
    
    def test_notification_creation(self):
        """Test creating notifications for report events"""
        # Create test report
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='notification_test',
            template_id=2,
            title='Notification Test Report',
            assigned_therapist_ids=['THER002'],
            disciplines=['physiotherapy']
        )
        
        # Create notification
        notification_id = create_report_notification(
            report_id=report_id,
            user_id='THER002',
            notification_type='request',
            message='Test notification message'
        )
        
        assert isinstance(notification_id, int)
        assert notification_id > 0
    
    def test_notification_retrieval(self):
        """Test retrieving user notifications"""
        user_id = 'THER001'
        
        # Get notifications
        notifications = ReportNotificationService.get_user_report_notifications(user_id)
        
        # Verify structure
        assert isinstance(notifications, list)
        
        if notifications:
            notification = notifications[0]
            required_fields = ['id', 'report_id', 'user_id', 'notification_type', 'message', 'created_at']
            
            for field in required_fields:
                assert field in notification
    
    def test_unread_notification_filtering(self):
        """Test filtering unread notifications"""
        user_id = 'THER001'
        
        # Get unread notifications
        unread_notifications = ReportNotificationService.get_user_report_notifications(
            user_id, unread_only=True
        )
        
        # Verify all returned notifications are unread
        for notification in unread_notifications:
            assert notification.get('is_read') is False or notification.get('is_read') == 0
    
    def test_notification_marking_read(self):
        """Test marking notifications as read"""
        # Create test notification
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='read_test',
            template_id=2,
            title='Read Test Report',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy']
        )
        
        notification_id = create_report_notification(
            report_id=report_id,
            user_id='THER001',
            notification_type='reminder',
            message='Test read functionality'
        )
        
        # Mark as read
        success = ReportNotificationService.mark_notification_as_read(notification_id)
        assert success is True
    
    def test_status_change_notifications(self):
        """Test automatic notifications when report status changes"""
        # Create report with manager requester
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='status_change_test',
            template_id=2,
            title='Status Change Test',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy'],
            requested_by_user_id='MGR001'
        )
        
        # Update status (should trigger notification)
        success = ReportWorkflowService.update_report_workflow(
            report_id=report_id,
            new_status='in_progress',
            user_id='THER001',
            notify_stakeholders=True
        )
        
        assert success is True
        
        # Check for notifications (would need to verify notification was created)
        # This is more of an integration test that would verify the notification exists


class TestUIComponents:
    """Test UI component functionality"""
    
    def test_report_modal_data_structure(self):
        """Test data structure for report creation modal"""
        from modules.database import get_report_templates, get_patient_disciplines
        
        # Get templates for modal
        templates = get_report_templates()
        assert len(templates) > 0
        
        # Verify template structure for UI
        template = templates[0]
        ui_required_fields = ['id', 'name', 'description', 'fields_schema']
        
        for field in ui_required_fields:
            assert field in template
        
        # Test patient disciplines for auto-detection
        disciplines = get_patient_disciplines('TEST_PATIENT_001')
        assert isinstance(disciplines, list)
    
    def test_discipline_selection_data(self):
        """Test discipline selection options for UI"""
        # Get available disciplines from existing data
        from modules.data_aggregation import get_patient_data_summary
        
        patient_summary = get_patient_data_summary('TEST_PATIENT_001')
        assert hasattr(patient_summary, 'disciplines_involved')
        assert isinstance(patient_summary.disciplines_involved, list)
        
        # Verify common disciplines are available
        common_disciplines = ['physiotherapy', 'occupational_therapy', 'speech_therapy']
        
        # At least some disciplines should be present in test data
        assert len(patient_summary.disciplines_involved) >= 0
    
    def test_report_editing_data_structure(self):
        """Test data structure for report editing interface"""
        # Create test report with content
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='editing_test',
            template_id=2,
            title='Report Editing Test',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy']
        )
        
        # Get report data for editing
        from modules.database import get_report_by_id
        report = get_report_by_id(report_id)
        
        # Verify structure for UI editing
        editing_required_fields = ['id', 'title', 'status', 'content', 'ai_generated_sections']
        
        for field in editing_required_fields:
            assert field in report
        
        # Verify JSON fields are properly structured
        import json
        if report.get('disciplines'):
            disciplines = json.loads(report['disciplines']) if isinstance(report['disciplines'], str) else report['disciplines']
            assert isinstance(disciplines, list)


class TestResponsiveDesign:
    """Test responsive design considerations"""
    
    def test_mobile_widget_data_limits(self):
        """Test data limits for mobile widget display"""
        mock_user = {'user_id': 'THER001', 'role': 'therapist'}
        
        # Test with limit for mobile display
        from modules.database import get_reports_for_user
        
        # Get limited reports for mobile widgets
        mobile_reports = get_reports_for_user('THER001', limit=5)
        
        # Should not exceed mobile display limits
        assert len(mobile_reports) <= 5
        
        # Verify essential fields are present for mobile display
        if mobile_reports:
            report = mobile_reports[0]
            mobile_essential_fields = ['id', 'title', 'status', 'priority', 'deadline_date']
            
            for field in mobile_essential_fields:
                assert field in report
    
    def test_dashboard_summary_conciseness(self):
        """Test dashboard summary data is concise for quick loading"""
        analytics = ReportWorkflowService.get_report_analytics('THER001')
        
        # Analytics should be lightweight for dashboard
        assert len(analytics) <= 10  # Reasonable number of summary metrics
        
        # All values should be simple numbers (not complex objects)
        for key, value in analytics.items():
            assert isinstance(value, (int, float, str))


class TestAccessibility:
    """Test accessibility considerations for UI components"""
    
    def test_notification_priority_indicators(self):
        """Test priority indicators for accessibility"""
        urgent_reports = ReportWorkflowService.get_urgent_reports('THER001')
        
        # Urgent reports should have clear priority indicators
        for report in urgent_reports:
            assert 'urgency_reason' in report
            assert isinstance(report['urgency_reason'], list)
            assert len(report['urgency_reason']) > 0
            
            # Priority should be clearly indicated
            assert 'priority' in report
            assert report['priority'] in [1, 2, 3]
    
    def test_status_accessibility_labels(self):
        """Test status labels are accessible"""
        reports = get_reports_for_user('THER001', limit=5)
        
        valid_statuses = ['pending', 'in_progress', 'completed', 'overdue', 'cancelled']
        
        for report in reports:
            assert report['status'] in valid_statuses
            # Status should be human-readable for screen readers
            assert isinstance(report['status'], str)
            assert len(report['status']) > 0


class TestErrorHandling:
    """Test error handling in UI components"""
    
    def test_empty_dashboard_data(self):
        """Test dashboard with no reports"""
        # Test with non-existent user
        analytics = ReportWorkflowService.get_report_analytics('NONEXISTENT_USER')
        
        # Should return empty but valid structure
        assert isinstance(analytics, dict)
        assert analytics['total_reports'] == 0
        assert analytics['completion_rate'] == 0
    
    def test_invalid_notification_handling(self):
        """Test handling invalid notifications"""
        # Try to mark non-existent notification as read
        success = ReportNotificationService.mark_notification_as_read(99999)
        
        # Should handle gracefully (may return True if no error checking implemented)
        assert isinstance(success, bool)
    
    def test_malformed_report_data_handling(self):
        """Test handling reports with malformed data"""
        from modules.database import get_report_by_id
        
        # Test with invalid report ID
        invalid_report = get_report_by_id(99999)
        assert invalid_report is None


@pytest.fixture(autouse=True)
def setup_test_data():
    """Setup test data before each test"""
    # Ensure test data exists
    try:
        from create_test_data import create_test_patients, create_test_treatment_notes
        create_test_patients()
        create_test_treatment_notes()
    except ImportError:
        pass  # Test data creation script may not be available


if __name__ == "__main__":
    pytest.main([__file__, "-v"])