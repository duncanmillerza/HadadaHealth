#!/usr/bin/env python3
"""
Simple Template Test - Using curl instead of requests
"""
import os
import subprocess

def run_curl(url):
    """Run curl command and return status code"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
            capture_output=True, text=True, timeout=10
        )
        return int(result.stdout.strip())
    except:
        return 0

def test_files_exist():
    """Test if template files exist on filesystem"""
    files = [
        "/Users/duncanmiller/Documents/HadadaHealth/static/css/template_customization.css",
        "/Users/duncanmiller/Documents/HadadaHealth/static/js/template_customization.js",
        "/Users/duncanmiller/Documents/HadadaHealth/static/fragments/template_customization_modal.html"
    ]
    
    print("📁 File Existence Test:")
    all_exist = True
    for file_path in files:
        exists = os.path.exists(file_path)
        all_exist = all_exist and exists
        status = "✅" if exists else "❌"
        print(f"   {status} {os.path.basename(file_path)}")
    
    return all_exist

def test_server_endpoints():
    """Test if server endpoints are accessible"""
    endpoints = [
        "http://localhost:8000/",
        "http://localhost:8000/static/css/template_customization.css",
        "http://localhost:8000/static/js/template_customization.js",
        "http://localhost:8000/static/fragments/template_customization_modal.html"
    ]
    
    print("\n🌐 Server Endpoint Test:")
    all_ok = True
    for endpoint in endpoints:
        status_code = run_curl(endpoint)
        is_ok = status_code == 200
        all_ok = all_ok and is_ok
        status = "✅" if is_ok else "❌"
        name = endpoint.split("/")[-1] if "/" in endpoint else "Dashboard"
        print(f"   {status} {name}: {status_code}")
    
    return all_ok

def test_dashboard_content():
    """Test if dashboard contains template-related content"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:8000/'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            print("\n❌ Could not fetch dashboard content")
            return False
            
        content = result.stdout
        
        # Check for various template-related elements
        checks = {
            "openTemplateCustomization function": "openTemplateCustomization" in content,
            "template-admin-btn element": "template-admin-btn" in content,
            "Templates text": "Templates" in content,
            "template_customization.js": "template_customization.js" in content,
            "template_customization.css": "template_customization.css" in content
        }
        
        print("\n🔍 Dashboard Content Test:")
        all_found = True
        for check_name, found in checks.items():
            all_found = all_found and found
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}")
        
        return all_found
        
    except Exception as e:
        print(f"\n❌ Dashboard content test failed: {e}")
        return False

def main():
    print("🧪 Simple Template Integration Test")
    print("=" * 40)
    
    # Run tests
    files_ok = test_files_exist()
    server_ok = test_server_endpoints()
    content_ok = test_dashboard_content()
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   {'✅' if files_ok else '❌'} Files exist: {files_ok}")
    print(f"   {'✅' if server_ok else '❌'} Server endpoints: {server_ok}")
    print(f"   {'✅' if content_ok else '❌'} Dashboard content: {content_ok}")
    
    overall = files_ok and server_ok and content_ok
    print(f"\n🎯 OVERALL: {'✅ READY' if overall else '❌ NEEDS ATTENTION'}")
    
    if overall:
        print("\n🎉 Template system is ready!")
        print("   Visit http://localhost:8000 and look for Templates button")
        print("   Or try the floating test button in bottom-right corner")
    else:
        print("\n🔧 Some components need attention")

if __name__ == "__main__":
    main()