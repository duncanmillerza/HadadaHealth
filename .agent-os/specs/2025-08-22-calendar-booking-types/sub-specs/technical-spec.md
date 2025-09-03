# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-22-calendar-booking-types/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Technical Requirements

- Modal component for appointment type selection
- Database schema for appointment types with hierarchical structure
- API endpoints for appointment type management (CRUD operations)
- Integration with existing booking system and calendar components
- Practice-specific configuration storage and retrieval
- Default appointment type seeding system
- Form validation for appointment type customization
- Real-time updates for appointment type changes across user sessions

## Approach

**Frontend Components:**
- AppointmentTypeModal: Main modal for type selection
- AppointmentTypeTree: Hierarchical display component
- AppointmentTypeForm: Configuration form for practice admins
- Calendar integration: Enhanced slot click handlers

**Backend Architecture:**
- AppointmentType model with self-referential relationships for hierarchy
- PracticeAppointmentType model for practice-specific configurations
- Appointment model updates to include appointment_type_id
- Seeder classes for default appointment types

**Database Design:**
- appointment_types table with parent_id for hierarchy
- practice_appointment_types table for customizations
- appointments table update with foreign key reference
- Migration scripts for existing data

**API Design:**
- RESTful endpoints for appointment type management
- Nested resource structure for sub-types
- Practice-scoped endpoints for customizations
- Bulk operations for default settings

## External Dependencies

- Existing Laravel booking system
- Current calendar component (likely Vue.js/React)
- Database migration system
- Authentication/authorization for practice-specific data
- Modal/overlay UI library components