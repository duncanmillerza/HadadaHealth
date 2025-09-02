-- Migration 010: Add multiple therapist support to structured template instances
-- Date: 2025-09-02
-- Description: Add assigned_therapist_ids column and migrate existing single therapist_id data

-- Add new column for multiple therapist IDs (JSON array like reports table)
ALTER TABLE structured_template_instances 
ADD COLUMN assigned_therapist_ids TEXT DEFAULT '[]';

-- Migrate existing single therapist_id data to the new assigned_therapist_ids array
UPDATE structured_template_instances 
SET assigned_therapist_ids = CASE 
    WHEN therapist_id IS NOT NULL AND therapist_id != '' 
    THEN json_array(therapist_id)
    ELSE '[]'
END
WHERE assigned_therapist_ids = '[]';

-- Create index for the new column
CREATE INDEX idx_template_instances_assigned_therapists ON structured_template_instances(assigned_therapist_ids);