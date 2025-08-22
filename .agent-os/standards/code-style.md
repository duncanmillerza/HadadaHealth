# Code Style Guide

## Context

Global code style rules for Agent OS projects - Python/FastAPI focused.

<conditional-block context-check="general-formatting">
IF this General Formatting section already read in current context:
  SKIP: Re-reading this section
  NOTE: "Using General Formatting rules already in context"
ELSE:
  READ: The following formatting rules

## General Formatting

### Indentation
- Use 4 spaces for indentation (Python PEP 8 standard)
- Never use tabs
- Maintain consistent indentation throughout files
- Align nested structures for readability

### Naming Conventions
- **Functions and Variables**: Use snake_case (e.g., `user_profile`, `calculate_total`)
- **Classes and Models**: Use PascalCase (e.g., `UserProfile`, `PaymentProcessor`, `PatientCreateModel`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`, `API_KEY`)
- **Private Methods**: Leading underscore (e.g., `_internal_method`)
- **Modules**: lowercase with underscores (e.g., `treatment_notes`, `medical_aids`)

### String Formatting
- Use double quotes for strings: `"Hello World"`
- Use single quotes only for strings containing double quotes: `'He said "Hello"'`
- Use f-strings for interpolation: `f"Patient {patient_id} found"`
- Use triple quotes for docstrings: `"""Function description"""`

### Code Comments
- Add brief comments above non-obvious business logic
- Document complex algorithms or calculations
- Explain the "why" behind implementation choices
- Never remove existing comments unless removing the associated code
- Update comments when modifying code to maintain accuracy
- Keep comments concise and relevant

### Import Organization
Group imports in this order with blank lines between groups:
1. Standard library imports
2. Third-party imports  
3. Local application imports

```python
# Standard library
import json
import logging
from datetime import datetime
from typing import List, Optional

# Third-party
import bcrypt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local
from modules.database import get_db_connection
from modules.patients import get_patient_by_id
```
</conditional-block>

<conditional-block task-condition="python-fastapi" context-check="python-fastapi-style">
IF current task involves writing or updating Python/FastAPI code:
  READ: The following Python/FastAPI specific conventions

## Python/FastAPI Conventions

### Endpoint Definitions
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

### Pydantic Models
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
    
    class Config:
        schema_extra = {
            "example": {
                "patient_name": "John Smith",
                "email": "john.smith@example.com",
                "phone_number": "+27123456789"
            }
        }
```

### Database Operations
- Use parameterized queries (never string formatting)
- Always use context managers for connections
- Handle database errors gracefully
- Log database operations appropriately

```python
def get_patient_by_id(patient_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve patient by ID with proper error handling."""
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
        raise HTTPException(status_code=500, detail="Database connection error")
```

### Documentation Standards
Use Google-style docstrings for Python functions:

```python
def calculate_treatment_cost(
    procedure_codes: List[str], 
    medical_aid_rate: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate total treatment cost based on procedure codes.
    
    Args:
        procedure_codes: List of medical procedure codes to bill
        medical_aid_rate: Optional medical aid coverage rate (0.0 to 1.0)
    
    Returns:
        Dict containing total_amount, covered_amount, patient_portion
    
    Raises:
        ValueError: If procedure codes are invalid
        HTTPException: If medical aid rate calculation fails
    """
    pass
```

### Error Handling
- Use HTTPException for API errors
- Include descriptive error messages
- Log errors appropriately
- Return consistent error format

### Testing Conventions
- Test files: `test_module_name.py`
- Test functions: `test_function_name_expected_behavior`
- Use descriptive test names explaining the scenario
- Use pytest fixtures for consistent test data

```python
def test_get_patient_by_id_returns_patient_data():
    """Test that GET /api/patients/{id} returns correct patient data."""
    # Arrange
    patient_id = 1
    
    # Act
    response = client.get(f"/api/patients/{patient_id}")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == patient_id
```
</conditional-block>

<conditional-block task-condition="html-css-tailwind" context-check="html-css-style">
IF current task involves writing or updating HTML, CSS, or TailwindCSS:
  READ: The following frontend conventions

## Frontend Conventions

### HTML Structure
- Use semantic HTML5 elements
- Include proper accessibility attributes  
- Use 2-space indentation for HTML
- Include meaningful class names

### JavaScript Style (Vanilla JS)
- Use `const` for unchanging values, `let` for variables
- Use camelCase for variables and functions
- Use PascalCase for constructors/classes
- Add comments for complex logic

### CSS Conventions
- Use 2-space indentation
- Use kebab-case for class names
- Group related properties
- Use meaningful selector names
</conditional-block>
