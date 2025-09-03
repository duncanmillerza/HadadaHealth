# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-22-calendar-booking-types/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Schema Changes

**New Tables:**

```sql
-- appointment_types: Master list of appointment types
CREATE TABLE appointment_types (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    parent_id BIGINT UNSIGNED NULL,
    color VARCHAR(7) DEFAULT '#007bff',
    is_default BOOLEAN DEFAULT false,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (parent_id) REFERENCES appointment_types(id) ON DELETE CASCADE,
    INDEX idx_parent_id (parent_id),
    INDEX idx_is_default (is_default),
    INDEX idx_sort_order (sort_order)
);

-- practice_appointment_types: Practice-specific customizations
CREATE TABLE practice_appointment_types (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    practice_id BIGINT UNSIGNED NOT NULL,
    appointment_type_id BIGINT UNSIGNED NOT NULL,
    custom_name VARCHAR(255) NULL,
    custom_description TEXT NULL,
    custom_color VARCHAR(7) NULL,
    is_enabled BOOLEAN DEFAULT true,
    default_duration INT DEFAULT 30,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (practice_id) REFERENCES practices(id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_type_id) REFERENCES appointment_types(id) ON DELETE CASCADE,
    UNIQUE KEY unique_practice_type (practice_id, appointment_type_id),
    INDEX idx_practice_id (practice_id),
    INDEX idx_enabled (is_enabled)
);
```

**Table Modifications:**

```sql
-- appointments: Add appointment type reference
ALTER TABLE appointments 
ADD COLUMN appointment_type_id BIGINT UNSIGNED NULL AFTER id,
ADD FOREIGN KEY (appointment_type_id) REFERENCES appointment_types(id) ON DELETE SET NULL,
ADD INDEX idx_appointment_type_id (appointment_type_id);
```

## Migrations

**Migration 1: Create appointment_types table**
- Create base appointment_types structure with self-referential hierarchy
- Add indexes for performance optimization
- Include default color and sorting capabilities

**Migration 2: Create practice_appointment_types table**
- Practice-specific customization layer
- Override capabilities for names, colors, descriptions
- Enable/disable functionality per practice
- Default duration settings

**Migration 3: Update appointments table**
- Add appointment_type_id foreign key
- Maintain backward compatibility with NULL values
- Index for query performance

**Migration 4: Seed default appointment types**
- Create default hierarchy: Patient, Meeting, Admin, Travel
- Add common sub-types: MDT meetings, assessments, follow-ups
- Set appropriate colors and sort orders
- Mark as system defaults