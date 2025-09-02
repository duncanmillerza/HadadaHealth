# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-28-enhanced-report-customization/spec.md

> Created: 2025-08-28
> Version: 1.0.0

## Additional Tables Required

### 1. Template Versions Table
```sql
CREATE TABLE template_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    template_data TEXT NOT NULL, -- Complete JSON template definition
    field_schema TEXT NOT NULL, -- JSON schema for validation
    conditional_rules TEXT, -- JSON conditional logic rules
    created_by_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    change_summary TEXT,
    is_active BOOLEAN DEFAULT 0, -- Only one version can be active
    approval_status TEXT DEFAULT 'draft', -- 'draft', 'pending', 'approved', 'rejected'
    approved_by_user_id TEXT,
    approved_at TEXT,
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE,
    UNIQUE (template_id, version_number),
    CHECK (approval_status IN ('draft', 'pending', 'approved', 'rejected'))
);
```

### 2. Field Type Definitions Table
```sql
CREATE TABLE field_type_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_type_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    validation_schema TEXT NOT NULL, -- JSON schema for field validation
    rendering_config TEXT NOT NULL, -- JSON config for UI rendering
    default_properties TEXT, -- JSON default field properties
    is_system_type BOOLEAN DEFAULT 0, -- System vs custom field types
    category TEXT NOT NULL DEFAULT 'general', -- 'general', 'clinical', 'signature', 'media'
    icon_name TEXT,
    created_by_user_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active BOOLEAN DEFAULT 1,
    CHECK (category IN ('general', 'clinical', 'signature', 'media', 'calculation', 'conditional'))
);
```

### 3. Template Components Table
```sql
CREATE TABLE template_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL, -- 'section', 'field_group', 'conditional_block'
    display_name TEXT NOT NULL,
    description TEXT,
    component_schema TEXT NOT NULL, -- JSON component definition
    preview_image_path TEXT,
    category TEXT NOT NULL DEFAULT 'general',
    is_system_component BOOLEAN DEFAULT 0,
    created_by_user_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    CHECK (component_type IN ('section', 'field_group', 'conditional_block', 'layout'))
);
```

### 4. Conditional Rules Table
```sql
CREATE TABLE conditional_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    template_id INTEGER NOT NULL,
    trigger_field_path TEXT NOT NULL, -- JSON path to trigger field
    trigger_condition TEXT NOT NULL, -- JSON condition definition
    action_type TEXT NOT NULL, -- 'show', 'hide', 'enable', 'disable', 'populate', 'validate'
    target_field_paths TEXT NOT NULL, -- JSON array of target field paths
    action_config TEXT NOT NULL, -- JSON action configuration
    execution_order INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    created_by_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE,
    CHECK (action_type IN ('show', 'hide', 'enable', 'disable', 'populate', 'validate', 'calculate'))
);
```

### 5. User Template Preferences Table
```sql
CREATE TABLE user_template_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    template_id INTEGER NOT NULL,
    preference_type TEXT NOT NULL, -- 'layout', 'defaults', 'shortcuts', 'visibility'
    preference_data TEXT NOT NULL, -- JSON preference configuration
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE,
    UNIQUE (user_id, template_id, preference_type),
    CHECK (preference_type IN ('layout', 'defaults', 'shortcuts', 'visibility', 'formatting'))
);
```

### 6. Template Change Log Table
```sql
CREATE TABLE template_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    change_type TEXT NOT NULL, -- 'create', 'update', 'delete', 'activate', 'deactivate'
    field_path TEXT, -- JSON path of changed field (if applicable)
    old_value TEXT, -- JSON representation of old value
    new_value TEXT, -- JSON representation of new value
    change_description TEXT,
    user_id TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES template_versions(id) ON DELETE CASCADE,
    CHECK (change_type IN ('create', 'update', 'delete', 'activate', 'deactivate', 'approve', 'reject'))
);
```

### 7. Field Validation Rules Table
```sql
CREATE TABLE field_validation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    field_type TEXT NOT NULL,
    validation_type TEXT NOT NULL, -- 'required', 'format', 'range', 'custom'
    rule_config TEXT NOT NULL, -- JSON validation configuration
    error_message TEXT NOT NULL,
    is_system_rule BOOLEAN DEFAULT 0,
    created_by_user_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active BOOLEAN DEFAULT 1,
    CHECK (validation_type IN ('required', 'format', 'range', 'custom', 'conditional', 'cross_field'))
);
```

## Enhanced Indexes for Performance

```sql
-- Template customization performance indexes
CREATE INDEX idx_template_versions_template_id ON template_versions(template_id, version_number);
CREATE INDEX idx_template_versions_active ON template_versions(template_id, is_active);
CREATE INDEX idx_field_types_category ON field_type_definitions(category, is_active);
CREATE INDEX idx_template_components_type ON template_components(component_type, is_active);
CREATE INDEX idx_conditional_rules_template ON conditional_rules(template_id, is_active);
CREATE INDEX idx_conditional_rules_execution ON conditional_rules(template_id, execution_order);
CREATE INDEX idx_user_preferences_user_template ON user_template_preferences(user_id, template_id);
CREATE INDEX idx_change_log_template_time ON template_change_log(template_id, created_at);
CREATE INDEX idx_validation_rules_type ON field_validation_rules(field_type, is_active);
```

## Updated Report Templates Table Schema

```sql
-- Add new columns to existing report_templates table
ALTER TABLE report_templates ADD COLUMN current_version_id INTEGER;
ALTER TABLE report_templates ADD COLUMN has_conditional_logic BOOLEAN DEFAULT 0;
ALTER TABLE report_templates ADD COLUMN last_modified_by_user_id TEXT;
ALTER TABLE report_templates ADD COLUMN approval_required BOOLEAN DEFAULT 0;
ALTER TABLE report_templates ADD COLUMN component_count INTEGER DEFAULT 0;

-- Add foreign key constraint (requires recreation in SQLite)
-- This would be handled in a migration script
```

## Migration Script for Enhanced Customization

```sql
-- Migration: Add Enhanced Report Customization Tables
-- File: migrations/XXX_add_report_customization.sql

PRAGMA foreign_keys = ON;

-- Create new tables
-- [Insert all CREATE TABLE statements above]

-- Create performance indexes  
-- [Insert all CREATE INDEX statements above]

-- Insert default field type definitions
INSERT INTO field_type_definitions (field_type_name, display_name, description, validation_schema, rendering_config, is_system_type, category) VALUES 
('rich_text', 'Rich Text Area', 'Multi-line text with formatting', '{"type": "string", "minLength": 0}', '{"editor": "tinymce", "height": 200}', 1, 'general'),
('signature', 'Digital Signature', 'Electronic signature capture', '{"type": "string", "format": "signature"}', '{"capture": "touch", "width": 400, "height": 150}', 1, 'signature'),
('file_upload', 'File Upload', 'Document attachment field', '{"type": "array", "items": {"type": "string", "format": "uri"}}', '{"accept": ".pdf,.doc,.jpg", "maxFiles": 5}', 1, 'media'),
('dropdown_dynamic', 'Dynamic Dropdown', 'Database-populated dropdown', '{"type": "string", "enum": []}', '{"source": "query", "searchable": true}', 1, 'general'),
('conditional_section', 'Conditional Section', 'Show/hide section based on logic', '{"type": "object"}', '{"collapsible": true, "conditional": true}', 1, 'conditional');

-- Insert default template components
INSERT INTO template_components (component_name, component_type, display_name, description, component_schema, is_system_component, category) VALUES
('patient_demographics', 'section', 'Patient Demographics', 'Standard patient information section', '{"fields": ["name", "dob", "id_number", "contact_info"]}', 1, 'clinical'),
('assessment_summary', 'field_group', 'Assessment Summary', 'Clinical assessment field group', '{"fields": ["assessment_date", "findings", "recommendations"]}', 1, 'clinical'),
('treatment_history', 'section', 'Treatment History', 'AI-generated treatment history section', '{"ai_generated": true, "editable": true}', 1, 'clinical');

-- Verify table creation
.tables
```

## Data Relationships & Constraints

### Key Relationships:
- **template_versions.template_id** → **report_templates.id** (CASCADE DELETE)
- **conditional_rules.template_id** → **report_templates.id** (CASCADE DELETE)  
- **user_template_preferences.template_id** → **report_templates.id** (CASCADE DELETE)
- **template_change_log.template_id** → **report_templates.id** (CASCADE DELETE)
- **template_change_log.version_id** → **template_versions.id** (CASCADE DELETE)

### Business Logic Constraints:
- Only one template version can be active per template
- Conditional rules execute in order (execution_order field)
- Field validation rules are applied based on field type matching
- Template changes are logged for audit compliance
- User preferences are maintained per template and user combination

### Performance Considerations:
- Composite indexes on frequently queried combinations
- JSON field indexing for conditional rule evaluation
- Template version caching for active versions
- Change log partitioning by date for large installations