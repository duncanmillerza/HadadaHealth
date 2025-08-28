#!/usr/bin/env python3
"""
Test the effective appointment types API directly
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.appointment_types import PracticeAppointmentTypeController

def test_effective_types():
    """Test the effective appointment types controller method"""
    print("🔍 Testing Effective Appointment Types API")
    
    try:
        # Test the controller method directly
        effective_types = PracticeAppointmentTypeController.get_effective_types(
            practice_id=1,
            active_only=True,
            enabled_only=False  # Same as frontend call
        )
        
        print(f"📊 Retrieved {len(effective_types)} effective types")
        
        # Group by parent_id to show structure
        categories = {}
        orphaned_types = []
        
        for et in effective_types:
            print(f"  - {et.name} (ID: {et.id}, Parent: {et.parent_id})")
            
            parent_id = et.parent_id
            if parent_id is None:
                # This should be a category
                if et.id not in categories:
                    categories[et.id] = {
                        'category': et,
                        'children': []
                    }
            else:
                # This is a child type - find its parent
                parent_found = False
                for other_et in effective_types:
                    if other_et.id == parent_id:
                        parent_found = True
                        if parent_id not in categories:
                            categories[parent_id] = {
                                'category': other_et,
                                'children': []
                            }
                        categories[parent_id]['children'].append(et)
                        break
                
                if not parent_found:
                    orphaned_types.append(et)
        
        print(f"\n📁 Categories found: {len(categories)}")
        print(f"🔗 Orphaned types (parent not in results): {len(orphaned_types)}")
        
        # Print the structure
        for cat_id, data in categories.items():
            category = data['category']
            children = data['children']
            
            print(f"\n📁 {category.name} (ID: {category.id})")
            if children:
                for child in children:
                    print(f"  ├── {child.name} (ID: {child.id})")
            else:
                print("  └── (no children)")
        
        if orphaned_types:
            print(f"\n🔗 Orphaned types:")
            for orphan in orphaned_types:
                print(f"  - {orphan.name} (ID: {orphan.id}) - Parent: {orphan.parent_id}")
        
        return effective_types
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_effective_types()