# Python/FastAPI Code Style Guide

**Document Version:** 1.0  
**Date:** December 2024  
**Target:** HadadaHealth Python/FastAPI Codebase  
**Base Standard:** PEP 8 with FastAPI-specific conventions  

---

## Python-Specific Formatting

### **Indentation**
- **Use 4 spaces** for indentation (Python PEP 8 standard)
- Never use tabs
- Maintain consistent indentation throughout files
- Align nested structures for readability

```python
# Correct
def process_patient_data(patient_id: int):
    if patient_id:
        patient = get_patient_by_id(patient_id)
        if patient:
            return process_treatment_notes(patient)
    return None

# Incorrect - 2 spaces
def process_patient_data(patient_id: int):
  if patient_id:
    patient = get_patient_by_id(patient_id)
  return None
```

### **Naming Conventions**
- **Functions and Variables**: snake_case (`user_profile`, `calculate_total`)
- **Classes and Models**: PascalCase (`PatientCreateModel`, `TreatmentNote`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`, `API_KEY`)
- **Private Methods**: Leading underscore (`_internal_method`)
- **Modules**: lowercase with underscores (`treatment_notes`, `medical_aids`)

```python
# Correct naming
class PatientCreateModel(BaseModel):
    patient_name: str
    medical_aid_id: Optional[int] = None

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

def get_patient_summary(patient_id: int) -> Dict[str, Any]:
    return _fetch_patient_data(patient_id)

def _fetch_patient_data(patient_id: int) -> Dict:
    # Private helper method
    pass
```

### **String Formatting**
- **Use double quotes** for strings: `"Hello World"`
- Use single quotes only for strings containing double quotes: `'He said "Hello"'`
- Use f-strings for string interpolation: `f"Patient {patient_id} found"`
- Use triple quotes for docstrings: `"""Function description"""`

```python
# Correct
def create_patient_message(name: str, appointment_time: str) -> str:
    return f"Hello {name}, your appointment is at {appointment_time}"

def get_error_message() -> str:
    return 'The system said "Connection failed"'

def process_data():
    """
    Process patient data and return summary.
    
    Returns:
        Dict[str, Any]: Patient summary data
    """
    pass
```

### **Import Organization**
Group imports in this order with blank lines between groups:

1. **Standard library imports**
2. **Third-party imports**
3. **Local application imports**

```python
# Standard library
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

# Third-party
import bcrypt
import httpx
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

# Local
from modules.database import get_db_connection
from modules.patients import Patient, get_patient_by_id
```

---

## FastAPI-Specific Conventions

### **Endpoint Definitions**
- Use clear, descriptive endpoint names
- Include proper HTTP method decorators
- Add response models for documentation
- Include status codes for non-200 responses

```python
@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int = Path(..., description="Patient ID"),
    current_user: User = Depends(get_current_user)
) -> PatientResponse:
    """
    Retrieve patient information by ID.
    
    Args:
        patient_id: Unique identifier for the patient
        current_user: Authenticated user making the request
        
    Returns:
        PatientResponse: Patient data with medical history
        
    Raises:
        HTTPException: 404 if patient not found
    """
    patient = get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse(**patient)
```

### **Pydantic Models**
- Use descriptive class names with Model suffix
- Include field descriptions for API documentation
- Add validation where appropriate
- Use Optional for nullable fields

```python
class PatientCreateModel(BaseModel):
    """Model for creating a new patient record."""
    
    patient_name: str = Field(..., description="Full name of the patient", min_length=1)
    email: Optional[EmailStr] = Field(None, description="Patient email address")
    phone_number: Optional[str] = Field(None, description="Primary contact number")
    medical_aid_id: Optional[int] = Field(None, description="Medical aid scheme ID")
    date_of_birth: Optional[datetime] = Field(None, description="Patient date of birth")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "patient_name": "John Smith",
                "email": "john.smith@example.com",
                "phone_number": "+27123456789",
                "medical_aid_id": 1
            }
        }
```

### **Error Handling**
- Use HTTPException for API errors
- Include descriptive error messages
- Log errors appropriately
- Return consistent error format

```python
def get_patient_by_id(patient_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve patient by ID with proper error handling.
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Optional[Dict]: Patient data or None if not found
        
    Raises:
        HTTPException: For database connection errors
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM patients WHERE id = ?", 
                (patient_id,)
            )
            result = cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None
            
    except sqlite3.Error as e:
        logging.error(f"Database error fetching patient {patient_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Database connection error"
        )
```

---

## Database and SQL Conventions

### **Query Formatting**
- Use parameterized queries (never string formatting)
- Format multi-line queries for readability
- Include proper error handling
- Use meaningful variable names

```python
# Correct - parameterized and readable
def get_patient_appointments(patient_id: int, start_date: datetime) -> List[Dict]:
    """Get all appointments for a patient from a given date."""
    query = """
        SELECT 
            b.id,
            b.appointment_datetime,
            b.duration_minutes,
            t.name as therapist_name,
            t.profession
        FROM bookings b
        JOIN therapists t ON b.therapist_id = t.id
        WHERE b.patient_id = ? 
            AND b.appointment_datetime >= ?
        ORDER BY b.appointment_datetime ASC
    """
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (patient_id, start_date))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Incorrect - SQL injection risk
def get_patient_appointments_bad(patient_id: int) -> List[Dict]:
    query = f"SELECT * FROM bookings WHERE patient_id = {patient_id}"  # NEVER DO THIS
    # ... dangerous code
```

### **Connection Management**
- Always use context managers
- Handle connection errors gracefully
- Log database operations appropriately

```python
def create_patient_record(patient_data: Dict[str, Any]) -> str:
    """Create new patient record with proper connection handling."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert patient record
            cursor.execute("""
                INSERT INTO patients (name, email, phone, medical_aid_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                patient_data["name"],
                patient_data.get("email"),
                patient_data.get("phone"),
                patient_data.get("medical_aid_id"),
                datetime.now()
            ))
            
            patient_id = cursor.lastrowid
            conn.commit()
            
            logging.info(f"Created patient record with ID: {patient_id}")
            return f"Patient created successfully with ID: {patient_id}"
            
    except sqlite3.IntegrityError as e:
        logging.error(f"Patient creation failed - integrity error: {e}")
        raise HTTPException(status_code=400, detail="Patient data conflicts with existing records")
        
    except sqlite3.Error as e:
        logging.error(f"Database error creating patient: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
```

---

## Frontend Code Conventions

### **JavaScript Style** (Current Vanilla JS)
- Use `const` for unchanging values, `let` for variables
- Use camelCase for variables and functions
- Use PascalCase for constructors/classes
- Add comments for complex logic

```javascript
// Correct
const MAX_RETRY_ATTEMPTS = 3;
let currentPatientId = null;

function fetchPatientData(patientId) {
    // Fetch patient data from API
    const apiUrl = `/api/patients/${patientId}`;
    
    return fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error("Failed to fetch patient data:", error);
            throw error;
        });
}

class PatientManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.patients = [];
    }
    
    async loadPatients() {
        // Load and display patients
        try {
            this.patients = await fetchPatientData();
            this.render();
        } catch (error) {
            this.showError("Failed to load patients");
        }
    }
}
```

### **HTML Structure**
- Use semantic HTML5 elements
- Include proper accessibility attributes
- Use 2-space indentation for HTML (web standard)
- Include meaningful class names

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Patient Dashboard - HadadaHealth</title>
  <link rel="stylesheet" href="/static/main.css">
</head>
<body>
  <header class="main-header">
    <nav class="primary-navigation" role="navigation" aria-label="Main navigation">
      <ul class="nav-list">
        <li class="nav-item">
          <a href="/dashboard" class="nav-link" aria-current="page">Dashboard</a>
        </li>
        <li class="nav-item">
          <a href="/patients" class="nav-link">Patients</a>
        </li>
      </ul>
    </nav>
  </header>
  
  <main class="main-content">
    <section class="patient-section">
      <h1 class="section-title">Patient Management</h1>
      
      <div class="patient-grid" role="grid" aria-label="Patient list">
        <!-- Patient cards generated here -->
      </div>
    </section>
  </main>
</body>
</html>
```

### **CSS/SCSS Conventions**
- Use 2-space indentation
- Use kebab-case for class names
- Group related properties
- Use meaningful selector names

```css
/* Component-based naming */
.patient-card {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background-color: #ffffff;
  transition: box-shadow 0.2s ease;
}

.patient-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.patient-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.patient-card__name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.patient-card__id {
  font-size: 0.875rem;
  color: #6b7280;
  font-family: monospace;
}
```

---

## Documentation Standards

### **Function/Method Documentation**
Use Google-style docstrings for Python functions:

```python
def calculate_treatment_cost(
    procedure_codes: List[str], 
    medical_aid_rate: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate total treatment cost based on procedure codes and medical aid rates.
    
    This function processes a list of procedure codes and calculates the total
    cost considering medical aid coverage rates and co-payment requirements.
    
    Args:
        procedure_codes: List of medical procedure codes to bill
        medical_aid_rate: Optional medical aid coverage rate (0.0 to 1.0)
            Defaults to None for private patients
    
    Returns:
        Dict containing:
            - total_amount: Total cost before medical aid
            - covered_amount: Amount covered by medical aid
            - patient_portion: Amount patient must pay
            - procedure_breakdown: List of individual procedure costs
    
    Raises:
        ValueError: If procedure codes are invalid
        HTTPException: If medical aid rate calculation fails
    
    Example:
        >>> codes = ["99213", "97110"]
        >>> result = calculate_treatment_cost(codes, medical_aid_rate=0.8)
        >>> print(result["patient_portion"])
        45.50
    """
    # Implementation here
    pass
```

### **API Endpoint Documentation**
Include comprehensive FastAPI documentation:

```python
@app.post(
    "/api/patients/{patient_id}/appointments",
    response_model=AppointmentResponse,
    status_code=201,
    summary="Create new patient appointment",
    description="Create a new appointment for an existing patient with specified therapist and time slot.",
    responses={
        201: {"description": "Appointment created successfully"},
        400: {"description": "Invalid appointment data or scheduling conflict"},
        404: {"description": "Patient or therapist not found"},
        422: {"description": "Validation error in request data"}
    },
    tags=["appointments"]
)
async def create_patient_appointment(
    patient_id: int = Path(..., description="ID of the patient", example=123),
    appointment_data: AppointmentCreateModel = Body(..., description="Appointment details"),
    current_user: User = Depends(get_current_authenticated_user)
) -> AppointmentResponse:
    """
    Create a new appointment for a patient.
    
    This endpoint creates a new appointment booking for an existing patient.
    It validates therapist availability, checks for scheduling conflicts,
    and sends confirmation notifications.
    
    **Business Rules:**
    - Patient must exist in the system
    - Therapist must be available at requested time
    - No overlapping appointments allowed
    - Minimum 15-minute appointment duration required
    
    **Notifications:**
    - Patient receives SMS/email confirmation
    - Therapist receives calendar update
    - Reminder notifications scheduled automatically
    """
    # Implementation here
    pass
```

---

## Testing Conventions

### **Test Structure and Naming**
- Test files: `test_module_name.py`
- Test functions: `test_function_name_expected_behavior`
- Test classes: `TestClassName`
- Use descriptive test names explaining the scenario

```python
# test_patients.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestPatientEndpoints:
    """Test cases for patient management endpoints."""
    
    def test_get_patient_by_id_returns_patient_data(self):
        """Test that GET /api/patients/{id} returns correct patient data."""
        # Arrange
        patient_id = 1
        
        # Act
        response = client.get(f"/api/patients/{patient_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient_id
        assert "patient_name" in data
        assert "created_at" in data
    
    def test_get_patient_by_id_returns_404_when_not_found(self):
        """Test that GET /api/patients/{id} returns 404 for non-existent patient."""
        # Arrange
        non_existent_id = 99999
        
        # Act
        response = client.get(f"/api/patients/{non_existent_id}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.parametrize("invalid_id", [-1, 0, "abc", None])
    def test_get_patient_by_id_handles_invalid_input(self, invalid_id):
        """Test that endpoint handles various invalid ID inputs gracefully."""
        response = client.get(f"/api/patients/{invalid_id}")
        assert response.status_code in [400, 422, 404]
```

### **Test Data and Fixtures**
Use pytest fixtures for consistent test data:

```python
# conftest.py
import pytest
import tempfile
import sqlite3
from modules.database import init_test_database

@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp_file:
        db_path = tmp_file.name
        init_test_database(db_path)
        yield db_path

@pytest.fixture
def sample_patient_data():
    """Provide sample patient data for testing."""
    return {
        "patient_name": "John Smith",
        "email": "john.smith@example.com",
        "phone_number": "+27123456789",
        "medical_aid_id": 1,
        "date_of_birth": "1980-05-15"
    }

@pytest.fixture
def authenticated_client():
    """Provide authenticated test client."""
    with TestClient(app) as client:
        # Login and get session
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert response.status_code == 200
        yield client
```

---

## Configuration and Environment

### **Environment Variable Naming**
- Use UPPER_SNAKE_CASE for environment variables
- Group related variables with prefixes
- Provide sensible defaults where possible
- Document all required variables

```python
# modules/config.py
import os
from typing import Optional

class Config:
    """Application configuration loaded from environment variables."""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/bookings.db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    
    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY")  # Required, no default
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))
    
    # External API Configuration
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    MAX_DAILY_AI_REQUESTS: int = int(os.getenv("MAX_DAILY_AI_REQUESTS", "100"))
    
    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration is present."""
        required_vars = ["SECRET_KEY"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
```

---

## Error Handling and Logging

### **Logging Standards**
- Use structured logging with context
- Include appropriate log levels
- Log security-relevant events
- Avoid logging sensitive data

```python
import logging
import structlog
from typing import Any, Dict

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_patient(patient_data: Dict[str, Any]) -> str:
    """Create patient with proper logging."""
    logger.info(
        "Creating patient record",
        action="create_patient",
        patient_name=patient_data.get("patient_name"),
        has_email=bool(patient_data.get("email")),
        medical_aid_id=patient_data.get("medical_aid_id")
    )
    
    try:
        # Create patient logic here
        patient_id = _insert_patient_record(patient_data)
        
        logger.info(
            "Patient created successfully",
            action="create_patient_success",
            patient_id=patient_id,
            duration_ms=125  # Example timing
        )
        
        return f"Patient created with ID: {patient_id}"
        
    except Exception as e:
        logger.error(
            "Failed to create patient",
            action="create_patient_error",
            error=str(e),
            error_type=type(e).__name__,
            patient_name=patient_data.get("patient_name")
        )
        raise HTTPException(status_code=500, detail="Patient creation failed")
```

---

## Summary of Key Changes from Agent OS Standards

### **Major Adaptations for Python/FastAPI:**

1. **Indentation**: 4 spaces (not 2) - Python PEP 8 standard
2. **String Quotes**: Double quotes (not single) - Python convention
3. **Naming**: snake_case for functions, PascalCase for classes - Python standard
4. **Documentation**: Google-style docstrings (not JSDoc)
5. **Error Handling**: HTTPException and structured logging
6. **Database**: Parameterized queries with SQLite/PostgreSQL
7. **Testing**: pytest with FastAPI TestClient
8. **Configuration**: Environment variables with validation

### **Maintained from Agent OS Standards:**
- Clear code organization and structure
- Comprehensive documentation requirements
- Security-first approach to development
- Consistent naming conventions within language
- Proper error handling and logging

This style guide maintains the quality and consistency principles from your Agent OS standards while adapting them appropriately for your Python/FastAPI healthcare platform.