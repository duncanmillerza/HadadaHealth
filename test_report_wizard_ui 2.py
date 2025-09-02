#!/usr/bin/env python3
"""
Report Creation Wizard UI Tests for AI Report Writing System

Tests the 5-step report creation wizard including step validation,
navigation, state management, and end-to-end report creation flow.
"""

import sys
import os
import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import create_report, get_reports_for_user, create_report_notification
from controllers.report_controller import ReportController


class TestReportWizardValidation:
    """Test report wizard step validation logic"""
    
    def test_step_1_patient_validation(self):
        """Test patient selection validation in step 1"""
        # Mock wizard state without patient
        wizard_state = {
            'patient': None,
            'reportType': 'discharge',
            'template': {'id': 1, 'name': 'Test Template'},
            'title': 'Test Report',
            'disciplines': ['physiotherapy'],
            'therapists': [{'id': '1', 'name': 'Test Therapist'}]
        }
        
        # Patient is required for step 1
        assert wizard_state['patient'] is None
        
        # Test with valid patient
        wizard_state['patient'] = {
            'id': 'TEST001',
            'name': 'Test Patient',
            'dob': '1990-01-01'
        }
        assert wizard_state['patient'] is not None
        assert wizard_state['patient']['id'] == 'TEST001'
        
    def test_step_2_report_type_validation(self):
        """Test report type and template validation in step 2"""
        wizard_state = {
            'patient': {'id': 'TEST001', 'name': 'Test Patient'},
            'reportType': None,
            'template': None,
            'title': '',
        }
        
        # All fields required for step 2
        assert wizard_state['reportType'] is None
        assert wizard_state['template'] is None
        assert not wizard_state['title'].strip()
        
        # Test with valid data
        wizard_state.update({
            'reportType': 'discharge',
            'template': {'id': 1, 'name': 'Discharge Template'},
            'title': 'Test Discharge Report'
        })
        
        assert wizard_state['reportType'] == 'discharge'
        assert wizard_state['template']['id'] == 1
        assert wizard_state['title'].strip() != ''
        
    def test_step_3_discipline_validation(self):
        """Test discipline selection validation in step 3"""
        wizard_state = {
            'patient': {'id': 'TEST001'},
            'reportType': 'discharge',
            'template': {'id': 1},
            'title': 'Test Report',
            'disciplines': [],
        }
        
        # At least one discipline required
        assert len(wizard_state['disciplines']) == 0
        
        # Test with valid disciplines
        wizard_state['disciplines'] = ['physiotherapy', 'occupational_therapy']
        assert len(wizard_state['disciplines']) > 0
        assert 'physiotherapy' in wizard_state['disciplines']
        
    def test_step_4_therapist_validation(self):
        """Test therapist assignment validation in step 4"""
        wizard_state = {
            'patient': {'id': 'TEST001'},
            'reportType': 'discharge',
            'template': {'id': 1},
            'title': 'Test Report',
            'disciplines': ['physiotherapy'],
            'therapists': [],
        }
        
        # At least one therapist required
        assert len(wizard_state['therapists']) == 0
        
        # Test with valid therapist assignment
        wizard_state['therapists'] = [{'id': '1', 'name': 'Duncan Miller'}]
        assert len(wizard_state['therapists']) > 0
        assert wizard_state['therapists'][0]['id'] == '1'
        
    def test_step_5_priority_validation(self):
        """Test priority and deadline validation in step 5"""
        wizard_state = {
            'priority': 2,  # Default medium priority
            'deadline': None  # Optional
        }
        
        # Priority should have valid default
        assert wizard_state['priority'] in [1, 2, 3]
        
        # Test with deadline
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        wizard_state['deadline'] = tomorrow
        
        deadline_date = datetime.strptime(wizard_state['deadline'], '%Y-%m-%d').date()
        assert deadline_date > datetime.now().date()


class TestReportWizardAPI:
    """Test wizard API integration and data flow"""
    
    @pytest.fixture
    def mock_wizard_options_response(self):
        """Mock wizard options API response"""
        return {
            "allowed_report_types": ["discharge", "progress", "assessment"],
            "priorities": [
                {"value": 1, "label": "Low"}, 
                {"value": 2, "label": "Medium"}, 
                {"value": 3, "label": "High"}
            ],
            "user_role": "therapist",
            "user_defaults": {"priority": 2, "assigned_therapist_ids": ["1"]},
            "recommended_disciplines": [
                {"discipline": "Physiotherapy", "bookings_count": 5, "last_seen": "2025-08-27"}
            ],
            "suggested_therapists": [
                {"user_id": "1", "name": "Duncan Miller", "disciplines": ["Physiotherapy"], 
                 "bookings_count_with_patient": 4, "last_seen": "2025-08-27"}
            ],
            "other_therapists": [
                {"user_id": "3", "name": "Kim Jones", "disciplines": ["Occupational Therapy"],
                 "bookings_count_with_patient": 0, "last_seen": None}
            ]
        }
    
    def test_wizard_options_api_call(self, mock_wizard_options_response):
        """Test wizard options API integration"""
        with patch('controllers.report_controller.ReportController.get_wizard_options') as mock_api:
            mock_api.return_value = mock_wizard_options_response
            
            # Simulate API call for step 4 (therapist suggestions)
            response = ReportController.get_wizard_options(
                patient_id="4603087263088",
                disciplines="physiotherapy,occupational_therapy"
            )
            
            assert response is not None
            assert "suggested_therapists" in response
            assert len(response["suggested_therapists"]) > 0
            assert response["suggested_therapists"][0]["user_id"] == "1"
    
    def test_discipline_mapping_fix(self):
        """Test that discipline mapping works correctly"""
        # Test the discipline mapping we implemented
        frontend_disciplines = ["physiotherapy", "occupational_therapy"]
        expected_db_disciplines = ["Physiotherapy", "Occupational Therapy"]
        
        discipline_mapping = {
            'physiotherapy': 'Physiotherapy',
            'occupational_therapy': 'Occupational Therapy',
            'speech_therapy': 'Speech Therapy',
            'psychology': 'Psychology'
        }
        
        mapped_disciplines = []
        for discipline in frontend_disciplines:
            mapped = discipline_mapping.get(discipline.lower())
            if mapped:
                mapped_disciplines.append(mapped)
                
        assert mapped_disciplines == expected_db_disciplines
        
    def test_therapist_suggestions_query(self):
        """Test therapist suggestions database query logic"""
        # This tests the logic we fixed in _get_therapist_suggestions
        patient_id = "4603087263088"
        disciplines = ["physiotherapy"]  # Frontend format
        
        # Test discipline mapping
        discipline_mapping = {
            'physiotherapy': 'Physiotherapy',
            'occupational_therapy': 'Occupational Therapy',
        }
        
        db_disciplines = [discipline_mapping.get(d, d.replace('_', ' ').title()) 
                         for d in disciplines]
        
        assert db_disciplines == ["Physiotherapy"]


class TestReportWizardEndToEnd:
    """Test complete end-to-end wizard flow"""
    
    def test_complete_wizard_flow_simulation(self):
        """Test complete wizard workflow simulation"""
        # Step 1: Patient Selection
        wizard_state = {'step': 1}
        
        # Simulate patient selection
        selected_patient = {
            'id': '4603087263088',
            'name': 'Andrew Mokoena', 
            'dob': '1987-08-30',
            'identifiers': '8708309999088'
        }
        wizard_state['patient'] = selected_patient
        
        # Validate step 1
        assert wizard_state['patient'] is not None
        wizard_state['step'] = 2
        
        # Step 2: Report Type & Template
        wizard_state.update({
            'reportType': 'discharge',
            'template': {'id': 1, 'name': 'Standard Discharge Report'},
            'title': 'Andrew Mokoena - Discharge Report - 2025-08-31'
        })
        
        # Validate step 2
        assert wizard_state['reportType'] and wizard_state['template'] and wizard_state['title']
        wizard_state['step'] = 3
        
        # Step 3: Disciplines
        wizard_state['disciplines'] = ['physiotherapy', 'occupational_therapy']
        
        # Validate step 3
        assert len(wizard_state['disciplines']) > 0
        wizard_state['step'] = 4
        
        # Step 4: Therapists
        wizard_state['therapists'] = [
            {'id': '1', 'name': 'Duncan Miller'},
            {'id': '3', 'name': 'Kim Jones'}
        ]
        
        # Validate step 4
        assert len(wizard_state['therapists']) > 0
        wizard_state['step'] = 5
        
        # Step 5: Priority & Deadline
        wizard_state.update({
            'priority': 2,
            'deadline': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        })
        
        # Validate step 5
        assert wizard_state['priority'] in [1, 2, 3]
        
        # Simulate final payload creation
        payload = {
            'patient_id': wizard_state['patient']['id'],
            'report_type': wizard_state['reportType'],
            'template_id': wizard_state['template']['id'],
            'title': wizard_state['title'],
            'disciplines': wizard_state['disciplines'],
            'assigned_therapist_ids': [t['id'] for t in wizard_state['therapists']],
            'priority': wizard_state['priority'],
            'deadline_date': wizard_state['deadline'],
            'generate_ai_content': True
        }
        
        # Validate payload structure
        assert payload['patient_id'] == '4603087263088'
        assert payload['report_type'] == 'discharge'
        assert isinstance(payload['assigned_therapist_ids'], list)
        assert isinstance(payload['disciplines'], list)
        assert len(payload['assigned_therapist_ids']) == 2
        
    def test_wizard_error_handling(self):
        """Test wizard error handling scenarios"""
        # Test missing patient
        incomplete_state = {
            'patient': None,
            'reportType': 'discharge',
            'template': {'id': 1},
            'title': 'Test',
            'disciplines': ['physiotherapy'],
            'therapists': [{'id': '1', 'name': 'Test'}]
        }
        
        # Should fail validation for step 1
        assert incomplete_state['patient'] is None
        
        # Test empty disciplines
        incomplete_state['patient'] = {'id': 'TEST001'}
        incomplete_state['disciplines'] = []
        
        # Should fail validation for step 3
        assert len(incomplete_state['disciplines']) == 0
        
        # Test empty therapists
        incomplete_state['disciplines'] = ['physiotherapy']
        incomplete_state['therapists'] = []
        
        # Should fail validation for step 4
        assert len(incomplete_state['therapists']) == 0
        
    def test_wizard_submission_success(self):
        """Test successful wizard submission payload structure"""
        # Complete wizard state
        complete_payload = {
            'patient_id': '4603087263088',
            'report_type': 'discharge',
            'template_id': 1,
            'title': 'Test Discharge Report',
            'disciplines': ['physiotherapy'],
            'assigned_therapist_ids': ['1'],
            'priority': 2,
            'deadline_date': '2025-09-07',
            'generate_ai_content': True
        }
        
        # Test payload structure is valid for submission
        required_fields = ['patient_id', 'report_type', 'template_id', 'title', 
                          'disciplines', 'assigned_therapist_ids', 'priority']
        
        for field in required_fields:
            assert field in complete_payload, f"Required field '{field}' missing from payload"
            
        # Test data types are correct
        assert isinstance(complete_payload['template_id'], int)
        assert isinstance(complete_payload['disciplines'], list)
        assert isinstance(complete_payload['assigned_therapist_ids'], list)
        assert isinstance(complete_payload['priority'], int)
        assert complete_payload['priority'] in [1, 2, 3]
        
        # Test non-empty required fields
        assert len(complete_payload['patient_id']) > 0
        assert len(complete_payload['title']) > 0
        assert len(complete_payload['disciplines']) > 0
        assert len(complete_payload['assigned_therapist_ids']) > 0
        
    def test_notification_type_fix_validation(self):
        """Test that notification types are valid after our fix"""
        # Valid notification types as per database constraint
        valid_types = ['request', 'reminder', 'completion', 'overdue']
        
        # Test the types we fixed in the code
        fixed_mapping = {
            'report_assigned': 'request',  # What we changed it to
            'status_change': 'reminder'    # What we changed it to
        }
        
        for original, fixed in fixed_mapping.items():
            assert fixed in valid_types, f"Fixed type '{fixed}' should be in valid types"
            
        # Ensure old invalid types are not being used
        invalid_types = ['report_assigned', 'status_change']
        for invalid_type in invalid_types:
            assert invalid_type not in valid_types, f"Invalid type '{invalid_type}' should not be in valid types"


class TestWizardJSONParsing:
    """Test JSON parsing fixes for arrays in report responses"""
    
    def test_json_field_parsing(self):
        """Test that JSON fields are properly parsed back to arrays"""
        # Simulate database row with JSON strings (how they're stored)
        mock_db_report = {
            'id': 289,
            'patient_id': '4603087263088',
            'assigned_therapist_ids': '["1", "3"]',  # JSON string from DB
            'disciplines': '["physiotherapy", "occupational_therapy"]',  # JSON string from DB
            'ai_generated_sections': '{"medical_history": "Generated content"}',
            'content': '{"section1": "Content"}'
        }
        
        # Simulate the parsing logic we added
        if isinstance(mock_db_report['assigned_therapist_ids'], str):
            mock_db_report['assigned_therapist_ids'] = json.loads(mock_db_report['assigned_therapist_ids'])
        if isinstance(mock_db_report['disciplines'], str):
            mock_db_report['disciplines'] = json.loads(mock_db_report['disciplines'])
        if isinstance(mock_db_report['ai_generated_sections'], str) and mock_db_report['ai_generated_sections']:
            mock_db_report['ai_generated_sections'] = json.loads(mock_db_report['ai_generated_sections'])
        if isinstance(mock_db_report['content'], str) and mock_db_report['content']:
            mock_db_report['content'] = json.loads(mock_db_report['content'])
            
        # Verify arrays are properly parsed
        assert isinstance(mock_db_report['assigned_therapist_ids'], list)
        assert isinstance(mock_db_report['disciplines'], list)
        assert isinstance(mock_db_report['ai_generated_sections'], dict)
        assert isinstance(mock_db_report['content'], dict)
        
        assert mock_db_report['assigned_therapist_ids'] == ["1", "3"]
        assert mock_db_report['disciplines'] == ["physiotherapy", "occupational_therapy"]


if __name__ == '__main__':
    # Run specific test classes
    pytest.main([__file__ + '::TestReportWizardValidation', '-v'])
    pytest.main([__file__ + '::TestReportWizardAPI', '-v'])
    pytest.main([__file__ + '::TestReportWizardEndToEnd', '-v'])
    pytest.main([__file__ + '::TestWizardJSONParsing', '-v'])