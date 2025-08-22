# Agent Instructions for HadadaHealth Development

**Version**: 1.0  
**Agent OS Framework**: Compatible  
**Last Updated**: August 2025  
**Scope**: Development Guidelines and Standards

---

## Overview

This document provides comprehensive instructions for AI agents working on the HadadaHealth healthcare practice management system. These guidelines ensure consistent, secure, and high-quality development practices while maintaining compliance with healthcare regulations and clinical standards.

---

## Product Context

### **System Description**
HadadaHealth is a comprehensive healthcare practice management system designed for physiotherapists and allied health professionals in South Africa. The system combines patient management, appointment scheduling, clinical documentation, AI-powered insights, billing, and analytics in a single integrated platform.

### **Key Characteristics**
- **Healthcare Domain**: Clinical documentation, patient data, outcome measures
- **Regulatory Environment**: POPIA/GDPR compliance, healthcare data protection
- **User Base**: Healthcare professionals (physiotherapists, practice managers)
- **Technology Stack**: FastAPI (Python), SQLite database, HTML/CSS/JavaScript
- **Security Requirements**: Healthcare-grade data protection and audit trails

### **Business Criticality**
- **High**: Patient data security and privacy
- **High**: Clinical documentation accuracy and completeness  
- **High**: System reliability and availability
- **Medium**: Performance optimization and scalability
- **Medium**: User experience and workflow efficiency

---

## Development Principles

### **1. Healthcare-First Development**
- **Patient Safety**: All changes must prioritize patient data integrity and safety
- **Clinical Accuracy**: Ensure all clinical calculations and assessments are precise
- **Regulatory Compliance**: Maintain POPIA/GDPR compliance in all implementations
- **Audit Trail**: Every change must maintain comprehensive logging and traceability
- **Evidence-Based**: Support clinical best practices and evidence-based care

### **2. Security-Centric Approach**
- **Data Protection**: Healthcare data requires enhanced security measures
- **Authentication**: All patient data endpoints must require valid authentication
- **Input Validation**: Comprehensive validation using Pydantic models
- **SQL Injection Prevention**: Use parameterized queries exclusively
- **Session Security**: Implement secure session management practices

### **3. Code Quality Standards**
- **Test Coverage**: Maintain >80% code coverage for all new features
- **Code Reviews**: All changes require peer review before deployment
- **Documentation**: Comprehensive inline comments and API documentation
- **Error Handling**: Graceful error handling with user-friendly messages
- **Performance**: Optimize for healthcare professional workflow efficiency

### **4. User Experience Focus**
- **Clinical Workflow**: Design interfaces that match clinical practice patterns
- **Efficiency**: Reduce administrative burden and task completion time
- **Accessibility**: Ensure accessibility for all healthcare professionals
- **Mobile Responsiveness**: Support various devices and screen sizes
- **Intuitive Design**: Follow healthcare UI/UX best practices

---

## Technical Guidelines

### **Backend Development (FastAPI/Python)**

#### **Code Structure**
```python
# Module organization pattern
modules/
├── auth.py                 # Authentication and authorization
├── patients.py            # Patient data management
├── appointments.py        # Scheduling and booking
├── treatment_notes.py     # Clinical documentation
├── outcome_measures.py    # Assessment tools
├── billing.py            # Financial operations
└── [feature_name].py     # New feature modules
```

#### **API Development Standards**
```python
# Endpoint pattern example
@app.post("/api/patients/{patient_id}/treatment-notes", 
          response_model=TreatmentNoteResponse)
async def create_treatment_note(
    patient_id: int,
    note_data: TreatmentNoteCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create new treatment note for patient.
    
    Args:
        patient_id: Unique patient identifier
        note_data: Treatment note creation data
        current_user: Authenticated user session
        
    Returns:
        TreatmentNoteResponse: Created treatment note data
        
    Raises:
        HTTPException: 404 if patient not found, 403 if unauthorized
    """
    # Implementation with proper validation and error handling
```

#### **Database Interaction Patterns**
```python
# Use parameterized queries exclusively
def get_patient_by_id(patient_id: int) -> Optional[Patient]:
    """Retrieve patient by ID with security validation."""
    query = """
        SELECT * FROM patients 
        WHERE id = ? AND clinic_id = ?
    """
    # Always include clinic_id for multi-tenant security
    return db.execute(query, (patient_id, current_user.clinic_id)).fetchone()

# Pydantic model validation
class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="Valid email address")
    phone: str = Field(..., regex=r"^\+?[\d\s\-\(\)]+$")
    date_of_birth: date = Field(..., description="Patient birth date")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+27123456789",
                "date_of_birth": "1980-01-15"
            }
        }
```

#### **Security Implementation**
```python
# Authentication dependency
async def get_current_user(request: Request) -> dict:
    """Validate user session and return user data."""
    session_token = request.session.get("user")
    if not session_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate session and return user data
    user = validate_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return user

# Authorization for patient data
def authorize_patient_access(patient_id: int, user: dict) -> bool:
    """Ensure user has access to specific patient data."""
    # Implement clinic-based authorization
    patient_clinic = get_patient_clinic(patient_id)
    return patient_clinic == user.get("clinic_id")
```

### **Frontend Development (HTML/CSS/JavaScript)**

#### **Template Structure**
```html
<!-- Follow consistent template pattern -->
{% extends "base.html" %}
{% block title %}Page Title - HadadaHealth{% endblock %}

{% block content %}
<div class="container">
    <!-- Breadcrumb navigation -->
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="/">Dashboard</a></li>
            <li class="breadcrumb-item active">Current Page</li>
        </ol>
    </nav>
    
    <!-- Main content with accessibility -->
    <main role="main" aria-labelledby="main-heading">
        <h1 id="main-heading">Page Heading</h1>
        <!-- Content implementation -->
    </main>
</div>
{% endblock %}
```

#### **JavaScript Patterns**
```javascript
// Use consistent error handling and user feedback
class HadadaAPI {
    static async makeRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            showUserNotification('error', 'Operation failed. Please try again.');
            throw error;
        }
    }
}

// User notification system
function showUserNotification(type, message, duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.getElementById('notifications').appendChild(notification);
    
    if (duration > 0) {
        setTimeout(() => {
            notification.remove();
        }, duration);
    }
}
```

### **Database Management**

#### **Schema Design Principles**
```sql
-- Follow consistent naming conventions
CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    date_of_birth DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinic_id) REFERENCES clinics(id)
);

-- Always include audit fields
CREATE TABLE treatment_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    therapist_id INTEGER NOT NULL,
    session_date DATE NOT NULL,
    subjective TEXT,
    objective TEXT,
    assessment TEXT,
    plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (therapist_id) REFERENCES therapists(id)
);
```

#### **Migration Patterns**
```python
def migrate_add_column_safe(table_name: str, column_definition: str):
    """Safely add column to existing table."""
    try:
        # Check if column already exists
        cursor = db.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        column_name = column_definition.split()[0]
        
        if column_name not in columns:
            db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
            db.commit()
            print(f"Added column {column_name} to {table_name}")
        else:
            print(f"Column {column_name} already exists in {table_name}")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise
```

---

## Feature Development Workflow

### **1. Feature Planning**
- **Requirements Analysis**: Understand clinical workflow impact
- **Security Assessment**: Identify data protection requirements
- **User Experience Design**: Create mockups and user journey maps
- **Technical Architecture**: Plan implementation approach
- **Testing Strategy**: Define test cases and validation criteria

### **2. Implementation Process**
```python
# Feature development checklist
class FeatureImplementation:
    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        self.checklist = [
            "Create Pydantic models for data validation",
            "Implement database schema changes",
            "Create API endpoints with authentication",
            "Add comprehensive error handling",
            "Implement frontend interface",
            "Add JavaScript functionality",
            "Create unit and integration tests",
            "Update API documentation",
            "Perform security review",
            "Conduct user acceptance testing"
        ]
    
    def validate_completion(self) -> bool:
        # Ensure all checklist items completed
        return all(self.verify_item(item) for item in self.checklist)
```

### **3. Quality Assurance**
```python
# Testing requirements
def test_feature_security():
    """Verify security requirements are met."""
    assert authentication_required()
    assert input_validation_implemented()
    assert sql_injection_protected()
    assert audit_logging_enabled()

def test_feature_functionality():
    """Verify feature works as specified."""
    assert core_functionality_works()
    assert edge_cases_handled()
    assert error_conditions_managed()
    assert user_feedback_provided()

def test_feature_performance():
    """Verify performance requirements are met."""
    assert response_time_under_threshold()
    assert memory_usage_acceptable()
    assert concurrent_user_support()
```

---

## Clinical Domain Specifications

### **Outcome Measures Implementation**
```python
# Standardized assessment scoring
class OutcomeMeasure:
    def __init__(self, measure_type: str):
        self.measure_type = measure_type
        self.scoring_rules = self.load_scoring_rules()
    
    def calculate_score(self, responses: Dict) -> Dict:
        """Calculate standardized score with clinical interpretation."""
        raw_score = self.calculate_raw_score(responses)
        interpretation = self.interpret_score(raw_score)
        percentile = self.calculate_percentile(raw_score)
        
        return {
            "raw_score": raw_score,
            "interpretation": interpretation,
            "percentile": percentile,
            "clinical_significance": self.assess_clinical_significance(raw_score),
            "recommendations": self.generate_recommendations(raw_score)
        }
```

### **Clinical Documentation Standards**
```python
# SOAP note structure
class TreatmentNote(BaseModel):
    subjective: str = Field(..., description="Patient's subjective report")
    objective: str = Field(..., description="Objective findings and measurements")
    assessment: str = Field(..., description="Clinical assessment and analysis") 
    plan: str = Field(..., description="Treatment plan and goals")
    
    # Additional clinical fields
    session_duration: int = Field(..., ge=15, le=180, description="Session duration in minutes")
    treatment_techniques: List[str] = Field(..., description="Treatment techniques used")
    outcome_measures: Optional[List[OutcomeMeasureResult]] = None
    clinical_reasoning: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "subjective": "Patient reports decreased pain and improved mobility",
                "objective": "ROM: shoulder flexion 150°, strength 4/5",
                "assessment": "Good progress with shoulder rehabilitation program",
                "plan": "Continue strengthening exercises, reassess in 1 week"
            }
        }
```

### **Medical Aid Integration**
```python
# South African medical aid handling
class MedicalAidClaim:
    def __init__(self, claim_data: Dict):
        self.claim_data = claim_data
        self.validate_claim_requirements()
    
    def generate_claim(self) -> Dict:
        """Generate medical aid claim with required fields."""
        return {
            "practice_number": self.get_practice_number(),
            "patient_info": self.extract_patient_info(),
            "treatment_codes": self.map_treatment_codes(),
            "diagnosis_codes": self.get_icd10_codes(),
            "claim_amount": self.calculate_claim_amount(),
            "supporting_documentation": self.gather_documentation()
        }
    
    def validate_claim_requirements(self):
        """Ensure all required fields for SA medical aids."""
        required_fields = [
            "patient_medical_aid_number",
            "dependant_code", 
            "treatment_date",
            "procedure_codes",
            "diagnosis_code",
            "referring_doctor"
        ]
        # Validation implementation
```

---

## Error Handling & User Feedback

### **Error Handling Patterns**
```python
# Comprehensive error handling
class HadadaHealthException(Exception):
    """Base exception for HadadaHealth application."""
    def __init__(self, message: str, error_code: str = None, user_message: str = None):
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or "An error occurred. Please try again."
        super().__init__(self.message)

class PatientNotFoundError(HadadaHealthException):
    """Raised when patient cannot be found."""
    def __init__(self, patient_id: int):
        super().__init__(
            message=f"Patient with ID {patient_id} not found",
            error_code="PATIENT_NOT_FOUND",
            user_message="Patient not found. Please check the patient ID and try again."
        )

# Global exception handler
@app.exception_handler(HadadaHealthException)
async def hadada_exception_handler(request: Request, exc: HadadaHealthException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code or "APPLICATION_ERROR",
            "message": exc.user_message,
            "detail": exc.message if settings.DEBUG else None
        }
    )
```

### **User Feedback System**
```javascript
// Consistent user feedback
class UserFeedback {
    static success(message, title = 'Success') {
        this.showNotification('success', title, message);
    }
    
    static error(message, title = 'Error') {
        this.showNotification('error', title, message);
    }
    
    static info(message, title = 'Information') {
        this.showNotification('info', title, message);
    }
    
    static showNotification(type, title, message) {
        // Implementation using toast notifications or modal dialogs
        const notification = {
            type: type,
            title: title,
            message: message,
            timestamp: new Date().toISOString(),
            auto_dismiss: type !== 'error' // Keep errors visible until dismissed
        };
        
        this.displayNotification(notification);
    }
}
```

---

## Testing Requirements

### **Unit Testing**
```python
# Test pattern for clinical functions
import pytest
from unittest.mock import patch, MagicMock

class TestOutcomeMeasures:
    def test_berg_balance_scale_calculation(self):
        """Test BBS score calculation accuracy."""
        responses = {
            "item_1": 4, "item_2": 3, "item_3": 4,
            # ... all 14 items
        }
        
        score = calculate_berg_balance_score(responses)
        
        assert score["total_score"] == 51
        assert score["interpretation"] == "Low fall risk"
        assert score["percentile"] > 0
    
    @patch('modules.database.get_patient')
    def test_patient_authorization(self, mock_get_patient):
        """Test patient data access authorization."""
        mock_get_patient.return_value = {"clinic_id": 1}
        user = {"clinic_id": 1, "role": "therapist"}
        
        access_granted = authorize_patient_access(patient_id=123, user=user)
        
        assert access_granted == True
    
    def test_treatment_note_validation(self):
        """Test treatment note data validation."""
        invalid_note = {
            "subjective": "",  # Empty subjective
            "session_duration": 200  # Exceeds maximum
        }
        
        with pytest.raises(ValidationError):
            TreatmentNote(**invalid_note)
```

### **Integration Testing**
```python
# API endpoint testing
class TestPatientEndpoints:
    def test_create_patient_workflow(self, test_client, authenticated_user):
        """Test complete patient creation workflow."""
        patient_data = {
            "name": "Test Patient",
            "email": "test@example.com",
            "phone": "+27123456789",
            "date_of_birth": "1980-01-15"
        }
        
        # Create patient
        response = test_client.post("/api/patients", json=patient_data)
        assert response.status_code == 201
        
        patient_id = response.json()["id"]
        
        # Verify patient was created
        get_response = test_client.get(f"/api/patients/{patient_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == patient_data["name"]
```

---

## Security Requirements

### **Data Protection**
- **Encryption**: All patient data encrypted at rest and in transit
- **Access Control**: Role-based permissions with audit logging
- **Session Management**: Secure session handling with timeout
- **Input Validation**: Comprehensive validation preventing injection attacks
- **API Security**: Authentication required for all sensitive endpoints

### **Compliance Requirements**
- **POPIA Compliance**: South African data protection requirements
- **GDPR Compliance**: European data protection standards
- **Healthcare Standards**: Clinical data handling best practices
- **Audit Requirements**: Complete activity logging and traceability
- **Data Retention**: Appropriate data lifecycle management

### **Security Checklist**
```python
# Security validation checklist
SECURITY_REQUIREMENTS = [
    "Authentication implemented on all patient data endpoints",
    "Input validation using Pydantic models",
    "SQL injection protection with parameterized queries", 
    "Session security with proper timeout and invalidation",
    "Audit logging for all data access and modifications",
    "Error messages don't expose sensitive information",
    "File upload validation and virus scanning",
    "Database backup encryption and access controls",
    "API rate limiting to prevent abuse",
    "HTTPS enforcement in production environment"
]
```

---

## Performance Guidelines

### **Database Optimization**
```sql
-- Index strategy for common queries
CREATE INDEX idx_patients_clinic_name ON patients(clinic_id, name);
CREATE INDEX idx_appointments_date_therapist ON appointments(appointment_date, therapist_id);
CREATE INDEX idx_treatment_notes_patient_date ON treatment_notes(patient_id, session_date);
CREATE INDEX idx_billing_date_status ON billing(billing_date, status);

-- Query optimization patterns
-- Use LIMIT for large result sets
SELECT * FROM patients WHERE clinic_id = ? ORDER BY name LIMIT 50;

-- Use appropriate joins for related data
SELECT p.name, t.session_date, t.subjective 
FROM patients p 
JOIN treatment_notes t ON p.id = t.patient_id 
WHERE p.clinic_id = ? AND t.session_date >= ?;
```

### **API Performance**
```python
# Response optimization
@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: int, include_notes: bool = False):
    """Get patient data with optional treatment notes."""
    patient = get_patient_basic_info(patient_id)
    
    if include_notes:
        # Only fetch notes if requested
        patient["treatment_notes"] = get_recent_treatment_notes(patient_id, limit=10)
    
    return patient

# Caching for static data
@lru_cache(maxsize=100)
def get_outcome_measure_templates():
    """Cache outcome measure templates."""
    return load_outcome_measure_templates()
```

---

## Deployment Guidelines

### **Environment Configuration**
```python
# Environment-specific settings
class Settings(BaseModel):
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    
    # Application
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("production", env="ENVIRONMENT")
    
    # Healthcare specific
    practice_registration_number: str = Field(..., env="PRACTICE_REG_NUMBER")
    medical_aid_provider_codes: str = Field(..., env="MEDICAL_AID_CODES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### **Production Checklist**
```python
PRODUCTION_READINESS_CHECKLIST = [
    "Environment variables configured securely",
    "Database backups automated and tested",
    "SSL/TLS certificates installed and valid", 
    "Rate limiting configured for API endpoints",
    "Monitoring and alerting system operational",
    "Log aggregation and analysis configured",
    "Security headers implemented (HSTS, CSP, etc.)",
    "Error tracking and notification system active",
    "Performance monitoring and profiling enabled",
    "Disaster recovery procedures documented and tested"
]
```

---

## Maintenance & Support

### **Monitoring Requirements**
```python
# Application monitoring
import logging
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logging.info(f"{func.__name__} completed in {execution_time:.2f}s")
            
            # Alert on slow performance
            if execution_time > 2.0:
                logging.warning(f"{func.__name__} slow performance: {execution_time:.2f}s")
                
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"{func.__name__} failed after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper
```

### **Logging Standards**
```python
# Structured logging configuration
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
    
    def log_user_action(self, user_id: int, action: str, details: dict = None):
        """Log user actions for audit trail."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "type": "user_action",
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "ip_address": self.get_client_ip()
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_security_event(self, event_type: str, details: dict):
        """Log security events for monitoring."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "WARNING",
            "type": "security_event",
            "event_type": event_type,
            "details": details,
            "requires_attention": True
        }
        
        self.logger.warning(json.dumps(log_entry))
```

---

## Agent Behavior Guidelines

### **When Working on HadadaHealth**

#### **DO:**
- Always prioritize patient data security and privacy
- Maintain comprehensive audit trails for all changes
- Follow healthcare industry best practices and standards
- Implement proper error handling with user-friendly messages
- Add comprehensive tests for all new functionality
- Document all changes thoroughly with clinical context
- Validate all user inputs using Pydantic models
- Use parameterized queries to prevent SQL injection
- Include accessibility features in all UI implementations
- Consider clinical workflow efficiency in all designs

#### **DON'T:**
- Never compromise on security for convenience
- Don't expose sensitive information in error messages or logs
- Never skip input validation or security checks
- Don't make changes without understanding clinical impact
- Never deploy without proper testing and review
- Don't hardcode sensitive information like API keys
- Never ignore performance implications of changes
- Don't break existing functionality without migration plan
- Never implement features without proper user feedback
- Don't forget to update documentation and tests

### **Decision Making Framework**
1. **Security First**: Is this change secure and compliant?
2. **Clinical Safety**: Does this support safe patient care?
3. **User Experience**: Will this improve healthcare professional workflow?
4. **Data Integrity**: Does this maintain data accuracy and completeness?
5. **Performance Impact**: Will this maintain system responsiveness?
6. **Maintenance**: Is this code maintainable and documentable?

---

## Conclusion

These agent instructions provide the foundation for high-quality, secure, and compliant development on the HadadaHealth platform. All development activities should align with these guidelines to ensure the system continues to serve healthcare professionals effectively while maintaining the highest standards of security, reliability, and clinical quality.

**Remember**: Healthcare software development requires extra diligence due to the critical nature of patient data and clinical workflows. When in doubt, prioritize security, compliance, and clinical safety over convenience or speed of implementation.

---

*These instructions are living documentation and should be updated as the system evolves and new requirements are identified.*