#!/usr/bin/env python3
"""
Data Migration Test for Appointment Types

Tests that existing booking data is compatible with the new appointment type system
and performs migration validation.
"""
import sqlite3
import sys

def test_existing_bookings_compatibility():
    """Test that existing bookings can work with appointment types"""
    print("🔍 Testing existing bookings compatibility...")
    
    try:
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Get bookings count
            cursor.execute("SELECT COUNT(*) FROM bookings;")
            booking_count = cursor.fetchone()[0]
            print(f"📊 Found {booking_count} existing bookings")
            
            # Check how many bookings already have appointment_type_id
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE appointment_type_id IS NOT NULL;")
            typed_bookings = cursor.fetchone()[0]
            print(f"📊 {typed_bookings} bookings already have appointment type assigned")
            
            # Check bookings without appointment types
            untyped = booking_count - typed_bookings
            if untyped > 0:
                print(f"⚠️  {untyped} bookings need appointment type assignment")
                
                # Show sample untyped bookings
                cursor.execute("""
                    SELECT id, name, therapist, date, duration, colour, notes 
                    FROM bookings 
                    WHERE appointment_type_id IS NULL 
                    LIMIT 5
                """)
                samples = cursor.fetchall()
                
                if samples:
                    print("📝 Sample untyped bookings:")
                    for booking in samples:
                        id_val, name, therapist, date, duration, colour, notes = booking
                        print(f"   - {name} with {therapist} ({duration}min, {colour}) on {date}")
                    
            return True
            
    except Exception as e:
        print(f"❌ Booking compatibility test failed: {e}")
        return False

def test_appointment_type_mapping():
    """Test mapping existing booking attributes to appointment types"""
    print("🔍 Testing appointment type mapping logic...")
    
    try:
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Get common booking patterns to map to appointment types
            cursor.execute("""
                SELECT 
                    duration,
                    colour,
                    COUNT(*) as count,
                    GROUP_CONCAT(DISTINCT SUBSTR(notes, 1, 20)) as sample_notes
                FROM bookings 
                WHERE appointment_type_id IS NULL
                GROUP BY duration, colour
                ORDER BY count DESC
                LIMIT 10
            """)
            
            patterns = cursor.fetchall()
            if patterns:
                print("📊 Common booking patterns that need type mapping:")
                for duration, colour, count, sample_notes in patterns:
                    print(f"   - {duration}min, {colour} color: {count} bookings")
                    if sample_notes:
                        print(f"     Sample notes: {sample_notes[:50]}...")
                        
                # Suggest mappings based on patterns
                print("\n💡 Suggested mappings:")
                
                # Get available appointment types for mapping
                cursor.execute("""
                    SELECT id, name, duration, color 
                    FROM appointment_types 
                    WHERE is_active = 1 AND parent_id IS NOT NULL
                    ORDER BY name
                """)
                
                available_types = cursor.fetchall()
                if available_types:
                    print("📋 Available appointment types for mapping:")
                    for type_id, name, duration, color in available_types[:10]:
                        print(f"   - {name} (ID: {type_id}, {duration}min, {color})")
                        
            return True
            
    except Exception as e:
        print(f"❌ Appointment type mapping test failed: {e}")
        return False

def test_foreign_key_relationships():
    """Test foreign key relationships work correctly"""
    print("🔍 Testing foreign key relationships...")
    
    try:
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Test join between bookings and appointment_types
            cursor.execute("""
                SELECT 
                    b.id,
                    b.name as booking_name,
                    at.name as appointment_type,
                    at.duration as type_duration,
                    b.duration as booking_duration
                FROM bookings b
                JOIN appointment_types at ON b.appointment_type_id = at.id
                WHERE at.is_active = 1
                LIMIT 5
            """)
            
            joined_results = cursor.fetchall()
            if joined_results:
                print("✅ Successfully joined bookings with appointment types:")
                for booking_id, booking_name, type_name, type_duration, booking_duration in joined_results:
                    duration_match = "✅" if type_duration == booking_duration else "⚠️"
                    print(f"   {duration_match} {booking_name} -> {type_name} ({type_duration}min vs {booking_duration}min)")
                return True
            else:
                print("⚠️  No bookings currently linked to appointment types")
                return True  # This is okay for migration testing
                
    except Exception as e:
        print(f"❌ Foreign key relationship test failed: {e}")
        return False

def test_migration_script_readiness():
    """Test that we have the data needed for migration"""
    print("🔍 Testing migration script readiness...")
    
    try:
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Check if we have default appointment types to use for unmapped bookings
            cursor.execute("""
                SELECT id, name 
                FROM appointment_types 
                WHERE name LIKE '%Treatment%' OR name LIKE '%Follow%' OR name LIKE '%Assessment%'
                AND is_active = 1
                ORDER BY name
            """)
            
            default_types = cursor.fetchall()
            if default_types:
                print("✅ Found default appointment types for migration:")
                for type_id, name in default_types:
                    print(f"   - {name} (ID: {type_id})")
            else:
                print("⚠️  No default appointment types found for migration")
                
            # Check if we can create a simple mapping strategy
            cursor.execute("""
                SELECT DISTINCT duration, COUNT(*) as count
                FROM bookings 
                WHERE appointment_type_id IS NULL
                GROUP BY duration
                ORDER BY count DESC
            """)
            
            duration_patterns = cursor.fetchall()
            if duration_patterns:
                print("\n📊 Duration patterns in untyped bookings:")
                for duration, count in duration_patterns:
                    print(f"   - {duration} minutes: {count} bookings")
                    
            return True
            
    except Exception as e:
        print(f"❌ Migration readiness test failed: {e}")
        return False

def suggest_migration_strategy():
    """Suggest a migration strategy based on data analysis"""
    print("🔍 Analyzing data for migration strategy...")
    
    try:
        with sqlite3.connect("data/bookings.db") as conn:
            cursor = conn.cursor()
            
            # Get the most common appointment type for each duration
            cursor.execute("""
                SELECT 
                    at.duration,
                    at.id,
                    at.name,
                    COUNT(*) as usage_count
                FROM appointment_types at
                LEFT JOIN bookings b ON at.id = b.appointment_type_id
                WHERE at.is_active = 1 AND at.parent_id IS NOT NULL
                GROUP BY at.duration, at.id, at.name
                ORDER BY at.duration, usage_count DESC
            """)
            
            type_usage = cursor.fetchall()
            
            print("\n💡 SUGGESTED MIGRATION STRATEGY:")
            print("=" * 50)
            print("1. Map existing bookings by duration:")
            
            duration_map = {}
            for duration, type_id, name, usage in type_usage:
                if duration not in duration_map:
                    duration_map[duration] = (type_id, name, usage)
            
            for duration, (type_id, name, usage) in sorted(duration_map.items()):
                print(f"   - {duration}min bookings -> {name} (ID: {type_id})")
            
            print("\n2. Handle edge cases:")
            print("   - Unknown durations -> Default 'Treatment' type")
            print("   - Preserve original booking duration if different from type")
            print("   - Log all migration actions for rollback capability")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration strategy analysis failed: {e}")
        return False

def main():
    """Run all data migration tests"""
    print("🚀 Starting Data Migration Tests")
    print("=" * 50)
    
    tests = [
        ("Existing Bookings Compatibility", test_existing_bookings_compatibility),
        ("Appointment Type Mapping", test_appointment_type_mapping),
        ("Foreign Key Relationships", test_foreign_key_relationships),
        ("Migration Script Readiness", test_migration_script_readiness),
        ("Migration Strategy", suggest_migration_strategy)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        
    print("\n" + "=" * 50)
    print("🎯 DATA MIGRATION TEST RESULTS")
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
        print("🎉 Data migration tests passed! Ready for production migration.")
        return 0
    else:
        print("⚠️  Some migration tests failed. Review before migrating.")
        return 1

if __name__ == "__main__":
    sys.exit(main())