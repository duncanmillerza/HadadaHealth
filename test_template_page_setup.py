#!/usr/bin/env python3
"""
Test script to verify the Template Management Page setup
"""
import os

def test_files_exist():
    """Test if all required files exist"""
    files = [
        "/Users/duncanmiller/Documents/HadadaHealth/templates/template_management.html",
        "/Users/duncanmiller/Documents/HadadaHealth/static/css/template_customization.css", 
        "/Users/duncanmiller/Documents/HadadaHealth/static/js/template_customization.js",
        "/Users/duncanmiller/Documents/HadadaHealth/static/fragments/template_customization_modal.html"
    ]
    
    print("📁 Template Management Files Check:")
    all_exist = True
    for file_path in files:
        exists = os.path.exists(file_path)
        all_exist = all_exist and exists
        status = "✅" if exists else "❌"
        print(f"   {status} {os.path.basename(file_path)}")
    
    return all_exist

def test_route_added():
    """Test if route was added to main.py"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/main.py", "r") as f:
            content = f.read()
        
        has_route = '@app.get("/templates")' in content
        has_function = 'def serve_template_management(' in content
        has_template_response = 'template_management.html' in content
        
        print("\n🛤️  Route Configuration Check:")
        print(f"   {'✅' if has_route else '❌'} Route decorator added")
        print(f"   {'✅' if has_function else '❌'} Route function added")  
        print(f"   {'✅' if has_template_response else '❌'} Template file referenced")
        
        return has_route and has_function and has_template_response
        
    except Exception as e:
        print(f"\n❌ Error checking main.py: {e}")
        return False

def test_navigation_updated():
    """Test if navigation was updated"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/static/fragments/nav.html", "r") as f:
            content = f.read()
        
        has_templates_link = 'href="/templates"' in content
        has_templates_text = 'Templates' in content and 'fa-file-alt' in content
        has_icon = 'fa-file-alt' in content
        
        print("\n🧭 Navigation Update Check:")
        print(f"   {'✅' if has_templates_link else '❌'} Templates link added")
        print(f"   {'✅' if has_templates_text else '❌'} Templates text added")
        print(f"   {'✅' if has_icon else '❌'} Templates icon added")
        
        return has_templates_link and has_templates_text
        
    except Exception as e:
        print(f"\n❌ Error checking navigation: {e}")
        return False

def test_dashboard_cleanup():
    """Test if dashboard was cleaned up"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/templates/index.html", "r") as f:
            content = f.read()
        
        # These should NOT be in the file anymore
        no_template_button = 'template-admin-btn' not in content
        no_template_function = 'openTemplateCustomization' not in content
        no_template_scripts = 'template_customization.js' not in content
        no_modal_container = 'template-customization-modal-container' not in content
        
        print("\n🧹 Dashboard Cleanup Check:")
        print(f"   {'✅' if no_template_button else '❌'} Template button removed")
        print(f"   {'✅' if no_template_function else '❌'} Template functions removed") 
        print(f"   {'✅' if no_template_scripts else '❌'} Template scripts removed")
        print(f"   {'✅' if no_modal_container else '❌'} Modal container removed")
        
        return all([no_template_button, no_template_function, no_template_scripts, no_modal_container])
        
    except Exception as e:
        print(f"\n❌ Error checking dashboard: {e}")
        return False

def test_widget_cleanup():
    """Test if dashboard widget was cleaned up"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/static/js/dashboard-widgets.js", "r") as f:
            content = f.read()
        
        # Template button should not be in widgets
        no_template_widget = 'template-btn' not in content and 'Templates' not in content
        
        print("\n🔧 Widget Cleanup Check:")
        print(f"   {'✅' if no_template_widget else '❌'} Template widget removed")
        
        return no_template_widget
        
    except Exception as e:
        print(f"\n❌ Error checking widgets: {e}")
        return False

def main():
    print("🧪 Template Management Page Setup Verification")
    print("=" * 50)
    
    # Run all tests
    files_ok = test_files_exist()
    route_ok = test_route_added()
    nav_ok = test_navigation_updated()
    dashboard_ok = test_dashboard_cleanup()
    widget_ok = test_widget_cleanup()
    
    # Summary
    print(f"\n📊 SETUP VERIFICATION SUMMARY:")
    print("=" * 35)
    print(f"   {'✅' if files_ok else '❌'} Template files exist: {files_ok}")
    print(f"   {'✅' if route_ok else '❌'} Route configured: {route_ok}")
    print(f"   {'✅' if nav_ok else '❌'} Navigation updated: {nav_ok}")
    print(f"   {'✅' if dashboard_ok else '❌'} Dashboard cleaned: {dashboard_ok}")
    print(f"   {'✅' if widget_ok else '❌'} Widget cleaned: {widget_ok}")
    
    overall = all([files_ok, route_ok, nav_ok, dashboard_ok, widget_ok])
    print(f"\n🎯 OVERALL STATUS: {'✅ READY FOR RESTART' if overall else '❌ NEEDS FIXES'}")
    
    if overall:
        print("\n🎉 Template Management Page setup is complete!")
        print("   Next steps:")
        print("   1. Restart the server: python main.py")
        print("   2. Visit http://localhost:8000")
        print("   3. Click Admin → Templates in the navigation")
        print("   4. Enjoy the dedicated Template Management page!")
    else:
        print("\n🔧 Some setup steps need attention before testing")

if __name__ == "__main__":
    main()