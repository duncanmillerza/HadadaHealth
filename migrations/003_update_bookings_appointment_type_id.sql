-- Migration: Add appointment_type_id foreign key to bookings table
-- Purpose: Link existing bookings to the new appointment types system
-- Dependencies: 001_create_appointment_types.sql, 002_create_practice_appointment_types.sql
-- Date: 2025-08-22

-- Add appointment_type_id column to existing bookings table
ALTER TABLE bookings ADD COLUMN appointment_type_id INTEGER;

-- Add foreign key constraint (SQLite doesn't support adding FK constraints to existing tables directly)
-- So we'll handle this with application-level validation for now

-- Create index for faster queries on appointment_type_id
CREATE INDEX IF NOT EXISTS idx_bookings_appointment_type_id ON bookings(appointment_type_id);

-- Create index for faster queries combining appointment type and therapist
CREATE INDEX IF NOT EXISTS idx_bookings_appointment_type_therapist ON bookings(appointment_type_id, therapist);

-- Create index for faster queries combining appointment type and date
CREATE INDEX IF NOT EXISTS idx_bookings_appointment_type_date ON bookings(appointment_type_id, date);