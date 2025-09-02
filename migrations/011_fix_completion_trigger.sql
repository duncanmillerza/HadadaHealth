-- Migration 011: Fix therapist completion trigger to use valid status values
-- Date: 2025-09-02
-- Description: Fix trigger to use 'in_progress' instead of 'partially_completed' to match CHECK constraint

-- Drop and recreate the trigger with correct status values
DROP TRIGGER IF EXISTS update_report_status_on_completion;

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
            ) > 0 THEN 'in_progress'
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

-- Also fix the deletion trigger
DROP TRIGGER IF EXISTS update_report_status_on_completion_delete;

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
            ) > 0 THEN 'in_progress'
            ELSE 'pending'
        END,
        completed_at = CASE 
            WHEN (
                SELECT COUNT(*) 
                FROM report_therapist_completions rtc 
                WHERE rtc.report_id = OLD.report_id
            ) >= (
                SELECT json_array_length(assigned_therapist_ids) 
                FROM reports r 
                WHERE r.id = OLD.report_id
            ) THEN datetime('now')
            ELSE NULL
        END,
        updated_at = datetime('now')
        WHERE id = OLD.report_id;
    END;