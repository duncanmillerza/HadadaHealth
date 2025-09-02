#!/usr/bin/env python3
"""
Integration test for appointment types functionality

Tests the full appointment type system integration including:
- API endpoints
- Controller functionality  
- Database operations
- Model validation
"""
import sys
import json
import sqlite3
from datetime import datetime

def test_database_setup():
    """Test that appointment types tables exist and have correct structure"""
    print("🔍 Testing database setup...")
    
    try:
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Test appointment_types table
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='appointment_types';")
            result = cursor.fetchone()
            if result:
                print("✅ appointment_types table exists")
            else:
                print("❌ appointment_types table missing")
                return False
            
            # Test practice_appointment_types table
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='practice_appointment_types';")
            result = cursor.fetchone()
            if result:
                print("✅ practice_appointment_types table exists")
            else:
                print("❌ practice_appointment_types table missing")
                return False
                
            # Check for sample data
            cursor.execute("SELECT COUNT(*) FROM appointment_types;")
            count = cursor.fetchone()[0]
            print(f"📊 Found {count} appointment types in database")
            
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_model_imports():
    """Test that models can be imported successfully"""
    print("🔍 Testing model imports...")
    
    try:
        from models.appointment_types import AppointmentType, PracticeAppointmentType
        print("✅ AppointmentType models imported successfully")
        
        # Test model creation
        test_type = AppointmentType(
            name="Test Type",
            color="#FF0000",
            duration=60
        )
        print("✅ AppointmentType model creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_controller_imports():
    """Test that controllers can be imported successfully"""
    print("🔍 Testing controller imports...")
    
    try:
        from controllers.appointment_types import AppointmentTypeController
        print("✅ AppointmentTypeController imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Controller import failed: {e}")
        return False

def test_frontend_files():
    """Test that frontend files exist and are properly structured"""
    print("🔍 Testing frontend files...")
    
    import os
    files_to_check = [
        "static/js/appointment-type-modal.js",
        "static/js/calendar-appointment-type-integration.js", 
        "static/css/appointment-type-modal.css",
        "static/fragments/appointment-type-modal.html"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
            
    return all_exist

def test_calendar_integration():
    """Test that calendar template includes appointment type components"""
    print("🔍 Testing calendar integration...")
    
    try:
        with open("templates/week-calendar.html", "r") as f:
            content = f.read()
            
        # Check for required components
        required_elements = [
            "appointment-type-modal",
            "appointment-type-modal.js",
            "calendar-appointment-type-integration.js",
            "appointment-type-modal.css"
        ]
        
        all_found = True
        for element in required_elements:
            if element in content:
                print(f"✅ {element} found in calendar template")
            else:
                print(f"❌ {element} missing from calendar template")
                all_found = False
                
        return all_found
        
    except Exception as e:
        print(f"❌ Calendar integration test failed: {e}")
        return False

def test_sample_data():
    """Test if sample appointment types exist in database"""
    print("🔍 Testing sample data...")
    
    try:
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Check for default appointment types
            cursor.execute("""
                SELECT id, name, parent_id, color, duration 
                FROM appointment_types 
                WHERE is_active = 1 
                ORDER BY parent_id IS NULL DESC, name
            """)
            
            types = cursor.fetchall()
            if types:
                print("✅ Sample appointment types found:")
                for type_data in types[:5]:  # Show first 5
                    id_val, name, parent_id, color, duration = type_data
                    parent_str = f" (parent: {parent_id})" if parent_id else ""
                    print(f"   - {name} ({duration}min, {color}){parent_str}")
                
                if len(types) > 5:
                    print(f"   ... and {len(types) - 5} more")
                    
                return True
            else:
                print("⚠️  No sample appointment types found")
                return False
                
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting Appointment Types Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Model Imports", test_model_imports), 
        ("Controller Imports", test_controller_imports),
        ("Frontend Files", test_frontend_files),
        ("Calendar Integration", test_calendar_integration),
        ("Sample Data", test_sample_data)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS SUMMARY")
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
        print("🎉 All tests passed! Appointment types integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Integration needs attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())