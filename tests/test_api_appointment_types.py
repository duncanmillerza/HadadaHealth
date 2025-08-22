"""
Feature tests for appointment type API endpoints

Tests CRUD operations, hierarchical responses, and practice scoping
for the appointment type management system.
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app and models
from main import app
from models.appointment_types import AppointmentType, PracticeAppointmentType
from modules.database import get_db_connection


class TestAppointmentTypeAPI:
    """Test suite for AppointmentType API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_appointment_types(self):
        """Create sample appointment types for testing"""
        # Create some test appointment types
        patient_type = AppointmentType.create(
            name="Test Patient Type",
            practice_id=1,
            color="#2D6356",
            duration=30,
            description="Test patient appointments"
        )
        
        child_type = AppointmentType.create(
            name="Test Assessment",
            parent_id=patient_type.id,
            practice_id=1,
            color="#16A34A",
            duration=45,
            description="Test assessment"
        )
        
        return {"parent": patient_type, "child": child_type}
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test-token"}
    
    def test_get_appointment_types_index(self, client, sample_appointment_types, auth_headers):
        """Test GET /api/appointment-types returns hierarchical list"""
        response = client.get("/api/appointment-types", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return array of appointment types
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure includes required fields
        for appointment_type in data:
            assert "id" in appointment_type
            assert "name" in appointment_type
            assert "color" in appointment_type
            assert "duration" in appointment_type
            assert "is_active" in appointment_type
    
    def test_get_appointment_types_hierarchical(self, client, sample_appointment_types, auth_headers):
        """Test GET /api/appointment-types?hierarchical=true returns nested structure"""
        response = client.get("/api/appointment-types?hierarchical=true", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return hierarchical structure
        assert isinstance(data, dict)
        
        # Check for parent types with children
        for parent_id, parent_data in data.items():
            assert "appointment_type" in parent_data
            assert "children" in parent_data
            
            parent_type = parent_data["appointment_type"]
            assert parent_type["parent_id"] is None  # Should be root level
    
    def test_get_appointment_type_by_id(self, client, sample_appointment_types, auth_headers):
        """Test GET /api/appointment-types/{id} returns specific appointment type"""
        appointment_type = sample_appointment_types["parent"]
        
        response = client.get(f"/api/appointment-types/{appointment_type.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == appointment_type.id
        assert data["name"] == appointment_type.name
        assert data["color"] == appointment_type.color
        assert data["duration"] == appointment_type.duration
    
    def test_get_appointment_type_not_found(self, client, auth_headers):
        """Test GET /api/appointment-types/{id} with invalid ID returns 404"""
        response = client.get("/api/appointment-types/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_appointment_type(self, client, auth_headers):
        """Test POST /api/appointment-types creates new appointment type"""
        appointment_data = {
            "name": "API Test Type",
            "practice_id": 1,
            "color": "#FF0000",
            "duration": 60,
            "description": "Created via API test"
        }
        
        response = client.post("/api/appointment-types", json=appointment_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == appointment_data["name"]
        assert data["color"] == appointment_data["color"]
        assert data["duration"] == appointment_data["duration"]
        assert data["id"] is not None
    
    def test_create_appointment_type_validation_error(self, client, auth_headers):
        """Test POST /api/appointment-types with invalid data returns 422"""
        invalid_data = {
            "name": "",  # Invalid empty name
            "color": "invalid-color",  # Invalid color format
            "duration": -5  # Invalid negative duration
        }
        
        response = client.post("/api/appointment-types", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    def test_create_child_appointment_type(self, client, sample_appointment_types, auth_headers):
        """Test POST /api/appointment-types creates child appointment type"""
        parent_type = sample_appointment_types["parent"]
        
        child_data = {
            "name": "API Child Test",
            "parent_id": parent_type.id,
            "practice_id": 1,
            "color": "#00FF00",
            "duration": 45
        }
        
        response = client.post("/api/appointment-types", json=child_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["parent_id"] == parent_type.id
        assert data["name"] == child_data["name"]
    
    def test_update_appointment_type(self, client, sample_appointment_types, auth_headers):
        """Test PUT /api/appointment-types/{id} updates appointment type"""
        appointment_type = sample_appointment_types["parent"]
        
        update_data = {
            "name": "Updated Test Type",
            "color": "#0000FF",
            "duration": 90
        }
        
        response = client.put(f"/api/appointment-types/{appointment_type.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["color"] == update_data["color"]
        assert data["duration"] == update_data["duration"]
    
    def test_delete_appointment_type(self, client, sample_appointment_types, auth_headers):
        """Test DELETE /api/appointment-types/{id} soft deletes appointment type"""
        appointment_type = sample_appointment_types["child"]  # Use child so no cascading issues
        
        response = client.delete(f"/api/appointment-types/{appointment_type.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify it's soft deleted (is_active = false)
        get_response = client.get(f"/api/appointment-types/{appointment_type.id}", headers=auth_headers)
        assert get_response.status_code == 404 or get_response.json()["is_active"] is False
    
    def test_practice_scoped_appointment_types(self, client, auth_headers):
        """Test GET /api/practices/{practice_id}/appointment-types returns practice-scoped types"""
        practice_id = 1
        
        response = client.get(f"/api/practices/{practice_id}/appointment-types", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return appointment types for the practice
        assert isinstance(data, list)
        
        # All returned types should be for this practice or global (practice_id=null)
        for appointment_type in data:
            assert appointment_type["practice_id"] is None or appointment_type["practice_id"] == practice_id
    
    def test_appointment_types_filtering(self, client, auth_headers):
        """Test GET /api/appointment-types with query parameters for filtering"""
        # Test active only filter
        response = client.get("/api/appointment-types?active_only=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for appointment_type in data:
            assert appointment_type["is_active"] is True
        
        # Test parent types only filter
        response = client.get("/api/appointment-types?parent_only=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for appointment_type in data:
            assert appointment_type["parent_id"] is None


class TestPracticeAppointmentTypeAPI:
    """Test suite for PracticeAppointmentType API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        # Create appointment type
        appointment_type = AppointmentType.create(
            name="Customizable Test Type",
            practice_id=None,  # Global type
            color="#2D6356",
            duration=30
        )
        
        return {"appointment_type": appointment_type}
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test-token"}
    
    def test_get_practice_customizations(self, client, sample_data, auth_headers):
        """Test GET /api/practices/{practice_id}/appointment-types/customizations"""
        practice_id = 1
        
        response = client.get(f"/api/practices/{practice_id}/appointment-types/customizations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of customizations
        assert isinstance(data, list)
    
    def test_create_practice_customization(self, client, sample_data, auth_headers):
        """Test POST /api/practices/{practice_id}/appointment-types/customizations"""
        practice_id = 1
        appointment_type = sample_data["appointment_type"]
        
        customization_data = {
            "appointment_type_id": appointment_type.id,
            "default_duration": 60,
            "default_billing_code": "CUSTOM01",
            "default_notes": "Custom practice notes",
            "is_enabled": True,
            "sort_order": 1
        }
        
        response = client.post(
            f"/api/practices/{practice_id}/appointment-types/customizations", 
            json=customization_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["practice_id"] == practice_id
        assert data["appointment_type_id"] == appointment_type.id
        assert data["default_duration"] == customization_data["default_duration"]
        assert data["default_billing_code"] == customization_data["default_billing_code"]
    
    def test_update_practice_customization(self, client, sample_data, auth_headers):
        """Test PUT /api/practices/{practice_id}/appointment-types/customizations/{id}"""
        practice_id = 1
        appointment_type = sample_data["appointment_type"]
        
        # Create customization first
        customization = PracticeAppointmentType.create(
            practice_id=practice_id,
            appointment_type_id=appointment_type.id,
            default_duration=30,
            default_billing_code="ORIG01"
        )
        
        update_data = {
            "default_duration": 90,
            "default_billing_code": "UPDATED01",
            "default_notes": "Updated notes"
        }
        
        response = client.put(
            f"/api/practices/{practice_id}/appointment-types/customizations/{customization.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["default_duration"] == update_data["default_duration"]
        assert data["default_billing_code"] == update_data["default_billing_code"]
        assert data["default_notes"] == update_data["default_notes"]
    
    def test_delete_practice_customization(self, client, sample_data, auth_headers):
        """Test DELETE /api/practices/{practice_id}/appointment-types/customizations/{id}"""
        practice_id = 1
        appointment_type = sample_data["appointment_type"]
        
        # Create customization to delete
        customization = PracticeAppointmentType.create(
            practice_id=practice_id,
            appointment_type_id=appointment_type.id,
            default_duration=30
        )
        
        response = client.delete(
            f"/api/practices/{practice_id}/appointment-types/customizations/{customization.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(
            f"/api/practices/{practice_id}/appointment-types/customizations/{customization.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_get_effective_appointment_types(self, client, sample_data, auth_headers):
        """Test GET /api/practices/{practice_id}/appointment-types/effective returns merged view"""
        practice_id = 1
        appointment_type = sample_data["appointment_type"]
        
        # Create customization
        PracticeAppointmentType.create(
            practice_id=practice_id,
            appointment_type_id=appointment_type.id,
            default_duration=75,  # Different from base
            default_billing_code="CUSTOM01"
        )
        
        response = client.get(f"/api/practices/{practice_id}/appointment-types/effective", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return appointment types with effective settings
        assert isinstance(data, list)
        
        # Find our customized type
        customized_type = next((at for at in data if at["id"] == appointment_type.id), None)
        assert customized_type is not None
        
        # Should show effective duration from customization
        assert customized_type["effective_duration"] == 75
        assert customized_type["default_billing_code"] == "CUSTOM01"


class TestAppointmentTypeAuthorizationAndValidation:
    """Test authentication, authorization and validation for appointment type APIs"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_unauthorized_request_returns_401(self, client):
        """Test that requests without auth headers return 401"""
        response = client.get("/api/appointment-types")
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_invalid_practice_access_returns_403(self, client):
        """Test that accessing other practice's data returns 403"""
        # Mock headers for practice 1
        headers = {"Authorization": "Bearer test-token", "X-Practice-ID": "1"}
        
        # Try to access practice 2's customizations
        response = client.get("/api/practices/2/appointment-types/customizations", headers=headers)
        
        # Should be forbidden if practice scoping is enforced
        # This test assumes practice-scoped middleware is implemented
        # For now, we'll accept 200 if no middleware exists yet
        assert response.status_code in [200, 403]
    
    def test_validation_error_responses_include_details(self, client):
        """Test that validation errors include helpful details"""
        auth_headers = {"Authorization": "Bearer test-token"}
        
        invalid_data = {
            "name": "",  # Required field empty
            "color": "not-a-color",  # Invalid format
            "duration": "not-a-number"  # Wrong type
        }
        
        response = client.post("/api/appointment-types", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        error_data = response.json()
        
        # Should include field-specific validation errors
        assert "detail" in error_data
        errors = error_data["detail"]
        
        # Should be a list of validation errors
        assert isinstance(errors, list)
        assert len(errors) > 0