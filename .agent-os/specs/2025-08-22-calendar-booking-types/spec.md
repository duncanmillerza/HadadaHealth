# Spec Requirements Document

> Spec: Calendar Booking Types
> Created: 2025-08-22
> Status: Planning

## Overview

This feature enhances the existing calendar booking system by introducing customizable appointment types with hierarchical categories. Users can click on booking slots to open a modal with appointment type selection, choose between main categories (Patient, Meeting, Admin, Travel) and their sub-types, allowing practices to customize their own booking types with default settings while minimizing clicks for a quick booking experience.

## User Stories

**As a healthcare provider**, I want to quickly select appointment types when booking slots so that I can categorize appointments efficiently without multiple navigation steps.

**As a practice administrator**, I want to customize appointment types and sub-types specific to our practice so that our booking system reflects our unique workflow and appointment categories.

**As a user**, I want a streamlined booking experience with minimal clicks so that I can quickly create appointments without navigating through complex menus.

**As a practice**, I want default appointment type settings so that common bookings require minimal configuration while still allowing customization when needed.

## Spec Scope

- Modal interface for appointment type selection when clicking booking slots
- Hierarchical appointment type system with main categories and sub-types
- Default categories: Patient, Meeting, Admin, Travel
- Sub-type examples: MDT meetings, assessments, follow-ups under respective categories
- Customizable appointment types per practice
- Default settings for appointment types to minimize configuration
- Integration with existing calendar booking system
- Quick booking workflow optimization

## Out of Scope

- Complete calendar system redesign
- Advanced appointment scheduling algorithms
- Multi-calendar synchronization
- Recurring appointment patterns (unless specifically needed for appointment types)
- Patient-facing booking interface changes

## Expected Deliverable

A fully integrated appointment type selection system that enhances the current calendar booking functionality with:
- Modal-based appointment type selection
- Hierarchical category system (main types and sub-types)
- Practice-specific customization capabilities
- Default appointment type configurations
- Streamlined user experience with minimal clicks
- Database schema to support appointment type management
- API endpoints for appointment type CRUD operations

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-22-calendar-booking-types/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-22-calendar-booking-types/sub-specs/technical-spec.md
- Database Schema: @.agent-os/specs/2025-08-22-calendar-booking-types/sub-specs/database-schema.md
- API Specification: @.agent-os/specs/2025-08-22-calendar-booking-types/sub-specs/api-spec.md