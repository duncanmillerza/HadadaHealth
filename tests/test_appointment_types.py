"""
Unit tests for AppointmentType model relationships and validation rules

Tests the hierarchical structure, validation, and business logic
for appointment types and their practice-specific customizations.
"""
import pytest
import sqlite3
from datetime import datetime


class TestAppointmentTypeModel:
    """Test suite for AppointmentType model"""
    
    def test_appointment_type_creation(self, appointment_types_table_setup):
        """Test basic appointment type creation"""
        conn = appointment_types_table_setup
        
        # Insert test practice
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        # Test creating a parent appointment type
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id, description) 
            VALUES (?, ?, ?)
        """, ("Patient", practice_id, "Patient appointments"))
        
        appointment_type_id = conn.lastrowid
        
        # Verify creation
        result = conn.execute("""
            SELECT name, practice_id, description, parent_id, is_active 
            FROM appointment_types WHERE id = ?
        """, (appointment_type_id,)).fetchone()
        
        assert result['name'] == "Patient"
        assert result['practice_id'] == practice_id
        assert result['description'] == "Patient appointments"
        assert result['parent_id'] is None
        assert result['is_active'] == 1
    
    def test_hierarchical_relationship(self, appointment_types_table_setup):
        """Test parent-child relationships in appointment types"""
        conn = appointment_types_table_setup
        
        # Insert test practice
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        # Create parent appointment type
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id, description) 
            VALUES (?, ?, ?)
        """, ("Patient", practice_id, "Patient appointments"))
        parent_id = conn.lastrowid
        
        # Create child appointment type
        conn.execute("""
            INSERT INTO appointment_types (name, parent_id, practice_id, description) 
            VALUES (?, ?, ?, ?)
        """, ("New Assessment", parent_id, practice_id, "New patient assessment"))
        child_id = conn.lastrowid
        
        # Test hierarchical query - get children of parent
        children = conn.execute("""
            SELECT id, name, parent_id 
            FROM appointment_types 
            WHERE parent_id = ?
        """, (parent_id,)).fetchall()
        
        assert len(children) == 1
        assert children[0]['name'] == "New Assessment"
        assert children[0]['parent_id'] == parent_id
        
        # Test getting parent from child
        parent = conn.execute("""
            SELECT p.id, p.name 
            FROM appointment_types c
            JOIN appointment_types p ON c.parent_id = p.id
            WHERE c.id = ?
        """, (child_id,)).fetchone()
        
        assert parent['name'] == "Patient"
        assert parent['id'] == parent_id
    
    def test_unique_constraint_validation(self, appointment_types_table_setup):
        """Test unique constraint for name, practice_id, parent_id combination"""
        conn = appointment_types_table_setup
        
        # Insert test practice
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        # Create first appointment type
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Assessment", practice_id))
        
        # Try to create duplicate - should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO appointment_types (name, practice_id) 
                VALUES (?, ?)
            """, ("Assessment", practice_id))
    
    def test_multiple_practice_isolation(self, appointment_types_table_setup):
        """Test that appointment types are isolated by practice"""
        conn = appointment_types_table_setup
        
        # Create two practices
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Practice A",))
        practice_a_id = conn.lastrowid
        
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Practice B",))
        practice_b_id = conn.lastrowid
        
        # Create same-named appointment type for both practices
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Assessment", practice_a_id))
        
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Assessment", practice_b_id))
        
        # Both should be created successfully
        practice_a_types = conn.execute("""
            SELECT name FROM appointment_types WHERE practice_id = ?
        """, (practice_a_id,)).fetchall()
        
        practice_b_types = conn.execute("""
            SELECT name FROM appointment_types WHERE practice_id = ?
        """, (practice_b_id,)).fetchall()
        
        assert len(practice_a_types) == 1
        assert len(practice_b_types) == 1
        assert practice_a_types[0]['name'] == "Assessment"
        assert practice_b_types[0]['name'] == "Assessment"
    
    def test_default_values(self, appointment_types_table_setup):
        """Test that default values are set correctly"""
        conn = appointment_types_table_setup
        
        # Insert test practice
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        # Create appointment type with minimal data
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Test Type", practice_id))
        
        appointment_type_id = conn.lastrowid
        
        # Check defaults
        result = conn.execute("""
            SELECT color, duration, is_active, created_at, updated_at
            FROM appointment_types WHERE id = ?
        """, (appointment_type_id,)).fetchone()
        
        assert result['color'] == '#2D6356'
        assert result['duration'] == 30
        assert result['is_active'] == 1
        assert result['created_at'] is not None
        assert result['updated_at'] is not None
    
    def test_deep_hierarchy_levels(self, appointment_types_table_setup):
        """Test creating multiple levels of hierarchy"""
        conn = appointment_types_table_setup
        
        # Insert test practice
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        # Create 3-level hierarchy: Patient -> Assessment -> New Assessment
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Patient", practice_id))
        level1_id = conn.lastrowid
        
        conn.execute("""
            INSERT INTO appointment_types (name, parent_id, practice_id) 
            VALUES (?, ?, ?)
        """, ("Assessment", level1_id, practice_id))
        level2_id = conn.lastrowid
        
        conn.execute("""
            INSERT INTO appointment_types (name, parent_id, practice_id) 
            VALUES (?, ?, ?)
        """, ("New Assessment", level2_id, practice_id))
        level3_id = conn.lastrowid
        
        # Test deep hierarchy query
        result = conn.execute("""
            SELECT 
                l3.name as level3_name,
                l2.name as level2_name, 
                l1.name as level1_name
            FROM appointment_types l3
            JOIN appointment_types l2 ON l3.parent_id = l2.id
            JOIN appointment_types l1 ON l2.parent_id = l1.id
            WHERE l3.id = ?
        """, (level3_id,)).fetchone()
        
        assert result['level1_name'] == "Patient"
        assert result['level2_name'] == "Assessment"
        assert result['level3_name'] == "New Assessment"


class TestPracticeAppointmentTypeModel:
    """Test suite for PracticeAppointmentType model"""
    
    def test_practice_appointment_type_creation(self, practice_appointment_types_table_setup):
        """Test creating practice-specific appointment type settings"""
        conn = practice_appointment_types_table_setup
        
        # Set up prerequisite data
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Assessment", practice_id))
        appointment_type_id = conn.lastrowid
        
        # Create practice-specific settings
        conn.execute("""
            INSERT INTO practice_appointment_types 
            (practice_id, appointment_type_id, default_duration, default_billing_code, default_notes)
            VALUES (?, ?, ?, ?, ?)
        """, (practice_id, appointment_type_id, 45, "ASSESS01", "Initial assessment notes"))
        
        settings_id = conn.lastrowid
        
        # Verify creation
        result = conn.execute("""
            SELECT practice_id, appointment_type_id, default_duration, 
                   default_billing_code, default_notes, is_enabled
            FROM practice_appointment_types WHERE id = ?
        """, (settings_id,)).fetchone()
        
        assert result['practice_id'] == practice_id
        assert result['appointment_type_id'] == appointment_type_id
        assert result['default_duration'] == 45
        assert result['default_billing_code'] == "ASSESS01"
        assert result['default_notes'] == "Initial assessment notes"
        assert result['is_enabled'] == 1
    
    def test_unique_practice_appointment_type_constraint(self, practice_appointment_types_table_setup):
        """Test unique constraint for practice_id and appointment_type_id"""
        conn = practice_appointment_types_table_setup
        
        # Set up prerequisite data
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Assessment", practice_id))
        appointment_type_id = conn.lastrowid
        
        # Create first settings entry
        conn.execute("""
            INSERT INTO practice_appointment_types (practice_id, appointment_type_id)
            VALUES (?, ?)
        """, (practice_id, appointment_type_id))
        
        # Try to create duplicate - should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO practice_appointment_types (practice_id, appointment_type_id)
                VALUES (?, ?)
            """, (practice_id, appointment_type_id))
    
    def test_practice_appointment_type_defaults(self, practice_appointment_types_table_setup):
        """Test default values for practice appointment type settings"""
        conn = practice_appointment_types_table_setup
        
        # Set up prerequisite data
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Assessment", practice_id))
        appointment_type_id = conn.lastrowid
        
        # Create minimal settings entry
        conn.execute("""
            INSERT INTO practice_appointment_types (practice_id, appointment_type_id)
            VALUES (?, ?)
        """, (practice_id, appointment_type_id))
        
        settings_id = conn.lastrowid
        
        # Check defaults
        result = conn.execute("""
            SELECT is_enabled, sort_order, created_at, updated_at
            FROM practice_appointment_types WHERE id = ?
        """, (settings_id,)).fetchone()
        
        assert result['is_enabled'] == 1
        assert result['sort_order'] == 0
        assert result['created_at'] is not None
        assert result['updated_at'] is not None
    
    def test_foreign_key_constraints(self, practice_appointment_types_table_setup):
        """Test foreign key constraint validation"""
        conn = practice_appointment_types_table_setup
        
        # Try to create settings with non-existent practice_id
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO practice_appointment_types (practice_id, appointment_type_id)
                VALUES (?, ?)
            """, (999, 1))
        
        # Create valid practice but try with non-existent appointment_type_id
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO practice_appointment_types (practice_id, appointment_type_id)
                VALUES (?, ?)
            """, (practice_id, 999))


class TestAppointmentTypeBusinessLogic:
    """Test business logic and validation rules"""
    
    def test_appointment_type_hierarchy_validation(self, appointment_types_table_setup):
        """Test business logic for appointment type hierarchy"""
        conn = appointment_types_table_setup
        
        # Insert test practice
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        # Create parent type
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Patient", practice_id))
        parent_id = conn.lastrowid
        
        # Test that we can retrieve all children of a parent
        conn.execute("""
            INSERT INTO appointment_types (name, parent_id, practice_id) 
            VALUES (?, ?, ?)
        """, ("New Assessment", parent_id, practice_id))
        
        conn.execute("""
            INSERT INTO appointment_types (name, parent_id, practice_id) 
            VALUES (?, ?, ?)
        """, ("Follow-up", parent_id, practice_id))
        
        # Get children count
        children = conn.execute("""
            SELECT COUNT(*) as count FROM appointment_types WHERE parent_id = ?
        """, (parent_id,)).fetchone()
        
        assert children['count'] == 2
    
    def test_appointment_type_deactivation(self, appointment_types_table_setup):
        """Test deactivating appointment types"""
        conn = appointment_types_table_setup
        
        # Insert test practice
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        # Create appointment type
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id) 
            VALUES (?, ?)
        """, ("Assessment", practice_id))
        appointment_type_id = conn.lastrowid
        
        # Deactivate it
        conn.execute("""
            UPDATE appointment_types SET is_active = 0 WHERE id = ?
        """, (appointment_type_id,))
        
        # Verify deactivation
        result = conn.execute("""
            SELECT is_active FROM appointment_types WHERE id = ?
        """, (appointment_type_id,)).fetchone()
        
        assert result['is_active'] == 0
        
        # Test that we can filter active types
        active_types = conn.execute("""
            SELECT COUNT(*) as count FROM appointment_types 
            WHERE practice_id = ? AND is_active = 1
        """, (practice_id,)).fetchone()
        
        assert active_types['count'] == 0
    
    def test_appointment_type_with_custom_settings(self, practice_appointment_types_table_setup):
        """Test retrieving appointment types with their custom practice settings"""
        conn = practice_appointment_types_table_setup
        
        # Set up data
        conn.execute("INSERT INTO practices (name) VALUES (?)", ("Test Practice",))
        practice_id = conn.lastrowid
        
        conn.execute("""
            INSERT INTO appointment_types (name, practice_id, duration, color) 
            VALUES (?, ?, ?, ?)
        """, ("Assessment", practice_id, 30, "#FF0000"))
        appointment_type_id = conn.lastrowid
        
        # Add custom practice settings
        conn.execute("""
            INSERT INTO practice_appointment_types 
            (practice_id, appointment_type_id, default_duration, default_billing_code)
            VALUES (?, ?, ?, ?)
        """, (practice_id, appointment_type_id, 45, "ASSESS01"))
        
        # Test joined query to get appointment type with custom settings
        result = conn.execute("""
            SELECT 
                at.name,
                at.duration as base_duration,
                at.color,
                pat.default_duration,
                pat.default_billing_code
            FROM appointment_types at
            LEFT JOIN practice_appointment_types pat ON at.id = pat.appointment_type_id
            WHERE at.id = ? AND (pat.practice_id = ? OR pat.practice_id IS NULL)
        """, (appointment_type_id, practice_id)).fetchone()
        
        assert result['name'] == "Assessment"
        assert result['base_duration'] == 30
        assert result['color'] == "#FF0000"
        assert result['default_duration'] == 45  # Custom override
        assert result['default_billing_code'] == "ASSESS01"