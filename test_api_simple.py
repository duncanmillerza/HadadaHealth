#!/usr/bin/env python3
"""
Simple test to verify appointment type API functionality
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_controller_imports():
    """Test that controllers can be imported"""
    try:
        from controllers.appointment_types import AppointmentTypeController
        print("✅ AppointmentTypeController imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import AppointmentTypeController: {e}")
        return False

def test_controller_functionality():
    """Test controller methods directly"""
    try:
        from controllers.appointment_types import AppointmentTypeController
        
        # Test index method
        result = AppointmentTypeController.index(
            hierarchical=False,
            practice_id=None,
            active_only=True,
            parent_only=False,
            include_global=True
        )
        
        print(f"✅ AppointmentTypeController.index returned {len(result)} appointment types")
        
        # Test hierarchical response
        hierarchical_result = AppointmentTypeController.index(
            hierarchical=True,
            practice_id=None,
            active_only=True,
            parent_only=False,
            include_global=True
        )
        
        print(f"✅ Hierarchical response returned {len(hierarchical_result)} parent types")
        
        # Test show method with first appointment type
        if result:
            first_type = result[0]
            single_result = AppointmentTypeController.show(appointment_type_id=first_type.id)
            print(f"✅ AppointmentTypeController.show returned: {single_result.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Controller functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_practice_controller():
    """Test practice appointment type controller"""
    try:
        from controllers.appointment_types import PracticeAppointmentTypeController
        
        # Test get_effective_types
        result = PracticeAppointmentTypeController.get_effective_types(
            practice_id=1,
            active_only=True,
            enabled_only=False  # Get all types, not just enabled ones
        )
        
        print(f"✅ PracticeAppointmentTypeController.get_effective_types returned {len(result)} types")
        
        return True
        
    except Exception as e:
        print(f"❌ Practice controller test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Appointment Type API Controllers\n")
    
    tests = [
        test_controller_imports,
        test_controller_functionality,
        test_practice_controller
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"Running {test.__name__}...")
            if test():
                passed += 1
            else:
                failed += 1
            print()  # Add spacing
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
            print()
    
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All controller tests passed! API layer is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)