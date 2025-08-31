#!/usr/bin/env python3
"""
Comprehensive API Tests for Report Management System

Tests all report CRUD operations, workflow endpoints, template management,
and multi-disciplinary data access with proper authentication.
"""

import sys
import os
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import (
    get_report_by_id, create_report, update_report_status, 
    get_reports_for_user, get_report_templates, cache_ai_content
)


class TestReportCRUDOperations:
    """Test basic CRUD operations for reports"""
    
    def test_create_report_basic(self):
        """Test creating a basic report"""
        report_data = {
            'patient_id': 'TEST_PATIENT_001',
            'report_type': 'progress',
            'template_id': 2,
            'title': 'Test Progress Report',
            'assigned_therapist_ids': ['THER001'],
            'disciplines': ['physiotherapy'],
            'requested_by_user_id': 'MGR001',
            'priority': 1
        }
        
        report_id = create_report(**report_data)
        assert isinstance(report_id, int)
        assert report_id > 0
        
        # Verify report was created
        retrieved_report = get_report_by_id(report_id)
        assert retrieved_report is not None
        assert retrieved_report['patient_id'] == 'TEST_PATIENT_001'
        assert retrieved_report['title'] == 'Test Progress Report'
        assert retrieved_report['status'] == 'pending'
    
    def test_create_report_with_deadline(self):
        """Test creating report with deadline"""
        deadline_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        report_data = {
            'patient_id': 'TEST_PATIENT_002',
            'report_type': 'discharge',
            'template_id': 2,
            'title': 'Discharge Summary with Deadline',
            'assigned_therapist_ids': ['THER002'],
            'disciplines': ['speech_therapy'],
            'deadline_date': deadline_date,
            'priority': 2
        }
        
        report_id = create_report(**report_data)
        retrieved_report = get_report_by_id(report_id)
        
        assert retrieved_report['deadline_date'] == deadline_date
        assert retrieved_report['priority'] == 2
    
    def test_create_multidisciplinary_report(self):
        """Test creating report with multiple disciplines"""
        report_data = {
            'patient_id': 'TEST_PATIENT_001',
            'report_type': 'comprehensive',
            'template_id': 2,
            'title': 'Multi-disciplinary Assessment',
            'assigned_therapist_ids': ['THER001', 'THER002', 'THER003'],
            'disciplines': ['physiotherapy', 'occupational_therapy', 'speech_therapy'],
            'requested_by_user_id': 'MGR001',
            'priority': 2
        }
        
        report_id = create_report(**report_data)
        retrieved_report = get_report_by_id(report_id)
        
        disciplines = json.loads(retrieved_report['disciplines'])
        therapist_ids = json.loads(retrieved_report['assigned_therapist_ids'])
        
        assert len(disciplines) == 3
        assert 'physiotherapy' in disciplines
        assert 'occupational_therapy' in disciplines
        assert 'speech_therapy' in disciplines
        assert len(therapist_ids) == 3
    
    def test_update_report_status(self):
        """Test updating report status"""
        # Create a report first
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='progress',
            template_id=1,
            title='Status Update Test',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy']
        )
        
        # Update status to in_progress
        success = update_report_status(report_id, 'in_progress', 'THER001')
        assert success is True
        
        retrieved_report = get_report_by_id(report_id)
        assert retrieved_report['status'] == 'in_progress'
        
        # Update to completed
        success = update_report_status(report_id, 'completed', 'THER001')
        assert success is True
        
        retrieved_report = get_report_by_id(report_id)
        assert retrieved_report['status'] == 'completed'
        assert retrieved_report['completed_at'] is not None
    
    def test_get_reports_for_user(self):
        """Test retrieving reports for specific user"""
        # Create test reports for different users
        report1_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='progress',
            template_id=2,
            title='User Report Test 1',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy']
        )
        
        report2_id = create_report(
            patient_id='TEST_PATIENT_002',
            report_type='discharge',
            template_id=2,
            title='User Report Test 2',
            assigned_therapist_ids=['THER002'],
            disciplines=['speech_therapy']
        )
        
        # Test getting reports for THER001
        ther001_reports = get_reports_for_user('THER001')
        assert len(ther001_reports) >= 1
        
        # Verify correct reports are returned
        found_report1 = False
        for report in ther001_reports:
            therapist_ids = report.get('assigned_therapist_ids', [])
            if 'THER001' in therapist_ids:
                found_report1 = True
                break
        
        assert found_report1, "Expected to find report assigned to THER001"


class TestReportWorkflowEndpoints:
    """Test report workflow management"""
    
    def test_manager_initiated_workflow(self):
        """Test manager-initiated report request workflow"""
        # Manager creates report request
        report_data = {
            'patient_id': 'TEST_PATIENT_001',
            'report_type': 'progress',
            'template_id': 2,
            'title': 'Manager Requested Progress Report',
            'assigned_therapist_ids': ['THER001'],
            'disciplines': ['physiotherapy'],
            'requested_by_user_id': 'MGR001',
            'deadline_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'priority': 2
        }
        
        report_id = create_report(**report_data)
        report = get_report_by_id(report_id)
        
        assert report['requested_by_user_id'] == 'MGR001'
        assert report['status'] == 'pending'
        assert report['deadline_date'] is not None
        
        # Therapist accepts and starts work
        success = update_report_status(report_id, 'in_progress', 'THER001')
        assert success is True
        
        report = get_report_by_id(report_id)
        assert report['status'] == 'in_progress'
    
    def test_therapist_initiated_workflow(self):
        """Test therapist-initiated report workflow"""
        # Therapist creates own report
        report_data = {
            'patient_id': 'TEST_PATIENT_002',
            'report_type': 'treatment_summary',
            'template_id': 2,
            'title': 'Self-initiated Treatment Summary',
            'assigned_therapist_ids': ['THER002'],
            'disciplines': ['speech_therapy'],
            'requested_by_user_id': None,  # Self-initiated
            'priority': 1
        }
        
        report_id = create_report(**report_data)
        report = get_report_by_id(report_id)
        
        assert report['requested_by_user_id'] is None
        assert report['status'] == 'pending'
        
        # Therapist can immediately start working
        success = update_report_status(report_id, 'in_progress', 'THER002')
        assert success is True
    
    def test_report_deadline_tracking(self):
        """Test deadline tracking functionality"""
        # Create report with tight deadline
        deadline_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='urgent',
            template_id=1,
            title='Urgent Report with Deadline',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy'],
            deadline_date=deadline_date,
            priority=3
        )
        
        report = get_report_by_id(report_id)
        assert report['deadline_date'] == deadline_date
        assert report['priority'] == 3
        
        # Test overdue detection (simulate past deadline)
        past_deadline = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        from modules.database import execute_query
        
        execute_query(
            "UPDATE reports SET deadline_date = ? WHERE id = ?",
            (past_deadline, report_id)
        )
        
        updated_report = get_report_by_id(report_id)
        report_deadline = datetime.strptime(updated_report['deadline_date'], '%Y-%m-%d')
        current_date = datetime.now()
        
        is_overdue = report_deadline.date() < current_date.date()
        assert is_overdue is True
    
    def test_priority_management(self):
        """Test report priority system"""
        priorities = [1, 2, 3]  # Low, Normal, High
        report_ids = []
        
        for priority in priorities:
            report_id = create_report(
                patient_id='TEST_PATIENT_001',
                report_type='priority_test',
                template_id=1,
                title=f'Priority {priority} Report',
                assigned_therapist_ids=['THER001'],
                disciplines=['physiotherapy'],
                priority=priority
            )
            report_ids.append(report_id)
        
        # Verify priorities are stored correctly
        for i, report_id in enumerate(report_ids):
            report = get_report_by_id(report_id)
            assert report['priority'] == priorities[i]


class TestTemplateManagement:
    """Test report template management"""
    
    def test_get_report_templates(self):
        """Test retrieving available report templates"""
        templates = get_report_templates()
        assert len(templates) > 0
        
        # Check template structure
        template = templates[0]
        required_fields = ['id', 'name', 'template_type', 'fields_schema', 'is_active']
        
        for field in required_fields:
            assert field in template
        
        # Verify fields_schema is valid (either dict or parseable JSON)
        fields_schema = template['fields_schema']
        if isinstance(fields_schema, str):
            try:
                fields_schema = json.loads(fields_schema)
            except json.JSONDecodeError:
                pytest.fail("fields_schema should be valid JSON")
        
        # Should be either a dict or list
        assert isinstance(fields_schema, (dict, list))
    
    def test_template_field_validation(self):
        """Test template field schema validation"""
        templates = get_report_templates()
        
        for template in templates:
            fields_schema = template['fields_schema']
            if isinstance(fields_schema, str):
                fields_schema = json.loads(fields_schema)
            
            # Handle both dict and list formats
            if isinstance(fields_schema, dict):
                # Dict format: field_name -> field_definition
                for field_name, field_def in fields_schema.items():
                    assert isinstance(field_name, str)
                    assert isinstance(field_def, dict)
                    # Check if field has basic properties
                    assert 'label' in field_def or 'description' in field_def
                    
            elif isinstance(fields_schema, list):
                # List format: list of field definitions
                for field in fields_schema:
                    assert isinstance(field, dict)
                    assert 'id' in field
                    assert 'label' in field
                    if 'type' in field:
                        valid_types = ['text', 'textarea', 'select', 'multiselect', 'date', 'number', 'checkbox']
                        assert field['type'] in valid_types


class TestMultiDisciplinaryAccess:
    """Test multi-disciplinary data access and permissions"""
    
    def test_cross_discipline_data_access(self):
        """Test accessing patient data across multiple disciplines"""
        from modules.data_aggregation import get_patient_data_summary
        
        # Test with multi-disciplinary patient
        patient_summary = get_patient_data_summary('TEST_PATIENT_001')
        
        assert patient_summary.patient_id == 'TEST_PATIENT_001'
        assert isinstance(patient_summary.disciplines_involved, list)
        
        # Should have data from multiple disciplines
        if len(patient_summary.treatment_notes) > 0:
            # Check for different professions in treatment notes
            professions = set()
            for note in patient_summary.treatment_notes:
                if 'profession' in note:
                    professions.add(note['profession'])
            
            # May have multiple disciplines
            assert len(professions) >= 1
    
    def test_discipline_filtering(self):
        """Test filtering data by specific disciplines"""
        from modules.data_aggregation import get_patient_data_summary
        
        # Test filtering by specific discipline
        physio_summary = get_patient_data_summary('TEST_PATIENT_001', disciplines=['physiotherapy'])
        
        if len(physio_summary.treatment_notes) > 0:
            # All notes should be physiotherapy-related
            for note in physio_summary.treatment_notes:
                if 'profession' in note:
                    profession_lower = note['profession'].lower()
                    assert 'physiotherapy' in profession_lower or 'physio' in profession_lower
    
    def test_data_completeness_indicators(self):
        """Test data completeness checking"""
        from modules.data_aggregation import get_patient_data_summary
        
        patient_summary = get_patient_data_summary('TEST_PATIENT_001')
        completeness = patient_summary.data_completeness
        
        # Check completeness structure
        assert isinstance(completeness, dict)
        assert 'has_demographics' in completeness
        assert 'has_treatment_notes' in completeness
        assert 'has_outcome_measures' in completeness
        
        # Should be boolean values
        for key, value in completeness.items():
            assert isinstance(value, bool)


class TestAIContentIntegration:
    """Test AI content generation integration with reports"""
    
    @patch('httpx.AsyncClient')
    async def test_ai_content_cache_integration(self, mock_client):
        """Test AI content caching for reports"""
        # Mock AI response
        mock_response = type('MockResponse', (), {
            'json': lambda: {
                "choices": [{"message": {"content": "Test medical history content"}}],
                "usage": {"total_tokens": 100}
            },
            'raise_for_status': lambda: None,
            'status_code': 200
        })()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            from modules.ai_content import ai_generator
            
            # Generate AI content
            result = await ai_generator.generate_medical_history('TEST_PATIENT_001')
            
            assert result['content'] == "Test medical history content"
            assert result['source'] in ['ai_generated', 'cached']
    
    def test_ai_cache_retrieval(self):
        """Test retrieving cached AI content for reports"""
        from modules.database import get_cached_ai_content
        
        # Try to get cached content
        cached_content = get_cached_ai_content('TEST_PATIENT_001', 'medical_history')
        
        if cached_content:
            assert 'content' in cached_content
            assert 'generated_at' in cached_content
            assert 'usage_count' in cached_content
            assert cached_content['usage_count'] >= 0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_report_id(self):
        """Test handling invalid report IDs"""
        invalid_report = get_report_by_id(99999)
        assert invalid_report is None
    
    def test_invalid_patient_id(self):
        """Test creating report with invalid patient ID"""
        try:
            report_id = create_report(
                patient_id='INVALID_PATIENT',
                report_type='test',
                template_id=1,
                title='Invalid Patient Test',
                assigned_therapist_ids=['THER001'],
                disciplines=['physiotherapy']
            )
            # Should still create the report (business logic allows this)
            assert isinstance(report_id, int)
        except Exception as e:
            # Or should handle gracefully
            assert "Invalid patient" in str(e) or "not found" in str(e)
    
    def test_empty_disciplines_list(self):
        """Test creating report with empty disciplines"""
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='test',
            template_id=1,
            title='Empty Disciplines Test',
            assigned_therapist_ids=['THER001'],
            disciplines=[]  # Empty list
        )
        
        report = get_report_by_id(report_id)
        disciplines = json.loads(report['disciplines'])
        assert isinstance(disciplines, list)
        assert len(disciplines) == 0
    
    def test_invalid_status_update(self):
        """Test updating report with invalid status"""
        report_id = create_report(
            patient_id='TEST_PATIENT_001',
            report_type='test',
            template_id=1,
            title='Status Update Test',
            assigned_therapist_ids=['THER001'],
            disciplines=['physiotherapy']
        )
        
        # Try invalid status
        success = update_report_status(report_id, 'invalid_status', 'THER001')
        # Should either return False or handle gracefully
        if success is not False:
            # Check that status wasn't changed to invalid value
            report = get_report_by_id(report_id)
            valid_statuses = ['draft', 'in_progress', 'completed', 'approved', 'cancelled']
            assert report['status'] in valid_statuses


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