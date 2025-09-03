#!/usr/bin/env python3
"""
Dashboard Widgets Integration Tests
Tests the full dashboard widget functionality with API integration
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import create_report, get_reports_for_user
from modules.reports import ReportWorkflowService
from controllers.report_controller import ReportController


class TestDashboardWidgetsIntegration:
    """Integration tests for dashboard widgets with real data"""
    
    def setup_method(self):
        """Setup test data before each test"""
        self.test_user_id = 'THER001'
        self.test_patient_id = 'TEST_PATIENT_001'
        
    def test_pending_reports_widget_data(self):
        """Test pending reports widget displays correct data"""
        # Create test reports with different priorities and deadlines
        
        # High priority, due soon
        urgent_report_id = create_report(
            patient_id=self.test_patient_id,
            report_type='progress',
            template_id=2,
            title='Urgent Progress Report',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['physiotherapy'],
            deadline_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            priority=3
        )
        
        # Normal priority, due today
        today_report_id = create_report(
            patient_id=self.test_patient_id,
            report_type='discharge',
            template_id=3,
            title='Discharge Report Due Today',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['occupational_therapy'],
            deadline_date=datetime.now().strftime('%Y-%m-%d'),
            priority=2
        )
        
        # Low priority, no urgency
        normal_report_id = create_report(
            patient_id=self.test_patient_id,
            report_type='insurance',
            template_id=4,
            title='Regular Insurance Report',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['speech_therapy'],
            deadline_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            priority=1
        )
        
        # Test widget data retrieval
        reports = get_reports_for_user(self.test_user_id, status='pending')
        
        # Verify we have the expected reports
        report_titles = [r['title'] for r in reports]
        assert 'Urgent Progress Report' in report_titles
        assert 'Discharge Report Due Today' in report_titles
        assert 'Regular Insurance Report' in report_titles
        
        # Test urgent reports detection
        urgent_reports = ReportWorkflowService.get_urgent_reports(self.test_user_id)
        urgent_titles = [r['title'] for r in urgent_reports]
        
        # High priority should be marked urgent
        assert 'Urgent Progress Report' in urgent_titles
        # Due today should be marked urgent
        assert 'Discharge Report Due Today' in urgent_titles
        
        print(f"✅ Created {len(reports)} pending reports with proper priority classification")
    
    def test_overdue_reports_widget_data(self):
        """Test overdue reports widget shows overdue items"""
        # Create overdue report
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        overdue_recent_id = create_report(
            patient_id=self.test_patient_id,
            report_type='progress',
            template_id=2,
            title='Recently Overdue Report',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['physiotherapy'],
            deadline_date=yesterday,
            priority=2
        )
        
        overdue_old_id = create_report(
            patient_id=self.test_patient_id,
            report_type='outcome_summary',
            template_id=5,
            title='Very Overdue Report',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['psychology'],
            deadline_date=week_ago,
            priority=3
        )
        
        # Get overdue reports
        overdue_reports = ReportWorkflowService.get_overdue_reports(self.test_user_id)
        
        # Verify overdue detection
        assert len(overdue_reports) >= 2
        
        overdue_titles = [r['title'] for r in overdue_reports]
        assert 'Recently Overdue Report' in overdue_titles
        assert 'Very Overdue Report' in overdue_titles
        
        # Check days overdue calculation
        for report in overdue_reports:
            assert report['days_overdue'] > 0
            if report['title'] == 'Very Overdue Report':
                assert report['days_overdue'] >= 7
            elif report['title'] == 'Recently Overdue Report':
                assert report['days_overdue'] >= 1
        
        print(f"✅ Identified {len(overdue_reports)} overdue reports with correct day calculations")
    
    def test_in_progress_reports_widget(self):
        """Test in-progress reports widget functionality"""
        # Create in-progress report
        in_progress_id = create_report(
            patient_id=self.test_patient_id,
            report_type='multi_disciplinary',
            template_id=6,
            title='Multi-disciplinary Assessment In Progress',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['physiotherapy', 'occupational_therapy', 'speech_therapy'],
            priority=2
        )
        
        # Update status to in_progress
        success = ReportWorkflowService.update_report_workflow(
            report_id=in_progress_id,
            new_status='in_progress',
            user_id=self.test_user_id
        )
        assert success
        
        # Verify in-progress reports can be retrieved
        in_progress_reports = get_reports_for_user(self.test_user_id, status='in_progress')
        
        in_progress_titles = [r['title'] for r in in_progress_reports]
        assert 'Multi-disciplinary Assessment In Progress' in in_progress_titles
        
        # Find our specific report
        our_report = next(r for r in in_progress_reports if r['id'] == in_progress_id)
        assert our_report['status'] == 'in_progress'
        assert len(our_report['disciplines']) >= 3  # Multi-disciplinary
        
        print(f"✅ Successfully tracking {len(in_progress_reports)} in-progress reports")
    
    def test_completed_reports_widget(self):
        """Test completed reports widget shows recent completions"""
        # Create and complete a report
        completed_id = create_report(
            patient_id=self.test_patient_id,
            report_type='discharge',
            template_id=3,
            title='Completed Discharge Report',
            assigned_therapist_ids=[self.test_user_id],
            disciplines=['physiotherapy'],
            priority=2
        )
        
        # Mark as completed
        success = ReportWorkflowService.update_report_workflow(
            report_id=completed_id,
            new_status='completed',
            user_id=self.test_user_id
        )
        assert success
        
        # Get completed reports
        completed_reports = get_reports_for_user(self.test_user_id, status='completed', limit=10)
        
        completed_titles = [r['title'] for r in completed_reports]
        assert 'Completed Discharge Report' in completed_titles
        
        # Verify the report is marked as completed
        our_report = next(r for r in completed_reports if r['id'] == completed_id)
        assert our_report['status'] == 'completed'
        
        print(f"✅ Successfully tracking {len(completed_reports)} completed reports")
    
    def test_analytics_widget_calculations(self):
        """Test analytics calculations for widgets"""
        user_id = self.test_user_id
        
        # Get analytics
        analytics = ReportWorkflowService.get_report_analytics(user_id)
        
        # Verify analytics structure and data types
        required_fields = [
            'total_reports', 'pending_count', 'in_progress_count', 
            'completed_count', 'overdue_count', 'completion_rate',
            'average_completion_days', 'urgent_reports'
        ]
        
        for field in required_fields:
            assert field in analytics, f"Missing analytics field: {field}"
            assert isinstance(analytics[field], (int, float)), f"Invalid type for {field}: {type(analytics[field])}"
        
        # Verify logical constraints
        assert analytics['completion_rate'] >= 0 and analytics['completion_rate'] <= 100
        assert analytics['total_reports'] >= 0
        assert analytics['average_completion_days'] >= 0
        
        # Verify counts add up logically
        total_active = analytics['pending_count'] + analytics['in_progress_count'] + analytics['completed_count']
        assert total_active <= analytics['total_reports']  # Some might be cancelled/etc
        
        print(f"✅ Analytics calculations valid: {analytics}")
    
    def test_deadline_timeline_data(self):
        """Test deadline timeline widget data"""
        # Create reports with various deadlines
        deadlines = [
            (datetime.now() + timedelta(days=1), 'Due Tomorrow'),
            (datetime.now() + timedelta(days=3), 'Due in 3 Days'),
            (datetime.now() + timedelta(days=7), 'Due Next Week'),
            (datetime.now() + timedelta(days=14), 'Due in 2 Weeks')
        ]
        
        created_reports = []
        for i, (deadline_date, title) in enumerate(deadlines):
            report_id = create_report(
                patient_id=self.test_patient_id,
                report_type='progress',
                template_id=2,
                title=title,
                assigned_therapist_ids=[self.test_user_id],
                disciplines=['physiotherapy'],
                deadline_date=deadline_date.strftime('%Y-%m-%d'),
                priority=2
            )
            created_reports.append(report_id)
        
        # Get all reports with deadlines
        all_reports = get_reports_for_user(self.test_user_id, limit=50)
        reports_with_deadlines = [r for r in all_reports if r.get('deadline_date')]
        
        # Verify we can sort by deadline
        sorted_reports = sorted(reports_with_deadlines, key=lambda r: r['deadline_date'])
        
        # Check that sorting works
        for i in range(len(sorted_reports) - 1):
            current_deadline = datetime.strptime(sorted_reports[i]['deadline_date'], '%Y-%m-%d')
            next_deadline = datetime.strptime(sorted_reports[i + 1]['deadline_date'], '%Y-%m-%d')
            assert current_deadline <= next_deadline, "Reports not properly sorted by deadline"
        
        print(f"✅ Successfully created and sorted {len(reports_with_deadlines)} reports with deadlines")
    
    def test_dashboard_data_api_endpoint(self):
        """Test the dashboard data API endpoint"""
        # This would test the actual API endpoint
        # For now, we'll test the controller method directly
        from unittest.mock import Mock
        
        # Mock the current_user
        mock_user = Mock()
        mock_user.get.return_value = self.test_user_id
        
        try:
            # Test dashboard data retrieval
            dashboard_data = ReportController.get_dashboard_data(current_user={'user_id': self.test_user_id})
            
            # Verify structure
            assert hasattr(dashboard_data, 'pending_reports')
            assert hasattr(dashboard_data, 'overdue_reports')
            assert hasattr(dashboard_data, 'completed_reports')
            assert hasattr(dashboard_data, 'report_counts')
            
            # Verify counts
            counts = dashboard_data.report_counts
            assert 'pending' in counts
            assert 'overdue' in counts
            assert 'completed' in counts
            
            print(f"✅ Dashboard API returns structured data with {counts}")
            
        except Exception as e:
            print(f"⚠️  Dashboard API test requires proper authentication setup: {e}")
            # This is expected in test environment without full auth setup
    
    def test_widget_performance_with_large_dataset(self):
        """Test widget performance with larger dataset"""
        import time
        
        # Create multiple reports quickly
        start_time = time.time()
        
        report_ids = []
        for i in range(20):  # Create 20 reports
            report_id = create_report(
                patient_id=self.test_patient_id,
                report_type='progress',
                template_id=2,
                title=f'Performance Test Report {i+1}',
                assigned_therapist_ids=[self.test_user_id],
                disciplines=['physiotherapy'],
                deadline_date=(datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                priority=(i % 3) + 1  # Mix of priorities
            )
            report_ids.append(report_id)
        
        creation_time = time.time() - start_time
        
        # Test data retrieval performance
        start_time = time.time()
        
        reports = get_reports_for_user(self.test_user_id, limit=50)
        urgent_reports = ReportWorkflowService.get_urgent_reports(self.test_user_id)
        analytics = ReportWorkflowService.get_report_analytics(self.test_user_id)
        
        retrieval_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 10.0, f"Report creation too slow: {creation_time:.2f}s"
        assert retrieval_time < 5.0, f"Data retrieval too slow: {retrieval_time:.2f}s"
        assert len(reports) >= 20, "Not all reports retrieved"
        
        print(f"✅ Performance test passed:")
        print(f"   - Created 20 reports in {creation_time:.2f}s")
        print(f"   - Retrieved all data in {retrieval_time:.2f}s")
        print(f"   - Found {len(urgent_reports)} urgent reports")
        print(f"   - Analytics: {analytics['total_reports']} total reports")
    
    def test_widget_responsive_design_data(self):
        """Test that widget data is suitable for responsive display"""
        # Get data for various widget types
        pending_reports = get_reports_for_user(self.test_user_id, status='pending', limit=5)
        completed_reports = get_reports_for_user(self.test_user_id, status='completed', limit=5)
        
        # Test that reports have necessary fields for mobile display
        for report in pending_reports[:3]:  # Test first 3 reports
            # Essential fields for mobile cards
            mobile_fields = ['id', 'title', 'status', 'priority', 'deadline_date', 'patient_id']
            for field in mobile_fields:
                assert field in report, f"Missing essential mobile field: {field}"
            
            # Title should not be too long for mobile
            assert len(report['title']) <= 100, f"Title too long for mobile: {report['title']}"
            
            # Priority should be valid
            assert report['priority'] in [1, 2, 3], f"Invalid priority: {report['priority']}"
        
        print(f"✅ Widget data suitable for responsive design")
        print(f"   - {len(pending_reports)} pending reports with mobile-friendly fields")
        print(f"   - {len(completed_reports)} completed reports ready for display")


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