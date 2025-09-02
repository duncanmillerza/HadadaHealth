-- Migration: Seed default appointment types with hierarchical structure
-- Purpose: Provide standard appointment type categories that practices can use and customize
-- Dependencies: 001_create_appointment_types.sql
-- Date: 2025-08-22

-- Insert top-level (parent) appointment types - these are global (practice_id = NULL)

-- Patient-related appointments (green color scheme)
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Patient', NULL, NULL, '#2D6356', 30, 'Patient treatment appointments', 1);

-- Meeting-related appointments (blue color scheme)  
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Meeting', NULL, NULL, '#1E40AF', 60, 'Professional meetings and consultations', 1);

-- Administrative appointments (orange color scheme)
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Admin', NULL, NULL, '#EA580C', 30, 'Administrative tasks and activities', 1);

-- Travel appointments (purple color scheme)
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Travel', NULL, NULL, '#7C3AED', 60, 'Travel to/from appointments or events', 1);

-- Get the IDs of the parent types we just created for sub-type insertion
-- Patient sub-types
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('New Assessment', 
 (SELECT id FROM appointment_types WHERE name = 'Patient' AND parent_id IS NULL LIMIT 1), 
 NULL, '#16A34A', 45, 'Initial patient assessment appointment', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Follow-up Assessment', 
 (SELECT id FROM appointment_types WHERE name = 'Patient' AND parent_id IS NULL LIMIT 1), 
 NULL, '#16A34A', 30, 'Follow-up assessment appointment', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Treatment', 
 (SELECT id FROM appointment_types WHERE name = 'Patient' AND parent_id IS NULL LIMIT 1), 
 NULL, '#059669', 30, 'Standard treatment session', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Neurological', 
 (SELECT id FROM appointment_types WHERE name = 'Patient' AND parent_id IS NULL LIMIT 1), 
 NULL, '#0D9488', 45, 'Neurological assessment or treatment', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Group Therapy', 
 (SELECT id FROM appointment_types WHERE name = 'Patient' AND parent_id IS NULL LIMIT 1), 
 NULL, '#0891B2', 60, 'Group therapy session', 1);

-- Meeting sub-types
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('MDT Meeting', 
 (SELECT id FROM appointment_types WHERE name = 'Meeting' AND parent_id IS NULL LIMIT 1), 
 NULL, '#2563EB', 60, 'Multidisciplinary team meeting', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Family Meeting', 
 (SELECT id FROM appointment_types WHERE name = 'Meeting' AND parent_id IS NULL LIMIT 1), 
 NULL, '#3B82F6', 45, 'Meeting with patient family members', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Academic Meeting', 
 (SELECT id FROM appointment_types WHERE name = 'Meeting' AND parent_id IS NULL LIMIT 1), 
 NULL, '#6366F1', 60, 'Academic or educational meeting', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Consultation', 
 (SELECT id FROM appointment_types WHERE name = 'Meeting' AND parent_id IS NULL LIMIT 1), 
 NULL, '#8B5CF6', 30, 'Professional consultation meeting', 1);

-- Admin sub-types
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Documentation', 
 (SELECT id FROM appointment_types WHERE name = 'Admin' AND parent_id IS NULL LIMIT 1), 
 NULL, '#F59E0B', 30, 'Administrative documentation time', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Equipment Maintenance', 
 (SELECT id FROM appointment_types WHERE name = 'Admin' AND parent_id IS NULL LIMIT 1), 
 NULL, '#EF4444', 45, 'Equipment maintenance and checks', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Training', 
 (SELECT id FROM appointment_types WHERE name = 'Admin' AND parent_id IS NULL LIMIT 1), 
 NULL, '#10B981', 120, 'Professional training or development', 1);

-- Travel sub-types
INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Home Visit', 
 (SELECT id FROM appointment_types WHERE name = 'Travel' AND parent_id IS NULL LIMIT 1), 
 NULL, '#A855F7', 90, 'Travel time for home visit', 1);

INSERT OR IGNORE INTO appointment_types (name, parent_id, practice_id, color, duration, description, is_active) VALUES
('Off-site Meeting', 
 (SELECT id FROM appointment_types WHERE name = 'Travel' AND parent_id IS NULL LIMIT 1), 
 NULL, '#9333EA', 120, 'Travel time for off-site meeting', 1);