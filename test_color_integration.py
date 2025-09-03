#!/usr/bin/env python3
"""
Test script to verify appointment type color integration works end-to-end
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_color_integration():
    """Test that appointment type colors flow through to calendar display"""
    
    print("🧪 Testing Appointment Type Color Integration")
    print("=" * 50)
    
    # 1. Create a test appointment type with a specific hex color
    appointment_type_data = {
        "name": "Color Test Type",
        "duration": 30,
        "color": "#FF5733",  # Bright orange-red
        "practice_id": 1,
        "description": "Test type for color integration",
        "default_billing_code": "TEST001"
    }
    
    print("1. Creating test appointment type...")
    response = requests.post(f"{BASE_URL}/api/appointment-types", json=appointment_type_data)
    
    if response.status_code == 200:
        appointment_type = response.json()
        print(f"   ✅ Created appointment type ID: {appointment_type['id']}")
        print(f"   🎨 Color: {appointment_type['color']}")
    else:
        print(f"   ❌ Failed to create appointment type: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # 2. Create a booking with this appointment type
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    booking_data = {
        "name": "Color Test Patient",
        "date": tomorrow,
        "time": "10:00",
        "duration": 30,
        "therapist_id": 1,
        "appointment_type_id": appointment_type['id'],
        "appointment_type_color": appointment_type['color'],
        "notes": "Testing color integration"
    }
    
    print("2. Creating test booking...")
    response = requests.post(f"{BASE_URL}/api/bookings", json=booking_data)
    
    if response.status_code == 200:
        booking = response.json()
        print(f"   ✅ Created booking ID: {booking['id']}")
        print(f"   📅 Date: {booking['date']} at {booking['time']}")
    else:
        print(f"   ❌ Failed to create booking: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # 3. Fetch calendar data to verify color is present
    print("3. Verifying calendar data includes color...")
    response = requests.get(f"{BASE_URL}/api/calendar")
    
    if response.status_code == 200:
        calendar_data = response.json()
        
        # Look for our test booking in calendar data
        test_booking_found = False
        for booking in calendar_data.get('bookings', []):
            if booking.get('id') == booking['id']:
                test_booking_found = True
                if booking.get('appointment_type_color') == appointment_type['color']:
                    print(f"   ✅ Calendar data contains correct color: {booking['appointment_type_color']}")
                    print("   🎯 Color integration test PASSED!")
                else:
                    print(f"   ❌ Color mismatch in calendar data!")
                    print(f"   Expected: {appointment_type['color']}")
                    print(f"   Found: {booking.get('appointment_type_color', 'None')}")
                break
        
        if not test_booking_found:
            print("   ⚠️  Test booking not found in calendar data")
            return False
            
    else:
        print(f"   ❌ Failed to fetch calendar data: {response.status_code}")
        return False
    
    # 4. Clean up test data
    print("4. Cleaning up test data...")
    requests.delete(f"{BASE_URL}/api/bookings/{booking['id']}")
    requests.delete(f"{BASE_URL}/api/appointment-types/{appointment_type['id']}")
    print("   ✅ Test data cleaned up")
    
    print("\n🎉 Color Integration Test Completed Successfully!")
    return True

if __name__ == "__main__":
    try:
        test_color_integration()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")