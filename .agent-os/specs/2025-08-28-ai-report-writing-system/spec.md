# Spec Requirements Document

> Spec: AI Report Writing System
> Created: 2025-08-28
> Status: Core System Implemented (Updated 2025-09-01)

## Overview

Implement an AI-powered clinical report writing system that enables both manager-initiated and therapist-initiated workflows for automated report generation. The system will leverage existing AI infrastructure to auto-populate reports with patient data, medical history, and treatment summaries while providing full customization capabilities and multi-disciplinary integration.

The user experience adopts a guided, multi-step wizard for report creation (patient → type & title → disciplines → clinicians → priority & timeline), mirroring the proven appointment booking flow for clarity and reduced cognitive load.

**Implementation Update (2025-09-01)**: The system has been enhanced with a unified "Add Report" workflow that combines both manager-initiated and therapist-initiated flows into a single, streamlined user experience. This approach reduces complexity while maintaining all required functionality.

## User Stories

### Manager-Initiated Report Workflow
As a practice manager, I want to request specific reports from therapists so that I can ensure timely, consistent documentation and reduce administrative communication overhead.

The manager selects a patient and report type (discharge, progress, insurance, outcome summary), chooses which disciplines to include, sets a deadline, and the request automatically appears on the relevant therapists' dashboards with notifications.

### Therapist-Initiated Report Creation  
As a therapist, I want to proactively create reports for my patients so that I can maintain up-to-date documentation without waiting for manager requests.

The therapist selects a patient, chooses a report type, and the system auto-populates available data while allowing full editing control and AI-assisted content generation.

### AI-Assisted Content Generation
As a therapist, I want AI to automatically generate medical history and treatment summaries from existing patient data so that I can focus on clinical insights rather than data compilation.

The system automatically detects if recent medical history exists (within 1 week) and reuses it, otherwise generates new content from treatment notes, session records, and outcome measures while maintaining full edit control and revert capabilities.

## Spec Scope

1. **Dual Workflow Support** - Both manager-initiated and therapist-initiated report creation with role-appropriate interfaces
2. **AI Content Generation** - Automated medical history and treatment summary generation with edit control and revert functionality  
3. **Customizable Templates** - Practice-level template customization with field addition/deletion and question type selection
4. **Multi-disciplinary Integration** - Automatic discipline detection with selective inclusion for comprehensive patient reports
5. **Dashboard Integration** - Seamless integration with existing dashboard including in-app notifications and deadline tracking
6. **Wizard UX** - Multi-step report creation wizard for consistent, easy-to-follow flow

## Out of Scope

- External notification methods (SMS, email) - in-app notifications only for initial release
- Advanced version control for collaborative editing
- Direct billing system integration  
- Multi-language template support
- Advanced AI training or model customization

## Expected Deliverable

1. Manager and therapist dashboards showing pending/completed reports with deadline tracking and notification system
2. AI-powered report generation that auto-populates patient data, medical history, and treatment summaries with full edit control
3. Template customization interface allowing practices to modify report fields and question types accessible to admins and managers
4. Multi-step report creation wizard with step validation and role-aware defaults

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-28-ai-report-writing-system/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-28-ai-report-writing-system/sub-specs/technical-spec.md
- Database Schema: @.agent-os/specs/2025-08-28-ai-report-writing-system/sub-specs/database-schema.md
- API Specification: @.agent-os/specs/2025-08-28-ai-report-writing-system/sub-specs/api-spec.md
- Report Creation Wizard: @.agent-os/specs/2025-08-28-ai-report-writing-system/sub-specs/report-creation-wizard.md
- **Implementation Status Update**: @.agent-os/specs/2025-08-28-ai-report-writing-system/implementation-status-update-2025-09-01.md
