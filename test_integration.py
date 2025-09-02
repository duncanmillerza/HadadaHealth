#!/usr/bin/env python3
"""
Integration test script to verify AppointmentType models work correctly with the database

Tests the complete functionality of the appointment types system.
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.appointment_types import AppointmentType, PracticeAppointmentType


def test_appointment_type_creation():
    """Test creating appointment types"""
    print("🧪 Testing AppointmentType creation...")
    
    try:
        # Test creating a practice-specific appointment type with unique name
        import time
        unique_name = f"Test Assessment {int(time.time())}"
        test_type = AppointmentType.create(
            name=unique_name,
            practice_id=1,
            color="#FF0000",
            duration=45,
            description="Test appointment type"
        )
        
        assert test_type.id is not None
        assert test_type.name == unique_name
        assert test_type.practice_id == 1
        assert test_type.color == "#FF0000"
        assert test_type.duration == 45
        
        print("✅ AppointmentType creation successful")
        return True
        
    except Exception as e:
        print(f"❌ AppointmentType creation failed: {e}")
        return False


def test_hierarchical_relationships():
    """Test parent-child relationships"""
    print("🧪 Testing hierarchical relationships...")
    
    try:
        # Get a parent type
        patient_type = AppointmentType.get_by_practice(practice_id=None)[0]  # Get first global type
        
        # Create a child type with unique name
        import time
        unique_name = f"Test Child Type {int(time.time())}"
        child_type = AppointmentType.create(
            name=unique_name,
            parent_id=patient_type.id,
            practice_id=1,
            description="Child appointment type"
        )
        
        # Test parent-child relationship
        parent = child_type.get_parent()
        assert parent is not None
        assert parent.id == patient_type.id
        
        children = parent.get_children()
        child_ids = [c.id for c in children]
        assert child_type.id in child_ids
        
        # Test full path
        path = child_type.get_full_path()
        assert parent.name in path
        assert child_type.name in path
        
        print("✅ Hierarchical relationships working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Hierarchical relationships test failed: {e}")
        return False


def test_practice_customizations():
    """Test practice-specific customizations"""
    print("🧪 Testing practice customizations...")
    
    try:
        # Get an appointment type - use one that likely doesn't have customizations yet
        appointment_types = AppointmentType.get_by_practice(practice_id=None)
        if not appointment_types:
            print("❌ No appointment types found for testing")
            return False
            
        # Find an appointment type without existing customization
        appointment_type = None
        for at in appointment_types:
            existing = PracticeAppointmentType.get_for_practice_and_type(1, at.id)
            if existing is None:
                appointment_type = at
                break
        
        if appointment_type is None:
            print("❌ No available appointment type for customization testing")
            return False
        
        # Create practice customization
        customization = PracticeAppointmentType.create(
            practice_id=1,
            appointment_type_id=appointment_type.id,
            default_duration=60,
            default_billing_code="TEST01",
            default_notes="Test customization notes",
            sort_order=1
        )
        
        assert customization.id is not None
        assert customization.practice_id == 1
        assert customization.appointment_type_id == appointment_type.id
        assert customization.default_duration == 60
        assert customization.default_billing_code == "TEST01"
        
        # Test effective duration
        effective_duration = customization.get_effective_duration()
        assert effective_duration == 60  # Should use custom duration
        
        # Test getting appointment type
        linked_type = customization.get_appointment_type()
        assert linked_type is not None
        assert linked_type.id == appointment_type.id
        
        print("✅ Practice customizations working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Practice customizations test failed: {e}")
        return False


def test_queries_and_filtering():
    """Test various query and filtering operations"""
    print("🧪 Testing queries and filtering...")
    
    try:
        # Test getting by practice
        global_types = AppointmentType.get_by_practice(practice_id=None, include_global=True)
        assert len(global_types) > 0
        
        # Test hierarchical structure
        hierarchy = AppointmentType.get_hierarchical(practice_id=None)
        assert len(hierarchy) > 0
        
        # Verify hierarchy has expected structure
        for parent_id, data in hierarchy.items():
            parent_type = data['appointment_type']
            assert parent_type.parent_id is None  # Should be root level
            
            # Check if has children
            children = data['children']
            for child_id, child_data in children.items():
                child_type = child_data['appointment_type']
                assert child_type.parent_id == parent_id
        
        print("✅ Queries and filtering working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Queries and filtering test failed: {e}")
        return False


def test_validation_rules():
    """Test validation rules"""
    print("🧪 Testing validation rules...")
    
    try:
        import time
        timestamp = int(time.time())
        
        # Test invalid color format
        try:
            AppointmentType.create(
                name=f"Invalid Color Test {timestamp}",
                color="invalid-color",
                practice_id=1
            )
            assert False, "Should have raised validation error for invalid color"
        except ValueError:
            pass  # Expected
        
        # Test duplicate name validation
        try:
            unique_name = f"Duplicate Test {timestamp}"
            
            # Create first type
            AppointmentType.create(
                name=unique_name,
                practice_id=1
            )
            
            # Try to create duplicate
            AppointmentType.create(
                name=unique_name, 
                practice_id=1
            )
            assert False, "Should have raised validation error for duplicate name"
        except ValueError:
            pass  # Expected
        
        print("✅ Validation rules working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Validation rules test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("🚀 Starting AppointmentType integration tests...\n")
    
    tests = [
        test_appointment_type_creation,
        test_hierarchical_relationships,
        test_practice_customizations, 
        test_queries_and_filtering,
        test_validation_rules
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! AppointmentType models are working correctly.")
        return True
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)