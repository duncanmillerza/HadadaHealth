#!/usr/bin/env python3
"""
Quick test script for Template Customization Integration
Tests the complete integration from dashboard to modal loading.
"""
import subprocess
import time
import requests
import os

def test_server_running():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_modal_endpoint():
    """Test if the modal HTML endpoint is accessible"""
    try:
        response = requests.get("http://localhost:8000/static/fragments/template_customization_modal.html", timeout=5)
        if response.status_code == 200:
            print("✅ Modal HTML endpoint working")
            print(f"   Response length: {len(response.text)} characters")
            return True
        else:
            print(f"❌ Modal HTML endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Modal HTML endpoint error: {e}")
        return False

def test_static_files():
    """Test if static files are accessible"""
    files_to_test = [
        "/static/css/template_customization.css",
        "/static/js/template_customization.js"
    ]
    
    results = {}
    for file_path in files_to_test:
        try:
            response = requests.get(f"http://localhost:8000{file_path}", timeout=5)
            status = response.status_code == 200
            results[file_path] = status
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {file_path}: {response.status_code}")
        except Exception as e:
            results[file_path] = False
            print(f"❌ {file_path}: Error - {e}")
    
    return all(results.values())

def test_dashboard_page():
    """Test if dashboard page loads and contains template button"""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            content = response.text
            has_template_button = 'id="template-admin-btn"' in content
            has_template_function = 'openTemplateCustomization' in content
            
            print(f"✅ Dashboard loads: {response.status_code}")
            print(f"{'✅' if has_template_button else '❌'} Template button present: {has_template_button}")
            print(f"{'✅' if has_template_function else '❌'} Template function present: {has_template_function}")
            
            return has_template_button and has_template_function
        else:
            print(f"❌ Dashboard failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return False

def test_file_existence():
    """Test if all required files exist"""
    files_to_check = [
        "/Users/duncanmiller/Documents/HadadaHealth/static/css/template_customization.css",
        "/Users/duncanmiller/Documents/HadadaHealth/static/js/template_customization.js",
        "/Users/duncanmiller/Documents/HadadaHealth/static/fragments/template_customization_modal.html"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        all_exist = all_exist and exists
        status_icon = "✅" if exists else "❌"
        print(f"{status_icon} {os.path.basename(file_path)}: {'EXISTS' if exists else 'MISSING'}")
    
    return all_exist

def main():
    print("🧪 Testing Template Customization Integration")
    print("=" * 50)
    
    # Test 1: File existence
    print("\n📁 Testing File Existence:")
    files_ok = test_file_existence()
    
    # Test 2: Server running
    print(f"\n🚀 Testing Server Status:")
    if test_server_running():
        print("✅ Server is running")
        
        # Test 3: Static files
        print(f"\n📄 Testing Static Files:")
        static_ok = test_static_files()
        
        # Test 4: Modal endpoint
        print(f"\n🔗 Testing Modal Endpoint:")
        modal_ok = test_modal_endpoint()
        
        # Test 5: Dashboard integration
        print(f"\n🏠 Testing Dashboard Integration:")
        dashboard_ok = test_dashboard_page()
        
        # Summary
        print(f"\n📊 INTEGRATION TEST SUMMARY:")
        print("=" * 30)
        print(f"{'✅' if files_ok else '❌'} Required files exist: {files_ok}")
        print(f"{'✅' if static_ok else '❌'} Static files accessible: {static_ok}")
        print(f"{'✅' if modal_ok else '❌'} Modal endpoint working: {modal_ok}")
        print(f"{'✅' if dashboard_ok else '❌'} Dashboard integration: {dashboard_ok}")
        
        overall_status = all([files_ok, static_ok, modal_ok, dashboard_ok])
        print(f"\n🎯 OVERALL STATUS: {'✅ READY FOR TESTING' if overall_status else '❌ NEEDS FIXES'}")
        
        if overall_status:
            print(f"\n🎉 Template Customization is ready to test!")
            print(f"   1. Visit http://localhost:8000 in your browser")
            print(f"   2. Look for the orange 'Templates' button in the AI Reports section")
            print(f"   3. Click it to open the template customization interface")
        
    else:
        print("❌ Server is not running")
        print("   Start the server with: python main.py")

if __name__ == "__main__":
    main()