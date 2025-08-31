# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-28-ai-report-writing-system/spec.md

> Created: 2025-08-28
> Version: 1.0.0

## New Tables Required

### 1. Reports Table
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    report_type TEXT NOT NULL, -- 'discharge', 'progress', 'insurance', 'outcome_summary'
    template_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'overdue'
    requested_by_user_id TEXT, -- NULL for therapist-initiated
    assigned_therapist_ids TEXT NOT NULL, -- JSON array of therapist IDs
    deadline_date TEXT, -- ISO format date
    disciplines TEXT NOT NULL, -- JSON array: ['physiotherapy', 'occupational_therapy', 'speech_therapy']
    priority INTEGER DEFAULT 1, -- 1=low, 2=medium, 3=high
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    content TEXT, -- JSON blob of report content
    ai_generated_sections TEXT, -- JSON array tracking which sections used AI
    last_ai_generation_date TEXT,
    notes TEXT,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),
    CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue')),
    CHECK (priority IN (1, 2, 3))
);
```

### 2. Report Templates Table  
```sql
CREATE TABLE report_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    template_type TEXT NOT NULL, -- 'discharge', 'progress', 'insurance', 'outcome_summary'
    practice_id TEXT, -- NULL for system templates, practice-specific otherwise
    is_active BOOLEAN DEFAULT 1,
    is_system_default BOOLEAN DEFAULT 0,
    fields_schema TEXT NOT NULL, -- JSON schema defining fields and question types
    section_order TEXT NOT NULL, -- JSON array defining section display order
    created_by_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    version INTEGER DEFAULT 1,
    CHECK (template_type IN ('discharge', 'progress', 'insurance', 'outcome_summary', 'assessment', 'custom'))
);
```

### 3. Report Content Versions Table
```sql
CREATE TABLE report_content_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL, -- JSON blob of complete report content
    ai_generated_sections TEXT, -- JSON array tracking AI vs manual content
    created_by_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    change_summary TEXT, -- Brief description of changes made
    is_ai_generated BOOLEAN DEFAULT 0,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    UNIQUE (report_id, version_number)
);
```

### 4. AI Content Cache Table
```sql
CREATE TABLE ai_content_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    content_type TEXT NOT NULL, -- 'medical_history', 'treatment_summary', 'assessment_summary'
    discipline TEXT, -- NULL for multi-disciplinary content
    content TEXT NOT NULL, -- Generated AI content
    source_data_hash TEXT NOT NULL, -- Hash of source data used for generation
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL, -- Auto-expire after 1 week
    usage_count INTEGER DEFAULT 0,
    last_used_at TEXT,
    is_valid BOOLEAN DEFAULT 1,
    CHECK (content_type IN ('medical_history', 'treatment_summary', 'assessment_summary', 'outcome_summary'))
);
```

### 5. Report Notifications Table
```sql
CREATE TABLE report_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    notification_type TEXT NOT NULL, -- 'request', 'reminder', 'completion', 'overdue'
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    read_at TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    CHECK (notification_type IN ('request', 'reminder', 'completion', 'overdue'))
);
```

## Database Indexes

```sql
-- Performance indexes for common queries
CREATE INDEX idx_reports_patient_id ON reports(patient_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_deadline ON reports(deadline_date);
CREATE INDEX idx_reports_assigned_therapists ON reports(assigned_therapist_ids);
CREATE INDEX idx_report_templates_type ON report_templates(template_type);
CREATE INDEX idx_report_templates_practice ON report_templates(practice_id);
CREATE INDEX idx_ai_cache_patient_type ON ai_content_cache(patient_id, content_type);
CREATE INDEX idx_ai_cache_expires ON ai_content_cache(expires_at);
CREATE INDEX idx_notifications_user_read ON report_notifications(user_id, is_read);
```

## Migration Script (Sequential Number TBD)

```sql
-- Migration: Add Report Writing System Tables
-- File: migrations/XXX_add_report_writing_system.sql

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Create tables in dependency order
-- [Insert CREATE TABLE statements above]

-- Create indexes
-- [Insert CREATE INDEX statements above]  

-- Insert default system templates
INSERT INTO report_templates (name, description, template_type, is_system_default, fields_schema, section_order, created_by_user_id) VALUES 
(
    'Standard Progress Report',
    'Default template for patient progress reporting',
    'progress',
    1,
    '{"patient_info":{"type":"auto","required":true},"medical_history":{"type":"ai_paragraph","required":true,"editable":true},"assessment_findings":{"type":"paragraph","required":true},"outcome_measures":{"type":"structured","required":true},"interventions":{"type":"paragraph","required":true},"progress_summary":{"type":"ai_paragraph","required":true,"editable":true},"recommendations":{"type":"paragraph","required":true},"therapist_signature":{"type":"signature","required":true}}',
    '["patient_info","medical_history","assessment_findings","outcome_measures","interventions","progress_summary","recommendations","therapist_signature"]',
    'system'
);

-- Verify tables created successfully
.tables
```

## Data Relationships

### Key Foreign Key Relationships:
- **reports.template_id** → **report_templates.id**  
- **report_content_versions.report_id** → **reports.id**
- **report_notifications.report_id** → **reports.id**
- **reports.patient_id** → **patients.patient_id** (existing table)
- **reports.assigned_therapist_ids** → **users.user_id** (existing table, JSON array)

### Data Integrity Rules:
- Cascade delete for report content versions and notifications when report is deleted
- Automatic expiry of AI cache content after 1 week  
- Version tracking for all report content changes
- Audit trail maintenance through content versions table