-- Migration: Create appointment_types table with hierarchical structure
-- Purpose: Support customizable appointment type categorization for practices
-- Dependencies: None
-- Date: 2025-08-22

-- Create appointment_types table with self-referential parent/child relationships
CREATE TABLE IF NOT EXISTS appointment_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER,
    practice_id INTEGER,
    color TEXT DEFAULT '#2D6356',
    duration INTEGER DEFAULT 30,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to self for hierarchical structure
    FOREIGN KEY (parent_id) REFERENCES appointment_types(id),
    
    -- Unique constraint ensures no duplicate names within same practice/parent combination
    UNIQUE(name, practice_id, parent_id)
);

-- Create index for faster queries on parent_id (hierarchical queries)
CREATE INDEX IF NOT EXISTS idx_appointment_types_parent_id ON appointment_types(parent_id);

-- Create index for faster queries on practice_id
CREATE INDEX IF NOT EXISTS idx_appointment_types_practice_id ON appointment_types(practice_id);

-- Create index for active appointment types filtering
CREATE INDEX IF NOT EXISTS idx_appointment_types_active ON appointment_types(is_active, practice_id);

-- Create trigger to update updated_at timestamp on modification
CREATE TRIGGER IF NOT EXISTS update_appointment_types_timestamp 
    AFTER UPDATE ON appointment_types
BEGIN
    UPDATE appointment_types SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;