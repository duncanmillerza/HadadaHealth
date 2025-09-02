-- Migration 009: Add Individual Therapist Completion Tracking
-- Created: 2025-09-02
-- Purpose: Enable individual therapist completion tracking for multi-disciplinary reports
-- This allows each assigned therapist to mark their portion as complete independently

-- Create report_therapist_completions table
-- Tracks individual therapist completions for multi-disciplinary reports
CREATE TABLE IF NOT EXISTS report_therapist_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    therapist_id TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT (datetime('now')),
    completion_notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Foreign key relationships
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    
    -- Ensure each therapist can only complete once per report
    UNIQUE (report_id, therapist_id)
);

-- Add partial completion status to reports table
-- Update the CHECK constraint to include new status options
-- Note: SQLite doesn't support ALTER CHECK constraints, so we need to recreate the constraint via triggers

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_therapist_completions_report_id ON report_therapist_completions(report_id);
CREATE INDEX IF NOT EXISTS idx_therapist_completions_therapist_id ON report_therapist_completions(therapist_id);
CREATE INDEX IF NOT EXISTS idx_therapist_completions_completed_at ON report_therapist_completions(completed_at);

-- Create a trigger to automatically update report status based on therapist completions
CREATE TRIGGER IF NOT EXISTS update_report_status_on_completion
    AFTER INSERT ON report_therapist_completions
    BEGIN
        UPDATE reports 
        SET status = CASE 
            WHEN (
                SELECT COUNT(*) 
                FROM report_therapist_completions rtc 
                WHERE rtc.report_id = NEW.report_id
            ) >= (
                SELECT json_array_length(assigned_therapist_ids) 
                FROM reports r 
                WHERE r.id = NEW.report_id
            ) THEN 'completed'
            WHEN (
                SELECT COUNT(*) 
                FROM report_therapist_completions rtc 
                WHERE rtc.report_id = NEW.report_id
            ) > 0 THEN 'partially_completed'
            ELSE status
        END,
        completed_at = CASE 
            WHEN (
                SELECT COUNT(*) 
                FROM report_therapist_completions rtc 
                WHERE rtc.report_id = NEW.report_id
            ) >= (
                SELECT json_array_length(assigned_therapist_ids) 
                FROM reports r 
                WHERE r.id = NEW.report_id
            ) THEN datetime('now')
            ELSE completed_at
        END,
        updated_at = datetime('now')
        WHERE id = NEW.report_id;
    END;

-- Create a trigger to handle deletion of therapist completions
CREATE TRIGGER IF NOT EXISTS update_report_status_on_completion_delete
    AFTER DELETE ON report_therapist_completions
    BEGIN
        UPDATE reports 
        SET status = CASE 
            WHEN (
                SELECT COUNT(*) 
                FROM report_therapist_completions rtc 
                WHERE rtc.report_id = OLD.report_id
            ) >= (
                SELECT json_array_length(assigned_therapist_ids) 
                FROM reports r 
                WHERE r.id = OLD.report_id
            ) THEN 'completed'
            WHEN (
                SELECT COUNT(*) 
                FROM report_therapist_completions rtc 
                WHERE rtc.report_id = OLD.report_id
            ) > 0 THEN 'partially_completed'
            ELSE 'in_progress'
        END,
        completed_at = CASE 
            WHEN (
                SELECT COUNT(*) 
                FROM report_therapist_completions rtc 
                WHERE rtc.report_id = OLD.report_id
            ) = 0 THEN NULL
            ELSE completed_at
        END,
        updated_at = datetime('now')
        WHERE id = OLD.report_id;
    END;

-- Migration complete
-- Summary: Added individual therapist completion tracking with automatic status management