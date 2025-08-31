# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-28-ai-report-writing-system/spec.md

> Created: 2025-08-28
> Version: 1.0.0

## Report Management Endpoints

### POST /api/reports/create
**Purpose:** Create a new report (both manager-initiated and therapist-initiated)
**Parameters:** 
- patient_id (required): Patient identifier
- report_type (required): discharge, progress, insurance, outcome_summary
- template_id (required): Template to use
- assigned_therapist_ids (required): Array of therapist user IDs
- deadline_date (optional): ISO date string
- disciplines (required): Array of disciplines to include
- priority (optional): 1-3 priority level
- requested_by_user_id (optional): NULL for therapist-initiated
**Response:** Report object with ID and initial status
**Errors:** 400 (invalid parameters), 401 (unauthorized), 404 (patient/template not found)

### GET /api/reports/dashboard
**Purpose:** Get reports for dashboard display (filtered by user role)
**Parameters:**
- status (optional): Filter by report status
- user_id (optional): Filter by assigned therapist
- limit (optional): Number of reports to return (default 50)
- offset (optional): Pagination offset
**Response:** Array of report objects with patient info and deadline status
**Errors:** 401 (unauthorized)

### GET /api/reports/{report_id}
**Purpose:** Get detailed report information including content
**Parameters:** report_id (path parameter)
**Response:** Complete report object with content and version history
**Errors:** 401 (unauthorized), 404 (report not found), 403 (insufficient permissions)

### PUT /api/reports/{report_id}/status
**Purpose:** Update report status and content
**Parameters:**
- report_id (path parameter)
- status (required): pending, in_progress, completed
- content (optional): JSON report content
- notes (optional): Status change notes
**Response:** Updated report object
**Errors:** 400 (invalid status), 401 (unauthorized), 404 (report not found)

### DELETE /api/reports/{report_id}
**Purpose:** Delete a report (admin/manager only)
**Parameters:** report_id (path parameter)
**Response:** 204 No Content
**Errors:** 401 (unauthorized), 403 (insufficient permissions), 404 (report not found)

## Template Management Endpoints

### GET /api/templates
**Purpose:** Get available report templates
**Parameters:**
- template_type (optional): Filter by template type
- practice_id (optional): Include practice-specific templates
- is_active (optional): Filter by active status (default true)
**Response:** Array of template objects with field schemas
**Errors:** 401 (unauthorized)

### POST /api/templates/create
**Purpose:** Create custom template (admin/manager only)
**Parameters:**
- name (required): Template name
- template_type (required): Template type
- description (optional): Template description
- fields_schema (required): JSON field definition
- section_order (required): Array of section names
**Response:** Created template object
**Errors:** 400 (invalid schema), 401 (unauthorized), 403 (insufficient permissions)

### PUT /api/templates/{template_id}
**Purpose:** Update existing template (admin/manager only)
**Parameters:**
- template_id (path parameter)
- name, description, fields_schema, section_order (as needed)
**Response:** Updated template object
**Errors:** 400 (invalid parameters), 401 (unauthorized), 403 (insufficient permissions), 404 (template not found)

### DELETE /api/templates/{template_id}
**Purpose:** Deactivate template (admin/manager only)
**Parameters:** template_id (path parameter)
**Response:** 204 No Content
**Errors:** 401 (unauthorized), 403 (insufficient permissions), 404 (template not found)

## AI Content Generation Endpoints

### POST /api/ai/generate-medical-history
**Purpose:** Generate AI medical history for patient
**Parameters:**
- patient_id (required): Patient identifier
- disciplines (optional): Array of disciplines to include
- force_regenerate (optional): Skip cache and regenerate (default false)
**Response:** Generated medical history content with metadata
**Errors:** 400 (invalid patient), 401 (unauthorized), 500 (AI generation failed)

### POST /api/ai/generate-treatment-summary
**Purpose:** Generate AI treatment summary for patient
**Parameters:**
- patient_id (required): Patient identifier
- disciplines (optional): Array of disciplines to include
- date_range (optional): Start and end dates for summary
- force_regenerate (optional): Skip cache and regenerate
**Response:** Generated treatment summary with source data references
**Errors:** 400 (invalid parameters), 401 (unauthorized), 500 (AI generation failed)

### GET /api/ai/cache/{patient_id}
**Purpose:** Get cached AI content for patient
**Parameters:**
- patient_id (path parameter)
- content_type (optional): Filter by content type
**Response:** Array of cached content objects with expiry info
**Errors:** 401 (unauthorized), 404 (patient not found)

### DELETE /api/ai/cache/{patient_id}
**Purpose:** Clear AI cache for patient (force regeneration)
**Parameters:** 
- patient_id (path parameter)
- content_type (optional): Specific content type to clear
**Response:** 204 No Content
**Errors:** 401 (unauthorized), 404 (patient not found)

## Notification Endpoints

### GET /api/notifications
**Purpose:** Get user notifications
**Parameters:**
- is_read (optional): Filter by read status
- notification_type (optional): Filter by type
- limit (optional): Number to return (default 20)
**Response:** Array of notification objects
**Errors:** 401 (unauthorized)

### PUT /api/notifications/{notification_id}/read
**Purpose:** Mark notification as read
**Parameters:** notification_id (path parameter)
**Response:** Updated notification object
**Errors:** 401 (unauthorized), 404 (notification not found)

### POST /api/notifications/mark-all-read
**Purpose:** Mark all user notifications as read
**Parameters:** None
**Response:** Count of notifications marked as read
**Errors:** 401 (unauthorized)

## Data Access & Permission Endpoints

### GET /api/reports/disciplines/{patient_id}
**Purpose:** Get disciplines that have treated a patient
**Parameters:** patient_id (path parameter)
**Response:** Array of discipline objects with therapist info and treatment date ranges
**Errors:** 401 (unauthorized), 404 (patient not found)

### GET /api/reports/export/{report_id}/pdf
**Purpose:** Export completed report as PDF
**Parameters:** 
- report_id (path parameter)
- include_signatures (optional): Include digital signatures (default true)
**Response:** PDF file download
**Errors:** 401 (unauthorized), 404 (report not found), 400 (report not completed)

## WebSocket Endpoints

### WS /ws/reports/{user_id}
**Purpose:** Real-time notifications for report updates
**Parameters:** user_id (path parameter)
**Events:** report_created, report_updated, deadline_approaching, report_completed
**Authentication:** JWT token via query parameter or header
**Errors:** 401 (unauthorized), 403 (insufficient permissions)

## Controllers

All endpoints will be implemented in a new `controllers/report_controller.py` following the existing HadadaHealth controller pattern:

```python
# Example controller structure
class ReportController:
    async def create_report(request: ReportCreateRequest) -> ReportResponse
    async def get_dashboard_reports(user_id: str, filters: ReportFilters) -> List[ReportSummary]
    async def generate_ai_content(patient_id: str, content_type: str) -> AIContentResponse
    async def update_report_status(report_id: int, status_update: StatusUpdate) -> ReportResponse
```

The controller will integrate with:
- `modules/reports.py` for business logic
- `modules/ai_content.py` for AI generation
- Existing authentication middleware
- Database connection management from `modules/database.py`

## Request/Response Models

### ReportCreateRequest
```json
{
  "patient_id": "string",
  "report_type": "discharge|progress|insurance|outcome_summary",
  "template_id": "integer",
  "assigned_therapist_ids": ["string"],
  "deadline_date": "2025-08-28T10:00:00Z",
  "disciplines": ["physiotherapy", "occupational_therapy"],
  "priority": 1,
  "requested_by_user_id": "string|null"
}
```

### ReportResponse
```json
{
  "id": "integer",
  "patient_id": "string",
  "patient_name": "string",
  "report_type": "string",
  "status": "pending|in_progress|completed",
  "assigned_therapists": [
    {
      "user_id": "string",
      "name": "string",
      "discipline": "string"
    }
  ],
  "created_date": "2025-08-28T09:00:00Z",
  "deadline_date": "2025-08-28T17:00:00Z",
  "content": "object|null",
  "version": "integer"
}
```

### TemplateResponse
```json
{
  "id": "integer",
  "name": "string",
  "template_type": "string",
  "description": "string",
  "fields_schema": {
    "sections": [
      {
        "name": "string",
        "fields": [
          {
            "name": "string",
            "type": "text|number|date|select",
            "required": "boolean",
            "options": ["array"]
          }
        ]
      }
    ]
  },
  "is_active": "boolean",
  "created_date": "2025-08-28T09:00:00Z"
}
```

### AIContentResponse
```json
{
  "content": "string",
  "content_type": "medical_history|treatment_summary",
  "patient_id": "string",
  "generated_date": "2025-08-28T09:00:00Z",
  "source_data": [
    {
      "type": "treatment_note|assessment|outcome_measure",
      "id": "string",
      "date": "2025-08-28",
      "discipline": "string"
    }
  ],
  "confidence_score": "number",
  "cache_expiry": "2025-08-29T09:00:00Z"
}
```

## Authentication & Authorization

All endpoints require valid session authentication using existing HadadaHealth auth system:
- Session-based authentication via cookies
- Role-based access control (therapist, manager, admin)
- Patient data access restricted by assigned therapists and treatment history
- Manager/admin roles have broader access for practice management

## Error Response Format

```json
{
  "error": "string",
  "message": "string",
  "details": "object|null"
}
```

## Integration Notes

- All endpoints follow FastAPI async patterns used in existing HadadaHealth codebase
- Database operations use existing `modules/database.py` connection management
- Input validation uses Pydantic models in `models/validation.py`
- Error handling follows existing patterns with proper HTTP status codes
- WebSocket implementation uses FastAPI WebSocket support for real-time features
## Wizard Support Endpoints

### GET /api/reports/wizard/options
Purpose: Provide aggregated options and sensible defaults for the wizard
Parameters:
- patient_id (optional): If provided, includes booking-derived recommendations
- disciplines (optional): Comma-separated list to scope therapist suggestions
Response: JSON object with keys:
- allowed_report_types, priorities, user_role, user_defaults (discipline, therapist_id)
- recommended_disciplines (when patient_id provided): array of { discipline, bookings_count, last_seen }
- suggested_therapists (when patient_id and disciplines provided): array of { user_id, name, disciplines, bookings_count_with_patient, last_seen }
- other_therapists (when disciplines provided): remaining eligible therapists without prior bookings for patient
Errors: 401 (unauthorized)

### GET /api/patients/search
Purpose: Search patients by name, surname, MRN/ID
Parameters:
- query (required): Search string
- limit (optional): Max results, default 20
Response: Array of patients with id, name, surname, dob, identifiers
Errors: 400 (invalid query), 401 (unauthorized)

### GET /api/patients/recent
Purpose: Fetch recent patients for current user
Parameters:
- limit (optional): Max results, default 10
Response: Array of patient summaries
Errors: 401 (unauthorized)

### GET /api/users/therapists
Purpose: List therapists filtered by disciplines
Parameters:
- disciplines (optional): Comma-separated list; returns therapists matching any
Response: Array of therapist users with user_id, name, disciplines
Errors: 401 (unauthorized)

## Data Sourcing Notes
- Booking-derived recommendations use existing appointment/booking data to compute:
  - Distinct disciplines engaged with the patient (counts, last_seen)
  - Therapists who have previously had bookings with the patient within the selected disciplines
