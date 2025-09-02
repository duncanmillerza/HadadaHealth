"""
Test Suite for Template Customization System

Tests for template creation, field type management, validation, permissions,
versioning, and approval workflows for the AI report writing system.
"""
import pytest
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from modules.database import get_db_connection, execute_query
from modules.reports import ReportWorkflowService
from controllers.report_controller import (
    create_custom_template, update_template, get_template_by_id,
    validate_template_schema, preview_template, get_practice_templates,
    approve_template, create_template_version, get_template_history
)

class TestTemplateCreation:
    """Test suite for template creation functionality"""

    def setup_method(self):
        """Set up test environment before each test"""
        self.test_template_data = {
            "name": "Test Custom Template",
            "description": "Template for testing purposes",
            "template_type": "custom",
            "practice_id": "test_practice_123",
            "fields_schema": {
                "patient_info": {
                    "type": "auto_populated",
                    "label": "Patient Information",
                    "required": True,
                    "fields": ["name", "date_of_birth", "patient_id"]
                },
                "assessment_text": {
                    "type": "rich_text", 
                    "label": "Assessment",
                    "required": True,
                    "placeholder": "Enter assessment details..."
                },
                "multiple_choice_question": {
                    "type": "multiple_choice",
                    "label": "Treatment Response",
                    "required": True,
                    "options": ["Excellent", "Good", "Fair", "Poor"],
                    "default": "Good"
                },
                "signature_field": {
                    "type": "digital_signature",
                    "label": "Therapist Signature",
                    "required": True
                }
            },
            "section_order": [
                "patient_info", 
                "assessment_text",
                "multiple_choice_question", 
                "signature_field"
            ],
            "created_by_user_id": "test_user_123"
        }

    def test_create_template_success(self):
        """Test successful template creation"""
        with patch('controllers.report_controller.create_report_template') as mock_create:
            mock_create.return_value = 42
            
            result = create_custom_template(**self.test_template_data)
            
            assert result["success"] is True
            assert result["template_id"] == 42
            mock_create.assert_called_once()

    def test_create_template_invalid_schema(self):
        """Test template creation with invalid field schema"""
        invalid_data = self.test_template_data.copy()
        invalid_data["fields_schema"] = {
            "invalid_field": {
                "type": "nonexistent_type",  # Invalid field type
                "label": "Invalid Field"
            }
        }
        
        result = create_custom_template(**invalid_data)
        
        assert result["success"] is False
        assert "unsupported type" in result["error"]

    def test_create_template_missing_required_fields(self):
        """Test template creation with missing required fields"""
        incomplete_data = {
            "name": "Incomplete Template",
            # Missing required fields: template_type, fields_schema, etc.
        }
        
        with pytest.raises(TypeError):
            create_custom_template(**incomplete_data)

    def test_create_template_duplicate_name(self):
        """Test template creation with duplicate name"""
        with patch('controllers.report_controller.create_report_template') as mock_create:
            mock_create.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
            
            result = create_custom_template(**self.test_template_data)
            
            assert result["success"] is False
            assert "already exists" in result["error"]


class TestFieldTypeManagement:
    """Test suite for field type system functionality"""

    def test_supported_field_types(self):
        """Test all supported field types are recognized"""
        supported_types = {
            "auto_populated": {},
            "ai_generated_paragraph": {"ai_source": "treatment_notes"}, 
            "rich_text": {},
            "structured_table": {"columns": ["col1", "col2"]},
            "structured_fields": {},
            "digital_signature": {},
            "multiple_choice": {"options": ["Option 1", "Option 2"]},
            "checklist": {},
            "dynamic_sections": {},
            "multi_signature": {},
            "paragraph": {},
            "date_picker": {},
            "number_input": {}
        }
        
        for field_type, extra_props in supported_types.items():
            field_config = {
                "type": field_type,
                "label": f"Test {field_type}",
                "required": True,
                **extra_props
            }
            
            result = validate_template_schema({"test_field": field_config})
            assert result["valid"] is True, f"Field type {field_type} failed validation: {result.get('errors', [])}"

    def test_field_type_specific_validation(self):
        """Test validation specific to different field types"""
        # Test multiple_choice requires options
        mc_field = {
            "type": "multiple_choice",
            "label": "Multiple Choice",
            "required": True,
            "options": ["Option 1", "Option 2", "Option 3"]
        }
        result = validate_template_schema({"mc_field": mc_field})
        assert result["valid"] is True
        
        # Test multiple_choice without options fails
        mc_field_invalid = {
            "type": "multiple_choice",
            "label": "Multiple Choice",
            "required": True
            # Missing options
        }
        result = validate_template_schema({"mc_field": mc_field_invalid})
        assert result["valid"] is False

    def test_structured_table_validation(self):
        """Test structured table field validation"""
        table_field = {
            "type": "structured_table",
            "label": "Outcome Measures",
            "required": True,
            "columns": ["measure", "score", "date", "notes"]
        }
        
        result = validate_template_schema({"table_field": table_field})
        assert result["valid"] is True

    def test_ai_generated_field_validation(self):
        """Test AI generated field validation"""
        ai_field = {
            "type": "ai_generated_paragraph",
            "label": "Medical History",
            "required": True,
            "ai_source": "treatment_notes",
            "editable": True
        }
        
        result = validate_template_schema({"ai_field": ai_field})
        assert result["valid"] is True

    def test_digital_signature_validation(self):
        """Test digital signature field validation"""
        sig_field = {
            "type": "digital_signature", 
            "label": "Therapist Signature",
            "required": True,
            "capture_credentials": True
        }
        
        result = validate_template_schema({"sig_field": sig_field})
        assert result["valid"] is True


class TestTemplateValidationAndPreview:
    """Test suite for template validation and preview functionality"""

    def test_template_schema_validation_success(self):
        """Test successful template schema validation"""
        valid_schema = {
            "patient_demographics": {
                "type": "auto_populated",
                "label": "Patient Information", 
                "required": True,
                "fields": ["name", "date_of_birth"]
            },
            "assessment": {
                "type": "rich_text",
                "label": "Clinical Assessment",
                "required": True,
                "placeholder": "Enter assessment..."
            }
        }
        
        result = validate_template_schema(valid_schema)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_template_schema_validation_failures(self):
        """Test template schema validation with various errors"""
        invalid_schema = {
            "field1": {
                "type": "invalid_type",  # Invalid field type
                "label": "Invalid Field"
            },
            "field2": {
                "type": "rich_text"
                # Missing required 'label' property
            },
            "field3": {
                "type": "multiple_choice",
                "label": "Choice Field",
                "required": True
                # Missing 'options' for multiple choice
            }
        }
        
        result = validate_template_schema(invalid_schema)
        
        assert result["valid"] is False
        assert len(result["errors"]) >= 3

    def test_template_preview_generation(self):
        """Test template preview HTML generation"""
        template_data = {
            "name": "Test Template",
            "fields_schema": {
                "patient_info": {
                    "type": "auto_populated",
                    "label": "Patient Information",
                    "required": True
                },
                "notes": {
                    "type": "rich_text",
                    "label": "Clinical Notes", 
                    "required": True,
                    "placeholder": "Enter notes..."
                }
            },
            "section_order": ["patient_info", "notes"]
        }
        
        result = preview_template(template_data)
        
        assert result["success"] is True
        assert "preview_html" in result
        assert "Patient Information" in result["preview_html"]
        assert "Clinical Notes" in result["preview_html"]

    def test_template_preview_with_sample_data(self):
        """Test template preview with sample data populated"""
        template_data = {
            "name": "Test Template",
            "fields_schema": {
                "patient_info": {
                    "type": "auto_populated",
                    "label": "Patient Information",
                    "required": True
                }
            },
            "section_order": ["patient_info"]
        }
        
        sample_data = {
            "patient_info": {
                "name": "John Doe",
                "date_of_birth": "1980-01-15",
                "patient_id": "P123456"
            }
        }
        
        result = preview_template(template_data, sample_data)
        
        assert result["success"] is True
        assert "John Doe" in result["preview_html"]


class TestPracticeSpecificTemplates:
    """Test suite for practice-specific template storage and permissions"""

    def test_get_practice_templates_filters_correctly(self):
        """Test that practice templates are filtered by practice_id"""
        with patch('controllers.report_controller.get_report_templates') as mock_get:
            mock_get.return_value = [
                {
                    "id": 1,
                    "name": "Practice Template 1",
                    "practice_id": "practice_123",
                    "is_system_default": False
                },
                {
                    "id": 2,
                    "name": "System Template",
                    "practice_id": None,
                    "is_system_default": True
                }
            ]
            
            result = get_practice_templates("practice_123")
            
            assert len(result) == 2  # Practice template + system templates
            mock_get.assert_called_with(practice_id="practice_123")

    def test_practice_template_creation_permissions(self):
        """Test that only authorized users can create practice templates"""
        template_data = {
            "name": "Practice Template",
            "template_type": "custom",
            "practice_id": "practice_123",
            "fields_schema": {"field1": {"type": "rich_text", "label": "Test"}},
            "section_order": ["field1"],
            "created_by_user_id": "user_123"
        }
        
        with patch('controllers.report_controller.user_has_permission') as mock_perm:
            mock_perm.return_value = True
            
            with patch('controllers.report_controller.create_report_template') as mock_create:
                mock_create.return_value = 42
                
                result = create_custom_template(**template_data)
                
                assert result["success"] is True
                mock_perm.assert_called_with("user_123", "create_template", "practice_123")

    def test_practice_template_access_permissions(self):
        """Test that users can only access authorized practice templates"""
        with patch('controllers.report_controller.user_has_practice_access') as mock_access:
            mock_access.return_value = False
            
            result = get_practice_templates("unauthorized_practice")
            
            assert result["success"] is False
            assert "permission" in result["error"].lower()


class TestTemplateVersioningAndApproval:
    """Test suite for template versioning and approval workflow"""

    def test_create_template_version(self):
        """Test creating a new template version"""
        version_data = {
            "template_id": 1,
            "changes": {
                "fields_schema": {
                    "new_field": {
                        "type": "rich_text",
                        "label": "New Field",
                        "required": False
                    }
                }
            },
            "change_summary": "Added new field for additional notes",
            "created_by_user_id": "user_123"
        }
        
        with patch('controllers.report_controller.create_template_version_record') as mock_create:
            mock_create.return_value = 2  # New version number
            
            result = create_template_version(**version_data)
            
            assert result["success"] is True
            assert result["version_number"] == 2

    def test_template_approval_workflow(self):
        """Test template approval workflow"""
        approval_data = {
            "template_id": 1,
            "version_number": 2,
            "approved_by_user_id": "manager_123",
            "approval_notes": "Approved for production use"
        }
        
        with patch('controllers.report_controller.approve_template_version') as mock_approve:
            mock_approve.return_value = True
            
            result = approve_template(**approval_data)
            
            assert result["success"] is True
            mock_approve.assert_called_once()

    def test_template_version_history(self):
        """Test retrieving template version history"""
        with patch('controllers.report_controller.get_template_version_history') as mock_history:
            mock_history.return_value = [
                {
                    "version_number": 1,
                    "created_at": "2025-08-28T10:00:00",
                    "created_by": "user_123",
                    "change_summary": "Initial version"
                },
                {
                    "version_number": 2,
                    "created_at": "2025-08-31T14:30:00", 
                    "created_by": "user_456",
                    "change_summary": "Added new field"
                }
            ]
            
            result = get_template_history(1)
            
            assert len(result) == 2
            assert result[0]["version_number"] == 1
            assert result[1]["version_number"] == 2

    def test_revert_to_previous_version(self):
        """Test reverting template to previous version"""
        with patch('controllers.report_controller.revert_template_version') as mock_revert:
            mock_revert.return_value = True
            
            result = revert_template_version(1, 1, "user_123", "Reverting due to issues")
            
            assert result["success"] is True
            mock_revert.assert_called_once()


class TestTemplatePermissionsAndSecurity:
    """Test suite for template permissions and security"""

    def test_template_access_by_role(self):
        """Test template access permissions by user role"""
        test_cases = [
            ("admin", True, True, True),      # Admin: create, edit, approve
            ("manager", True, True, True),    # Manager: create, edit, approve
            ("therapist", False, False, False) # Therapist: read-only
        ]
        
        for role, can_create, can_edit, can_approve in test_cases:
            with patch('controllers.report_controller.get_user_role') as mock_role:
                mock_role.return_value = role
                
                create_result = check_template_permission("user_123", "create")
                edit_result = check_template_permission("user_123", "edit")
                approve_result = check_template_permission("user_123", "approve")
                
                assert create_result == can_create
                assert edit_result == can_edit
                assert approve_result == can_approve

    def test_template_data_sanitization(self):
        """Test that template data is properly sanitized"""
        malicious_data = {
            "name": "<script>alert('xss')</script>Test Template",
            "description": "Template with <script>malicious code</script>",
            "fields_schema": {
                "field1": {
                    "type": "rich_text",
                    "label": "<script>alert('xss')</script>Field",
                    "placeholder": "Safe placeholder"
                }
            }
        }
        
        with patch('controllers.report_controller.sanitize_template_data') as mock_sanitize:
            mock_sanitize.return_value = {
                "name": "Test Template",
                "description": "Template with malicious code",
                "fields_schema": {
                    "field1": {
                        "type": "rich_text", 
                        "label": "Field",
                        "placeholder": "Safe placeholder"
                    }
                }
            }
            
            result = create_custom_template(**malicious_data)
            mock_sanitize.assert_called_once()


class TestTemplateIntegrationTests:
    """Integration tests for template customization system"""

    def test_end_to_end_template_creation_workflow(self):
        """Test complete template creation workflow"""
        # 1. Create template
        template_data = {
            "name": "Integration Test Template",
            "template_type": "custom",
            "practice_id": "practice_123",
            "fields_schema": {
                "assessment": {
                    "type": "rich_text",
                    "label": "Assessment",
                    "required": True
                }
            },
            "section_order": ["assessment"],
            "created_by_user_id": "user_123"
        }
        
        with patch('controllers.report_controller.create_report_template') as mock_create:
            mock_create.return_value = 42
            
            # 2. Create template
            create_result = create_custom_template(**template_data)
            assert create_result["success"] is True
            template_id = create_result["template_id"]
            
            # 3. Validate template
            with patch('controllers.report_controller.get_template_by_id') as mock_get:
                mock_get.return_value = {
                    "id": template_id,
                    "name": "Integration Test Template",
                    "fields_schema": template_data["fields_schema"]
                }
                
                validation_result = validate_template_schema(template_data["fields_schema"])
                assert validation_result["valid"] is True
            
            # 4. Preview template
            preview_result = preview_template(template_data)
            assert preview_result["success"] is True

    def test_template_usage_in_report_creation(self):
        """Test using custom template in report creation"""
        template_id = 42
        
        with patch('modules.reports.ReportWorkflowService.get_available_templates') as mock_templates:
            mock_templates.return_value = [{
                "id": template_id,
                "name": "Custom Template",
                "fields_schema": {
                    "assessment": {
                        "type": "rich_text",
                        "label": "Assessment", 
                        "required": True
                    }
                }
            }]
            
            templates = ReportWorkflowService.get_available_templates("practice_123")
            
            assert len(templates) == 1
            assert templates[0]["id"] == template_id

if __name__ == "__main__":
    pytest.main([__file__, "-v"])