-- Migration 007: Create structured report templates system
-- This migration creates tables for structured report templates with JSON-based definitions

-- Create structured_templates table for template definitions
CREATE TABLE IF NOT EXISTS structured_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'clinical',
    template_structure TEXT NOT NULL, -- JSON structure of the template
    auto_populate_mapping TEXT, -- JSON mapping for auto-population fields
    is_active BOOLEAN DEFAULT 1,
    version INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create structured_template_instances table for saved template instances
CREATE TABLE IF NOT EXISTS structured_template_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    therapist_id TEXT, -- User who created the instance
    instance_data TEXT NOT NULL, -- JSON data with filled values
    sections_deleted TEXT, -- JSON array of deleted section IDs
    status TEXT DEFAULT 'draft', -- 'draft', 'completed', 'archived'
    title TEXT, -- Custom title for this instance
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    FOREIGN KEY (template_id) REFERENCES structured_templates(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_structured_templates_active ON structured_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_structured_templates_category ON structured_templates(category);
CREATE INDEX IF NOT EXISTS idx_template_instances_patient ON structured_template_instances(patient_id);
CREATE INDEX IF NOT EXISTS idx_template_instances_template ON structured_template_instances(template_id);
CREATE INDEX IF NOT EXISTS idx_template_instances_status ON structured_template_instances(status);
CREATE INDEX IF NOT EXISTS idx_template_instances_therapist ON structured_template_instances(therapist_id);

-- Create update triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_structured_templates_timestamp 
    AFTER UPDATE ON structured_templates
    FOR EACH ROW
BEGIN
    UPDATE structured_templates 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_template_instances_timestamp 
    AFTER UPDATE ON structured_template_instances
    FOR EACH ROW
BEGIN
    UPDATE structured_template_instances 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Add completion timestamp trigger
CREATE TRIGGER IF NOT EXISTS set_template_instance_completion 
    AFTER UPDATE OF status ON structured_template_instances
    FOR EACH ROW
    WHEN NEW.status = 'completed' AND OLD.status != 'completed'
BEGIN
    UPDATE structured_template_instances 
    SET completed_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;