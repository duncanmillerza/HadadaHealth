#!/usr/bin/env python3
"""
Test script for structured template functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_templates_api():
    """Test the templates API endpoints"""
    print("🧪 Testing Structured Templates API...")
    
    try:
        # Test 1: Get all templates
        print("\n1️⃣ Testing GET /api/templates")
        response = requests.get(f"{BASE_URL}/api/templates")
        
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Found {len(templates)} templates")
            for template in templates:
                print(f"   - {template['display_name']} (ID: {template['id']})")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return
            
        if not templates:
            print("❌ No templates found - check database seeding")
            return
            
        template = templates[0]
        template_id = template['id']
        
        # Test 2: Get specific template
        print(f"\n2️⃣ Testing GET /api/templates/{template_id}")
        response = requests.get(f"{BASE_URL}/api/templates/{template_id}")
        
        if response.status_code == 200:
            template_detail = response.json()
            print(f"✅ Template details loaded: {template_detail['display_name']}")
            
            sections = template_detail['template_structure'].get('sections', [])
            print(f"   - Sections: {len(sections)}")
            for section in sections[:3]:  # Show first 3
                fields = len(section.get('fields', []))
                print(f"     • {section['title']} ({fields} fields)")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return
            
        # Test 3: Create template instance (need a patient_id)
        print(f"\n3️⃣ Testing POST /api/templates/instances")
        instance_payload = {
            "template_id": template_id,
            "patient_id": 1,  # Assuming patient ID 1 exists
            "therapist_id": "therapist_1",
            "title": "Test Template Instance"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/templates/instances",
            json=instance_payload
        )
        
        if response.status_code == 200:
            instance = response.json()
            print(f"✅ Template instance created: ID {instance['id']}")
            print(f"   - Title: {instance['title']}")
            print(f"   - Patient: {instance['patient_name']}")
            print(f"   - Status: {instance['status']}")
            
            instance_id = instance['id']
            
            # Test 4: Get template instance
            print(f"\n4️⃣ Testing GET /api/templates/instances/{instance_id}")
            response = requests.get(f"{BASE_URL}/api/templates/instances/{instance_id}")
            
            if response.status_code == 200:
                instance_detail = response.json()
                print(f"✅ Instance loaded: {instance_detail['title']}")
                
                # Show auto-populated data
                instance_data = instance_detail['instance_data']
                populated_fields = [k for k, v in instance_data.items() if v]
                print(f"   - Auto-populated fields: {populated_fields}")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
            # Test 5: Update template instance
            print(f"\n5️⃣ Testing PUT /api/templates/instances/{instance_id}")
            update_payload = {
                "instance_data": {
                    "administrative": {
                        "discharge_date": "2025-01-15",
                        "attending_physician": "Dr. Smith"
                    }
                },
                "status": "draft"
            }
            
            response = requests.put(
                f"{BASE_URL}/api/templates/instances/{instance_id}",
                json=update_payload
            )
            
            if response.status_code == 200:
                updated_instance = response.json()
                print(f"✅ Instance updated successfully")
                print(f"   - Updated at: {updated_instance['updated_at']}")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        else:
            print(f"❌ Failed to create instance: {response.status_code} - {response.text}")
            print(f"Response: {response.text}")
            
        print("\n🎉 Template API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Test error: {str(e)}")


def test_wizard_integration():
    """Test the wizard integration"""
    print("\n🔮 Testing Report Wizard Integration...")
    
    try:
        # Test that templates are available in wizard
        print("1️⃣ Testing wizard templates endpoint")
        response = requests.get(f"{BASE_URL}/api/templates?active_only=true")
        
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Wizard can access {len(templates)} templates")
            
            structured_templates = [t for t in templates if t['name'] in ['discharge_summary', 'outpatient_planning_record']]
            print(f"✅ Found {len(structured_templates)} structured templates for wizard")
            
        else:
            print(f"❌ Wizard templates failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Wizard integration test error: {str(e)}")


if __name__ == "__main__":
    print("🧪 HadadaHealth Structured Templates Test Suite")
    print("=" * 60)
    
    test_templates_api()
    test_wizard_integration()
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("\n📝 Next steps:")
    print("   1. Open the report wizard to see structured templates")
    print("   2. Create a template instance")
    print("   3. Open template editor: /template-instance/{id}/edit")
    print("   4. Test form generation, auto-population, and saving")