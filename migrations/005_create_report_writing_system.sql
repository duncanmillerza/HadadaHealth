-- Migration: Create AI Report Writing System tables
-- Purpose: Support automated clinical report generation with AI assistance
-- Dependencies: None (standalone system)
-- Date: 2025-08-28

-- Enable foreign key constraints for referential integrity
PRAGMA foreign_keys = ON;

-- Create report_templates table
-- Stores customizable report templates with field schemas and validation
CREATE TABLE IF NOT EXISTS report_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    template_type TEXT NOT NULL,
    practice_id TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_system_default BOOLEAN DEFAULT 0,
    fields_schema TEXT NOT NULL, -- JSON schema defining fields and question types
    section_order TEXT NOT NULL, -- JSON array defining section display order
    created_by_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    version INTEGER DEFAULT 1,
    
    -- Ensure valid template types
    CHECK (template_type IN ('discharge', 'progress', 'insurance', 'outcome_summary', 'assessment', 'custom'))
);

-- Create reports table
-- Main table for tracking report requests, assignments, and content
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    report_type TEXT NOT NULL, -- 'discharge', 'progress', 'insurance', 'outcome_summary'
    template_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'overdue'
    requested_by_user_id TEXT, -- NULL for therapist-initiated reports
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
    
    -- Foreign key relationships
    FOREIGN KEY (template_id) REFERENCES report_templates(id),
    
    -- Ensure valid status and priority values
    CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue')),
    CHECK (priority IN (1, 2, 3))
);

-- Create report_content_versions table
-- Version control for all report content changes with audit trail
CREATE TABLE IF NOT EXISTS report_content_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL, -- JSON blob of complete report content
    ai_generated_sections TEXT, -- JSON array tracking AI vs manual content
    created_by_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    change_summary TEXT, -- Brief description of changes made
    is_ai_generated BOOLEAN DEFAULT 0,
    
    -- Foreign key with cascade delete
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    
    -- Ensure unique version numbers per report
    UNIQUE (report_id, version_number)
);

-- Create ai_content_cache table
-- Cache AI-generated content with expiry for performance and consistency
CREATE TABLE IF NOT EXISTS ai_content_cache (
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
    
    -- Ensure valid content types
    CHECK (content_type IN ('medical_history', 'treatment_summary', 'assessment_summary', 'outcome_summary'))
);

-- Create report_notifications table
-- In-app notification system for report workflow management
CREATE TABLE IF NOT EXISTS report_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    notification_type TEXT NOT NULL, -- 'request', 'reminder', 'completion', 'overdue'
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    read_at TEXT,
    
    -- Foreign key with cascade delete
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    
    -- Ensure valid notification types
    CHECK (notification_type IN ('request', 'reminder', 'completion', 'overdue'))
);

-- Performance indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_reports_patient_id ON reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_deadline ON reports(deadline_date);
CREATE INDEX IF NOT EXISTS idx_reports_assigned_therapists ON reports(assigned_therapist_ids);
CREATE INDEX IF NOT EXISTS idx_reports_template ON reports(template_id);

CREATE INDEX IF NOT EXISTS idx_report_templates_type ON report_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_report_templates_practice ON report_templates(practice_id);
CREATE INDEX IF NOT EXISTS idx_report_templates_active ON report_templates(is_active, practice_id);

CREATE INDEX IF NOT EXISTS idx_content_versions_report ON report_content_versions(report_id, version_number);
CREATE INDEX IF NOT EXISTS idx_content_versions_user ON report_content_versions(created_by_user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_ai_cache_patient_type ON ai_content_cache(patient_id, content_type);
CREATE INDEX IF NOT EXISTS idx_ai_cache_expires ON ai_content_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_ai_cache_discipline ON ai_content_cache(discipline, is_valid);

CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON report_notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON report_notifications(notification_type, created_at);

-- Create triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_reports_timestamp 
    AFTER UPDATE ON reports
BEGIN
    UPDATE reports SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_report_templates_timestamp 
    AFTER UPDATE ON report_templates
BEGIN
    UPDATE report_templates SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Create trigger to automatically create content version on report content changes
CREATE TRIGGER IF NOT EXISTS create_content_version_on_update
    AFTER UPDATE OF content ON reports
    WHEN NEW.content IS NOT NULL AND NEW.content != OLD.content
BEGIN
    INSERT INTO report_content_versions (
        report_id, 
        version_number, 
        content, 
        ai_generated_sections,
        created_by_user_id, 
        change_summary,
        is_ai_generated
    )
    VALUES (
        NEW.id,
        COALESCE((SELECT MAX(version_number) FROM report_content_versions WHERE report_id = NEW.id), 0) + 1,
        NEW.content,
        NEW.ai_generated_sections,
        'system', -- Default to system user for automated versioning
        'Automatic version created on content update',
        0
    );
END;

-- Create trigger to invalidate AI cache when source data changes
-- Note: This would typically be triggered by application logic based on treatment note updates
CREATE TRIGGER IF NOT EXISTS invalidate_ai_cache_on_expiry
    AFTER UPDATE ON ai_content_cache
    WHEN NEW.expires_at < datetime('now')
BEGIN
    UPDATE ai_content_cache SET is_valid = 0 WHERE id = NEW.id;
END;