#!/usr/bin/env python3
"""
Test the effective appointment types API directly
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.appointment_types import PracticeAppointmentTypeController

def test_effective_types_api():
    """Test what the effective types API actually returns"""
    print("🔍 Testing Effective Appointment Types API")
    print("=" * 50)
    
    try:
        # Test the exact same call the frontend makes
        effective_types = PracticeAppointmentTypeController.get_effective_types(
            practice_id=1,
            active_only=True,
            enabled_only=False
        )
        
        print(f"📊 API returned {len(effective_types)} effective types")
        
        # Group by parent_id to analyze structure
        categories = {}
        orphaned_types = []
        
        for et in effective_types:
            parent_id = et.parent_id
            if parent_id is None:
                # This should be a category
                categories[et.id] = {
                    'category': et,
                    'children': []
                }
            else:
                # This is a child type - find its parent
                if parent_id not in categories:
                    # Create placeholder for parent if it doesn't exist yet
                    categories[parent_id] = {
                        'category': None,
                        'children': []
                    }
                categories[parent_id]['children'].append(et)
        
        # Find and set category objects for parents
        for et in effective_types:
            if et.parent_id is None and et.id in categories:
                categories[et.id]['category'] = et
        
        print("\n📊 Effective Types Structure:")
        print("-" * 30)
        
        for cat_id, data in categories.items():
            category = data['category']
            children = data['children']
            
            if category:
                print(f"📁 {category.name} (ID: {category.id}) - {len(children)} children")
                
                if children:
                    for child in children:
                        print(f"  ├── {child.name} (ID: {child.id})")
                else:
                    print("  └── (no children)")
            else:
                print(f"📁 [Missing Category ID: {cat_id}] - {len(children)} orphaned children")
                for child in children:
                    print(f"  ├── {child.name} (ID: {child.id}) - Parent: {child.parent_id}")
            
            print()
        
        # Check what categories are missing
        print("🔍 Analysis:")
        print("-" * 10)
        
        categories_in_response = [et.id for et in effective_types if et.parent_id is None]
        child_parent_ids = set(et.parent_id for et in effective_types if et.parent_id is not None)
        
        missing_parents = child_parent_ids - set(categories_in_response)
        if missing_parents:
            print(f"⚠️  Child types reference missing parent categories: {missing_parents}")
        
        print(f"✅ Categories in response: {len(categories_in_response)}")
        print(f"✅ Total child types: {len([et for et in effective_types if et.parent_id is not None])}")
        
        return effective_types
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_effective_types_api()