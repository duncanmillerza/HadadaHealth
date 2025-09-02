-- Migration: Create practice_appointment_types table for practice-specific customizations
-- Purpose: Allow practices to customize appointment type settings (duration, billing, notes)
-- Dependencies: 001_create_appointment_types.sql
-- Date: 2025-08-22

-- Create practice_appointment_types table for practice-specific appointment type customizations
CREATE TABLE IF NOT EXISTS practice_appointment_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    practice_id INTEGER NOT NULL,
    appointment_type_id INTEGER NOT NULL,
    default_duration INTEGER,
    default_billing_code TEXT,
    default_notes TEXT,
    is_enabled BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (appointment_type_id) REFERENCES appointment_types(id) ON DELETE CASCADE,
    
    -- Unique constraint ensures each practice can only have one customization per appointment type
    UNIQUE(practice_id, appointment_type_id)
);

-- Create index for faster queries on practice_id
CREATE INDEX IF NOT EXISTS idx_practice_appointment_types_practice_id ON practice_appointment_types(practice_id);

-- Create index for faster queries on appointment_type_id
CREATE INDEX IF NOT EXISTS idx_practice_appointment_types_appointment_type_id ON practice_appointment_types(appointment_type_id);

-- Create index for sort order queries (for UI ordering)
CREATE INDEX IF NOT EXISTS idx_practice_appointment_types_sort_order ON practice_appointment_types(practice_id, sort_order);

-- Create trigger to update updated_at timestamp on modification
CREATE TRIGGER IF NOT EXISTS update_practice_appointment_types_timestamp 
    AFTER UPDATE ON practice_appointment_types
BEGIN
    UPDATE practice_appointment_types SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;