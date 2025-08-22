# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-22-calendar-booking-types/spec.md

> Created: 2025-08-22
> Status: Ready for Implementation

## Tasks

## 1. Database Schema & Model Foundation

1.1. Write unit tests for AppointmentType model relationships and validation rules
1.2. Create appointment_types migration with hierarchical structure (id, name, parent_id, practice_id, color, duration, description)
1.3. Create practice_appointment_types migration for practice-specific customizations
1.4. Update appointments migration to add appointment_type_id foreign key
1.5. Implement AppointmentType model with self-referential parent/child relationships
1.6. Implement PracticeAppointmentType model with practice associations
1.7. Create database seeders for default appointment types (Patient, Meeting, Admin, Travel) with sub-types
1.8. Verify all database tests pass and relationships work correctly

## 2. API Layer & Backend Controllers

2.1. Write feature tests for appointment type API endpoints (CRUD, hierarchical responses, practice scoping)
2.2. Create AppointmentTypeController with index, show, store, update, destroy methods
2.3. Create PracticeAppointmentTypeController for practice-specific customizations
2.4. Implement hierarchical API responses with nested tree structure
2.5. Add form request validation classes for appointment type creation/updates
2.6. Update AppointmentController to handle appointment_type_id in booking flow
2.7. Create API routes with practice-scoped middleware protection
2.8. Verify all API tests pass and endpoints return correct hierarchical data

## 3. Frontend Modal & Selection Components

3.1. Write component tests for AppointmentTypeModal user interactions and selections
3.2. Create AppointmentTypeModal component with hierarchical type selection interface
3.3. Build AppointmentTypeTree component for displaying nested appointment types
3.4. Implement appointment type selection logic with parent/child relationships
3.5. Update calendar slot click handlers to trigger appointment type modal
3.6. Add visual indicators (colors, icons) for different appointment type categories
3.7. Integrate modal selection with existing booking form submission
3.8. Verify all frontend component tests pass and modal functionality works

## 4. Practice Configuration & Admin Interface

4.1. Write integration tests for appointment type customization workflows
4.2. Create AppointmentTypeForm component for adding/editing practice-specific types
4.3. Build appointment type management page for practice administrators
4.4. Implement bulk operations interface for enabling/disabling default types
4.5. Add appointment type configuration to practice settings navigation
4.6. Create default settings restoration functionality
4.7. Implement real-time updates for appointment type changes across sessions
4.8. Verify all configuration tests pass and admin interface functions correctly

## 5. Integration Testing & Data Migration

5.1. Write end-to-end tests for complete booking workflow with appointment types
5.2. Create migration script to assign default appointment types to existing appointments
5.3. Integrate appointment type display with calendar view and appointment listings
5.4. Implement error handling for missing/invalid appointment types in booking flow
5.5. Test performance of hierarchical queries with large datasets
5.6. Validate cascading effects of appointment type changes on existing bookings
5.7. Create rollback procedures for appointment type migrations
5.8. Verify all integration tests pass and system performs optimally in production scenarios