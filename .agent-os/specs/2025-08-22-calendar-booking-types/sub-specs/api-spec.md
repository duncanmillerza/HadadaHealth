# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-22-calendar-booking-types/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Endpoints

**Appointment Types Management:**

```
GET /api/appointment-types
- Returns hierarchical list of all appointment types
- Query params: include_inactive=false, practice_id=null
- Response: Tree structure with parent-child relationships

GET /api/appointment-types/{id}
- Returns specific appointment type with children
- Include practice customizations if practice context available

POST /api/appointment-types
- Create new appointment type (admin only)
- Body: {name, description, parent_id, color, sort_order}

PUT /api/appointment-types/{id}
- Update appointment type (admin only)
- Body: {name, description, color, sort_order, is_active}

DELETE /api/appointment-types/{id}
- Soft delete appointment type (admin only)
- Cascades to children and practice customizations
```

**Practice-Specific Customizations:**

```
GET /api/practices/{practice_id}/appointment-types
- Returns appointment types with practice customizations applied
- Merged view of defaults + practice overrides

PUT /api/practices/{practice_id}/appointment-types/{type_id}
- Customize appointment type for specific practice
- Body: {custom_name, custom_description, custom_color, is_enabled, default_duration, sort_order}

POST /api/practices/{practice_id}/appointment-types/bulk
- Bulk update practice customizations
- Body: [{appointment_type_id, custom_name, is_enabled, ...}, ...]

DELETE /api/practices/{practice_id}/appointment-types/{type_id}
- Remove practice customization (reverts to default)
```

**Booking Integration:**

```
POST /api/appointments
- Enhanced to include appointment_type_id
- Body: {...existing fields..., appointment_type_id}

PUT /api/appointments/{id}
- Update appointment including type change
- Body: {...existing fields..., appointment_type_id}
```

## Controllers

**AppointmentTypeController:**
- index(): List all appointment types with hierarchy
- show(): Get specific appointment type
- store(): Create new appointment type (admin)
- update(): Modify appointment type (admin)
- destroy(): Soft delete appointment type (admin)

**PracticeAppointmentTypeController:**
- index(): Get practice-specific appointment types
- update(): Customize appointment type for practice
- bulkUpdate(): Handle multiple customizations
- destroy(): Remove practice customization

**AppointmentController (Enhanced):**
- store(): Include appointment type validation
- update(): Handle appointment type changes
- Middleware: Validate appointment type belongs to practice