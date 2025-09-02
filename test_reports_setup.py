#!/usr/bin/env python3
"""
Test script to verify the AI Reports and Template Management pages setup
"""
import os

def test_files_exist():
    """Test if all required files exist"""
    files = [
        "/Users/duncanmiller/Documents/HadadaHealth/templates/ai_reports.html",
        "/Users/duncanmiller/Documents/HadadaHealth/templates/template_management.html",
    ]
    
    print("📁 Reports Pages Files Check:")
    all_exist = True
    for file_path in files:
        exists = os.path.exists(file_path)
        all_exist = all_exist and exists
        status = "✅" if exists else "❌"
        print(f"   {status} {os.path.basename(file_path)}")
    
    return all_exist

def test_routes_added():
    """Test if routes were added to main.py"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/main.py", "r") as f:
            content = f.read()
        
        has_ai_reports_route = '@app.get("/ai-reports")' in content
        has_template_route = '@app.get("/template-management")' in content
        has_ai_reports_function = 'serve_ai_reports_dashboard' in content
        has_template_function = 'serve_template_management' in content
        
        print("\n🛤️  Route Configuration Check:")
        print(f"   {'✅' if has_ai_reports_route else '❌'} AI Reports route added")
        print(f"   {'✅' if has_template_route else '❌'} Template Management route added")
        print(f"   {'✅' if has_ai_reports_function else '❌'} AI Reports function added")  
        print(f"   {'✅' if has_template_function else '❌'} Template function added")
        
        return all([has_ai_reports_route, has_template_route, has_ai_reports_function, has_template_function])
        
    except Exception as e:
        print(f"\n❌ Error checking main.py: {e}")
        return False

def test_navigation_updated():
    """Test if navigation was updated"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/static/fragments/nav.html", "r") as f:
            content = f.read()
        
        has_reports_dropdown = 'toggleReportsMenu' in content
        has_ai_reports_link = 'href="/ai-reports"' in content
        has_template_link = 'href="/template-management"' in content
        has_reports_icon = 'description</span>' in content
        
        print("\n🧭 Navigation Update Check:")
        print(f"   {'✅' if has_reports_dropdown else '❌'} Reports dropdown added")
        print(f"   {'✅' if has_ai_reports_link else '❌'} AI Reports link added")
        print(f"   {'✅' if has_template_link else '❌'} Template Management link added")
        print(f"   {'✅' if has_reports_icon else '❌'} Reports icon added")
        
        return all([has_reports_dropdown, has_ai_reports_link, has_template_link, has_reports_icon])
        
    except Exception as e:
        print(f"\n❌ Error checking navigation: {e}")
        return False

def test_navigation_js_updated():
    """Test if navigation JavaScript was updated"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/static/js/nav-bar.js", "r") as f:
            content = f.read()
        
        has_reports_function = 'toggleReportsMenu' in content
        has_reports_dropdown_logic = 'reports-dropdown' in content
        
        print("\n🔧 Navigation JavaScript Check:")
        print(f"   {'✅' if has_reports_function else '❌'} Reports toggle function added")
        print(f"   {'✅' if has_reports_dropdown_logic else '❌'} Reports dropdown logic added")
        
        return has_reports_function and has_reports_dropdown_logic
        
    except Exception as e:
        print(f"\n❌ Error checking nav-bar.js: {e}")
        return False

def test_dashboard_cleanup():
    """Test if dashboard was cleaned up"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/templates/index.html", "r") as f:
            content = f.read()
        
        # AI Reports section should be removed
        no_ai_reports_section = 'AI Reports</h2>' not in content
        
        print("\n🧹 Dashboard Cleanup Check:")
        print(f"   {'✅' if no_ai_reports_section else '❌'} AI Reports section removed")
        
        return no_ai_reports_section
        
    except Exception as e:
        print(f"\n❌ Error checking dashboard: {e}")
        return False

def test_widget_cleanup():
    """Test if dashboard widget was cleaned up"""
    try:
        with open("/Users/duncanmiller/Documents/HadadaHealth/static/js/dashboard-widgets.js", "r") as f:
            content = f.read()
        
        # Widget replacement should be disabled
        widget_disabled = 'return;' in content and 'Disabled: AI Reports now has a dedicated page' in content
        
        print("\n🔧 Widget Cleanup Check:")
        print(f"   {'✅' if widget_disabled else '❌'} Widget replacement disabled")
        
        return widget_disabled
        
    except Exception as e:
        print(f"\n❌ Error checking widgets: {e}")
        return False

def main():
    print("🧪 AI Reports and Template Management Setup Verification")
    print("=" * 60)
    
    # Run all tests
    files_ok = test_files_exist()
    routes_ok = test_routes_added()
    nav_ok = test_navigation_updated()
    nav_js_ok = test_navigation_js_updated()
    dashboard_ok = test_dashboard_cleanup()
    widget_ok = test_widget_cleanup()
    
    # Summary
    print(f"\n📊 SETUP VERIFICATION SUMMARY:")
    print("=" * 40)
    print(f"   {'✅' if files_ok else '❌'} Page files exist: {files_ok}")
    print(f"   {'✅' if routes_ok else '❌'} Routes configured: {routes_ok}")
    print(f"   {'✅' if nav_ok else '❌'} Navigation updated: {nav_ok}")
    print(f"   {'✅' if nav_js_ok else '❌'} Navigation JS updated: {nav_js_ok}")
    print(f"   {'✅' if dashboard_ok else '❌'} Dashboard cleaned: {dashboard_ok}")
    print(f"   {'✅' if widget_ok else '❌'} Widget cleaned: {widget_ok}")
    
    overall = all([files_ok, routes_ok, nav_ok, nav_js_ok, dashboard_ok, widget_ok])
    print(f"\n🎯 OVERALL STATUS: {'✅ READY FOR TESTING' if overall else '❌ NEEDS FIXES'}")
    
    if overall:
        print("\n🎉 AI Reports and Template Management setup is complete!")
        print("   Navigation structure:")
        print("   📍 Reports → AI Reports Dashboard (/ai-reports)")
        print("   📍 Reports → Template Management (/template-management)")
        print("   📍 Admin → (Therapists, Medical Aids, Settings, Users, Billing)")
        print("\n   Direct access:")
        print("   🔗 http://localhost:8000/ai-reports")
        print("   🔗 http://localhost:8000/template-management")
    else:
        print("\n🔧 Some setup steps need attention before testing")

if __name__ == "__main__":
    main()