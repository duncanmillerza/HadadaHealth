# Report Creation Wizard Specification

> Created: 2025-08-29
> Status: Proposed (pre-implementation)

## Overview

Replace the current single-step report creation modal with a guided, multi-step wizard that mirrors the successful unified booking pattern. The flow breaks decisions into clear stages to reduce cognitive load and improve data quality.

Wizard Steps:
1) Select Patient
2) Report Type & Title
3) Disciplines
4) Clinicians/Therapists
5) Priority & Timeline

Primary outcome: On completion, submit a single payload to `POST /api/reports/create` with all selections. The wizard can be used by both managers and therapists; permissions and defaults adapt based on role.

## Step Details

### Step 1: Select Patient
- Inputs: patient search/select (required)
- Features:
  - Search with debounce; support MRN/ID, name, surname
  - Recent patients list (last 10 for current user)
  - Patient info preview (DOB, ID, active disciplines, last visit)
  - Validation: `patient_id` required
- Data:
  - `GET /api/patients/search?query={q}&limit=20`
  - Optionally preload recent via `GET /api/patients/recent?limit=10`

### Step 2: Report Type & Title
- Inputs: report type (required), template (required), title (required)
- Features:
  - Report types: discharge, progress, insurance, outcome_summary, assessment
  - Template dropdown filtered by chosen report type
  - Auto-title suggestion: `{PatientName} - {ReportTypeLabel} - {YYYY-MM-DD}` (editable)
  - Template preview: sections and required fields list
  - Validation: `report_type`, `template_id`, non-empty `title`
- Data:
  - `GET /api/templates?template_type={report_type}&is_active=true`

### Step 3: Disciplines
- Inputs: one or more disciplines (required; at least one)
- Recommendation Logic:
  - Recommend disciplines that have existing bookings for the patient (from appointment/booking data)
  - Show count of historical bookings and last-seen date per discipline
  - Preselect recommended disciplines; user can change selections
- Features:
  - Discipline chips/toggles: physiotherapy, occupational_therapy, speech_therapy (extendable)
  - Rationale tooltip: “Recommended based on X prior bookings (last on YYYY-MM-DD)”
  - Validation: min 1 selection
- Data:
  - Provided by `GET /api/reports/wizard/options?patient_id=...` as `recommended_disciplines` with metadata `{discipline, bookings_count, last_seen}`

### Step 4: Clinicians/Therapists
- Inputs: assign one or more therapists (required)
- Suggestion Logic:
  - Suggest therapists who match the selected disciplines AND have existing bookings with this patient
  - Show per-therapist stats: bookings_count_with_patient, last_seen
  - List suggested therapists first, followed by other eligible therapists in those disciplines
- Features:
  - Filter therapists by selected disciplines
  - Default: if therapist user, preselect self; if manager, show multi-select
  - Validation: at least one therapist
- Data:
  - Provided by `GET /api/reports/wizard/options?patient_id=...&disciplines=...` as `suggested_therapists` array with `{user_id, name, disciplines, bookings_count_with_patient, last_seen}` and `other_therapists`

### Step 5: Priority & Timeline
- Inputs: priority (low/medium/high), deadline date (optional but recommended), notes (optional)
- Features:
  - Deadline date picker; enforce future date
  - Priority defaults to medium; color-coded UI
  - SLA helper text based on priority (e.g., High → 2 working days)
  - Summary panel of prior selections for quick review
- Validation: if provided, deadline must be today or later

## Navigation & UX
- Back/Next controls; keyboard accessible; progress indicator (1..5)
- Disabled Next until step validation passes
- Persist state between steps; confirm on cancel if unsaved
- Editing existing requests opens at Step 5 with a change-step control (summary sidebar)
- Responsive: single column on mobile, two-column with summary on desktop

## Payload Mapping (Finish → POST /api/reports/create)
- patient_id: from Step 1
- report_type: from Step 2
- template_id: from Step 2
- title: from Step 2
- disciplines: array from Step 3
- assigned_therapist_ids: array from Step 4
- priority: from Step 5 (1=low,2=medium,3=high)
- deadline_date: ISO date from Step 5 (optional)
- requested_by_user_id: server derives from auth if manager; null for therapist-initiated

## Permissions & Defaults
- Therapist role:
  - Step 4 defaults to self; allow adding co-authors if permissioned
  - Cannot assign other therapists unless manager permission
- Manager role:
  - Full access to assign multiple therapists
  - Sees discipline recommendations with counts of involved therapists

## Validation Rules (per step)
- Step 1: patient_id required
- Step 2: report_type ∈ allowed; template_id must exist and match type; title non-empty
- Step 3: disciplines length ≥ 1
- Step 4: assigned_therapist_ids length ≥ 1; all users must be therapists
- Step 5: if deadline_date provided, must be >= today

## API Support

Use existing endpoints where possible and add one aggregated helper for wizard performance:
- GET /api/reports/wizard/options
  - Parameters: `patient_id` (optional), `disciplines` (optional, comma-separated)
  - Returns: 
    - `allowed_report_types`, `priorities`, `user_role`, `user_defaults`
    - If `patient_id` present: `recommended_disciplines` derived from bookings with `{discipline, bookings_count, last_seen}`
    - If `patient_id` and `disciplines` present: `suggested_therapists` and `other_therapists` for those disciplines with booking stats per therapist
- GET /api/patients/search
- GET /api/patients/recent
- GET /api/templates
- POST /api/reports/create

Notes:
- The wizard should call `GET /api/reports/wizard/options?patient_id=...` after Step 1, and again with `&disciplines=...` after Step 3 to fetch therapist suggestions in a single roundtrip.

## Acceptance Criteria
- Users can complete the flow end-to-end with clear step validation
- Managers can assign multiple therapists; therapists default to self
- Disciplines show sensible recommendations based on patient history
- Title auto-suggest works and is editable
- Final submission creates a report visible in dashboard widgets with correct status and deadline
- All strings and controls are accessible (ARIA labels) and responsive

## Implementation Handoff
- UI: one modal with 5 `.wizard-step` containers, a `.wizard-progress` header, and a persistent summary sidebar on desktop
- State: single JS store object synced per step; serialize to payload on Finish
- Tests: Cypress-style flow tests (or equivalent) for validation and payload correctness
