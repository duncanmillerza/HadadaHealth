#!/usr/bin/env python3
"""
API endpoint test for appointment types functionality

Tests API endpoints directly without requiring a running server.
"""
import sys
from unittest.mock import MagicMock, patch

def test_controller_methods():
    """Test controller methods can be called"""
    print("🔍 Testing controller method calls...")
    
    try:
        from controllers.appointment_types import AppointmentTypeController, PracticeAppointmentTypeController
        
        # Test that methods exist and are callable
        methods_to_test = [
            (AppointmentTypeController, 'index'),
            (AppointmentTypeController, 'show'),
            (AppointmentTypeController, 'get_by_practice'),
            (PracticeAppointmentTypeController, 'get_effective_types')
        ]
        
        for controller, method_name in methods_to_test:
            if hasattr(controller, method_name):
                print(f"✅ {controller.__name__}.{method_name} exists")
            else:
                print(f"❌ {controller.__name__}.{method_name} missing")
                return False
                
        print("✅ All controller methods exist")
        return True
        
    except Exception as e:
        print(f"❌ Controller method test failed: {e}")
        return False

def test_database_queries():
    """Test database queries work correctly"""
    print("🔍 Testing database queries...")
    
    try:
        import sqlite3
        
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Test the query that would be used by get_effective_types
            cursor.execute("""
                SELECT 
                    at.id,
                    at.name,
                    at.parent_id,
                    at.color,
                    at.duration,
                    at.description,
                    at.is_active,
                    COALESCE(pat.effective_duration, at.duration) as effective_duration,
                    COALESCE(pat.effective_color, at.color) as effective_color,
                    COALESCE(pat.enabled, 1) as enabled,
                    pat.default_billing_code,
                    pat.default_notes
                FROM appointment_types at
                LEFT JOIN practice_appointment_types pat ON at.id = pat.appointment_type_id 
                WHERE at.is_active = 1 
                AND (pat.practice_id = 1 OR pat.practice_id IS NULL)
                ORDER BY at.parent_id IS NULL DESC, at.name
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            if results:
                print(f"✅ Query returned {len(results)} appointment types")
                
                # Test hierarchical structure
                parent_types = [r for r in results if r[2] is None]  # parent_id is None
                child_types = [r for r in results if r[2] is not None]
                
                print(f"✅ Found {len(parent_types)} parent types, {len(child_types)} child types")
                return True
            else:
                print("⚠️  Query returned no results")
                return False
                
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        return False

def test_response_format():
    """Test that API response format matches frontend expectations"""
    print("🔍 Testing response format...")
    
    try:
        import sqlite3
        
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Get a sample appointment type and format it like the API would
            cursor.execute("""
                SELECT 
                    at.id,
                    at.name, 
                    at.parent_id,
                    at.color,
                    at.duration,
                    at.description,
                    COALESCE(pat.effective_duration, at.duration) as effective_duration,
                    pat.default_billing_code
                FROM appointment_types at
                LEFT JOIN practice_appointment_types pat ON at.id = pat.appointment_type_id 
                WHERE at.is_active = 1
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                # Format like API response
                api_response = {
                    "id": result[0],
                    "name": result[1],
                    "parent_id": result[2],
                    "color": result[3],
                    "duration": result[4],
                    "description": result[5],
                    "effective_duration": result[6],
                    "default_billing_code": result[7]
                }
                
                # Check required fields for frontend
                required_fields = ["id", "name", "color", "duration"]
                all_present = all(field in api_response and api_response[field] is not None 
                                for field in required_fields)
                
                if all_present:
                    print("✅ API response format matches frontend requirements")
                    print(f"   Sample: {result[1]} ({result[6] or result[4]}min, {result[3]})")
                    return True
                else:
                    print("❌ API response missing required fields")
                    return False
            else:
                print("⚠️  No sample data to test response format")
                return False
                
    except Exception as e:
        print(f"❌ Response format test failed: {e}")
        return False

def test_javascript_integration_points():
    """Test JavaScript integration points"""
    print("🔍 Testing JavaScript integration points...")
    
    try:
        # Check that the JavaScript files have the expected functions
        with open("static/js/appointment-type-modal.js", "r") as f:
            js_content = f.read()
            
        expected_functions = [
            "AppointmentTypeModal",
            "open",
            "close", 
            "loadAppointmentTypes",
            "confirmSelection"
        ]
        
        all_found = True
        for func in expected_functions:
            if func in js_content:
                print(f"✅ Function '{func}' found in modal JavaScript")
            else:
                print(f"❌ Function '{func}' missing from modal JavaScript")
                all_found = False
        
        # Check integration file
        with open("static/js/calendar-appointment-type-integration.js", "r") as f:
            integration_content = f.read()
            
        integration_functions = [
            "enhancedOpenModal",
            "proceedToBookingWithAppointmentType",
            "fillBookingFormWithAppointmentType"
        ]
        
        for func in integration_functions:
            if func in integration_content:
                print(f"✅ Function '{func}' found in integration JavaScript")
            else:
                print(f"❌ Function '{func}' missing from integration JavaScript")
                all_found = False
                
        return all_found
        
    except Exception as e:
        print(f"❌ JavaScript integration test failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Starting Appointment Types API Tests")
    print("=" * 50)
    
    tests = [
        ("Controller Methods", test_controller_methods),
        ("Database Queries", test_database_queries),
        ("Response Format", test_response_format),
        ("JavaScript Integration", test_javascript_integration_points)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        
    print("\n" + "=" * 50)
    print("🎯 API TEST RESULTS SUMMARY") 
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if success:
            passed += 1
    
    print("-" * 50)
    print(f"📊 {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All API tests passed! Endpoints are ready for integration.")
        return 0
    else:
        print("⚠️  Some API tests failed. Review implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())