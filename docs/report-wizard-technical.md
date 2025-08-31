# Report Creation Wizard - Technical Documentation

> **Developer Guide for the 5-Step Report Creation Wizard**  
> Architecture, APIs, and implementation details

## Architecture Overview

The Report Creation Wizard is implemented as a client-side JavaScript class with server-side API integration. It replaces the legacy single-step modal with a guided 5-step process.

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Report Wizard Architecture                │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Frontend      │   Backend       │   Database              │
├─────────────────┼─────────────────┼─────────────────────────┤
│ ReportWizard    │ ReportController│ reports                 │
│ (JavaScript)    │ (Python/FastAPI)│ report_templates        │
│                 │                 │ therapists              │
│ HTML Templates  │ Wizard Options  │ bookings                │
│ CSS Styling     │ API Endpoints   │ patients                │
│ State Management│ Validation      │ report_notifications    │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Frontend Implementation

### JavaScript Class Structure

**File:** `static/js/report_wizard.js`

```javascript
class ReportWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 5;
        this.state = {
            patient: null,
            reportType: null,
            template: null,
            title: '',
            disciplines: [],
            therapists: [],
            priority: 2,
            deadline: null
        };
    }
}
```

### Step Navigation Logic

```javascript
// Step validation
isStepValid(stepNumber) {
    switch(stepNumber) {
        case 1: return this.state.patient !== null;
        case 2: return this.state.reportType && this.state.template && this.state.title.trim();
        case 3: return this.state.disciplines.length > 0;
        case 4: return this.state.therapists.length > 0;
        case 5: return true; // Priority has default, deadline optional
    }
}

// Step progression
goToNextStep() {
    if (this.isStepValid(this.currentStep) && this.currentStep < this.totalSteps) {
        this.showStep(this.currentStep + 1);
    }
}
```

### State Management

The wizard maintains state throughout the multi-step process:

- **Patient Selection:** Stores patient ID, name, DOB, identifiers
- **Report Configuration:** Type, template ID, title
- **Discipline Selection:** Array of selected disciplines
- **Therapist Assignment:** Array of therapist objects with ID and name
- **Priority/Deadline:** Priority level (1-3) and optional deadline date

## Backend Implementation

### API Endpoints

#### GET /api/reports/wizard/options
**Purpose:** Get wizard configuration and recommendations

**Parameters:**
- `patient_id` (optional): Patient ID for personalized recommendations
- `disciplines` (optional): Comma-separated disciplines for therapist filtering

**Response:**
```json
{
    "allowed_report_types": ["discharge", "progress", "assessment"],
    "priorities": [{"value": 1, "label": "Low"}, ...],
    "user_role": "therapist",
    "user_defaults": {"priority": 2, "assigned_therapist_ids": ["1"]},
    "recommended_disciplines": [...],
    "suggested_therapists": [...],
    "other_therapists": [...]
}
```

#### POST /api/reports/create
**Purpose:** Create report from wizard payload

**Request Body:**
```json
{
    "patient_id": "4603087263088",
    "report_type": "discharge", 
    "template_id": 1,
    "title": "Patient Name - Report Type - Date",
    "disciplines": ["physiotherapy", "occupational_therapy"],
    "assigned_therapist_ids": ["1", "3"],
    "priority": 2,
    "deadline_date": "2025-09-07",
    "generate_ai_content": true
}
```

### Data Processing Pipeline

```python
# Controller: controllers/report_controller.py
class ReportController:
    @staticmethod
    async def create_report(request: ReportCreateRequest, current_user: dict):
        # 1. Create report in database
        report_id = create_report(...)
        
        # 2. Create notifications for assigned therapists
        for therapist_id in request.assigned_therapist_ids:
            create_report_notification(
                report_id=report_id,
                user_id=therapist_id,
                notification_type='request',  # Fixed from 'report_assigned'
                message=f'New report assigned: {request.title}'
            )
        
        # 3. Generate AI content if requested
        if request.generate_ai_content:
            ReportController._generate_ai_content_async(report_id, request.disciplines)
            
        # 4. Return created report with JSON parsing
        report = get_report_by_id(report_id)
        # Parse JSON fields back to arrays for response model
        if isinstance(report['assigned_therapist_ids'], str):
            report['assigned_therapist_ids'] = json.loads(report['assigned_therapist_ids'])
        # ... more parsing
        
        return ReportResponse(**report)
```

## Key Bug Fixes Implemented

### 1. Discipline Mapping Issue

**Problem:** Frontend sends `"physiotherapy"`, database stores `"Physiotherapy"`

**Solution:** Added discipline mapping in `_get_therapist_suggestions`:

```python
# Map frontend discipline names to database profession names
discipline_mapping = {
    'physiotherapy': 'Physiotherapy',
    'occupational_therapy': 'Occupational Therapy', 
    'speech_therapy': 'Speech Therapy',
    'psychology': 'Psychology'
}

# Convert frontend discipline names to database profession names
db_disciplines = []
for discipline in selected_disciplines:
    mapped_discipline = discipline_mapping.get(discipline.lower())
    if mapped_discipline:
        db_disciplines.append(mapped_discipline)
```

### 2. Notification Type Constraint Error

**Problem:** Using invalid notification types `'report_assigned'` and `'status_change'`

**Solution:** Updated to use valid constraint values:
- `'report_assigned'` → `'request'`
- `'status_change'` → `'reminder'`

**Database Constraint:**
```sql
CHECK (notification_type IN ('request', 'reminder', 'completion', 'overdue'))
```

### 3. JSON Parsing Error

**Problem:** Database stores arrays as JSON strings, Pydantic expects actual arrays

**Solution:** Added JSON parsing before creating `ReportResponse`:

```python
# Parse JSON fields back to arrays for the response model
if isinstance(report['assigned_therapist_ids'], str):
    report['assigned_therapist_ids'] = json.loads(report['assigned_therapist_ids'])
if isinstance(report['disciplines'], str):
    report['disciplines'] = json.loads(report['disciplines'])
```

## Database Schema

### Key Tables

```sql
-- Reports storage
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    report_type TEXT NOT NULL,
    template_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    assigned_therapist_ids TEXT NOT NULL, -- JSON array
    disciplines TEXT NOT NULL,            -- JSON array
    priority INTEGER DEFAULT 2,
    deadline_date TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (template_id) REFERENCES report_templates(id)
);

-- Notifications
CREATE TABLE report_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    CHECK (notification_type IN ('request', 'reminder', 'completion', 'overdue'))
);
```

## Testing

### Test Coverage

**File:** `test_report_wizard_ui.py`

**Test Classes:**
1. **TestReportWizardValidation:** Step validation logic
2. **TestReportWizardAPI:** API integration and discipline mapping
3. **TestReportWizardEndToEnd:** Complete workflow simulation
4. **TestWizardJSONParsing:** JSON field parsing validation

**Key Test Cases:**
```python
def test_complete_wizard_flow_simulation(self):
    """Test complete wizard workflow simulation"""
    # Step 1: Patient Selection
    # Step 2: Report Type & Template  
    # Step 3: Disciplines
    # Step 4: Therapists
    # Step 5: Priority & Timeline
    # Validate final payload structure

def test_discipline_mapping_fix(self):
    """Test that discipline mapping works correctly"""
    frontend_disciplines = ["physiotherapy", "occupational_therapy"]
    expected_db_disciplines = ["Physiotherapy", "Occupational Therapy"]
    # Test mapping logic

def test_notification_type_fix_validation(self):
    """Test that notification types are valid after our fix"""
    valid_types = ['request', 'reminder', 'completion', 'overdue']
    fixed_mapping = {
        'report_assigned': 'request',
        'status_change': 'reminder'
    }
```

### Running Tests

```bash
# Run all wizard tests
python -m pytest test_report_wizard_ui.py -v

# Run specific test class
python -m pytest test_report_wizard_ui.py::TestReportWizardValidation -v

# Run with coverage
python -m pytest test_report_wizard_ui.py --cov=controllers --cov=modules
```

## Browser Compatibility

### Supported Features
- **ES6 Classes:** ReportWizard implementation
- **Fetch API:** AJAX requests to backend
- **LocalStorage:** State persistence (future enhancement)
- **CSS Grid/Flexbox:** Layout and responsive design

### Minimum Requirements
- Chrome 60+, Firefox 55+, Safari 12+
- JavaScript enabled
- Modern CSS support

## Performance Considerations

### Frontend Optimizations
- **Debounced Search:** 300ms delay for patient search
- **Progressive Loading:** Load data only when needed for each step
- **Event Delegation:** Efficient event handling for dynamic content
- **State Caching:** Minimize API calls by caching wizard options

### Backend Optimizations
- **Database Indexes:** Optimized queries for therapist suggestions
- **Query Efficiency:** Single query to get therapist suggestions and other options
- **JSON Parsing:** Efficient JSON field handling in responses

### Caching Strategy
```python
# Cache wizard options for repeated requests
@lru_cache(maxsize=100)
def get_wizard_options_cached(patient_id, disciplines_str):
    return get_wizard_options(patient_id, disciplines_str.split(','))
```

## Security Considerations

### Input Validation
- **Client-side:** Immediate feedback for user experience
- **Server-side:** Comprehensive validation using Pydantic models
- **SQL Injection Prevention:** Parameterized queries only
- **CSRF Protection:** Session-based authentication

### Data Protection
- **POPIA Compliance:** Healthcare data protection standards
- **Audit Trails:** All report activities logged
- **Role-based Access:** Therapist/Manager permission levels
- **Secure Communication:** HTTPS for all API calls

### Authentication
```python
@app.post("/api/reports/create")
async def create_report_endpoint(
    request: ReportCreateRequest, 
    current_user: dict = Depends(require_auth)  # Authentication required
):
```

## Error Handling

### Frontend Error Recovery
```javascript
async submitReport() {
    try {
        const response = await fetch('/api/reports/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create report');
        }
        
        // Success handling
    } catch (error) {
        console.error('Error creating report:', error);
        this.showError(error.message);
        this.finishBtn.disabled = false;
    }
}
```

### Backend Error Responses
```python
# Standardized error responses
try:
    # Report creation logic
    return ReportResponse(**report)
except Exception as e:
    raise HTTPException(
        status_code=400, 
        detail=f"Failed to create report: {str(e)}"
    )
```

## Migration from Legacy Modal

### Backward Compatibility
```javascript
// Compatibility function for legacy calls
function openReportRequestModal(workflowType = 'therapist', reportId = null) {
    console.log('⚠️ openReportRequestModal is deprecated, redirecting to wizard...');
    openReportWizard(workflowType, reportId);
}
```

### Deprecation Strategy
1. **Phase 1:** New wizard alongside legacy modal
2. **Phase 2:** Redirect legacy calls to wizard (current)
3. **Phase 3:** Remove legacy modal code (future)

## Future Enhancements

### Planned Features
- **Draft Saving:** Save wizard state and resume later
- **Template Preview:** Live preview of selected template
- **Batch Creation:** Create multiple reports for related patients
- **Advanced Scheduling:** Integration with therapist availability
- **Mobile Optimization:** Touch-friendly interface improvements

### Technical Debt
- **Pydantic V2 Migration:** Update from deprecated V1 validators
- **TypeScript Conversion:** Add type safety to JavaScript
- **Component Architecture:** Convert to modular component system
- **Automated Testing:** Add Cypress end-to-end tests

---

*This technical documentation is maintained alongside the codebase. For questions or contributions, contact the development team.*