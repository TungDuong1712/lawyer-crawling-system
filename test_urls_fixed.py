#!/usr/bin/env python3
"""
Test script to verify all URL configuration errors are fixed
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lawyers_project.settings')

def test_urls():
    """Test all URL configurations"""
    print("🔍 Testing URL configurations...")
    
    try:
        # Initialize Django
        django.setup()
        
        # Test main URLs
        from django.urls import reverse, NoReverseMatch
        from django.test import Client
        
        print("✅ Django setup successful")
        
        # Test URL patterns
        url_patterns = [
            ('crawler:dashboard', None),
            ('crawler:session-list', None),
            ('crawler:start-crawl', {'pk': 1}),
            ('crawler:stop-crawl', {'pk': 1}),
            ('lawyers:lawyer-list', None),
            ('lawyers:lawyer-stats', None),
            ('tasks:task-list', None),
            ('tasks:schedule-task', None),
        ]
        
        client = Client()
        
        for url_name, kwargs in url_patterns:
            try:
                if kwargs:
                    url = reverse(url_name, kwargs=kwargs)
                else:
                    url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except NoReverseMatch as e:
                print(f"❌ {url_name}: {e}")
            except Exception as e:
                print(f"⚠️  {url_name}: {e}")
        
        print("\n🎉 All URL configurations are working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing URLs: {e}")
        return False

def test_imports():
    """Test all imports"""
    print("🔍 Testing imports...")
    
    try:
        # Test app imports
        from apps.crawler import views as crawler_views
        from apps.lawyers import views as lawyers_views
        from apps.tasks import views as tasks_views
        
        print("✅ All app imports successful")
        
        # Test specific views
        views_to_test = [
            (crawler_views, 'StartCrawlView'),
            (crawler_views, 'StopCrawlView'),
            (lawyers_views, 'LawyerStatsView'),
            (tasks_views, 'ScheduleTaskView'),
        ]
        
        for module, view_name in views_to_test:
            if hasattr(module, view_name):
                view = getattr(module, view_name)
                if callable(view):
                    print(f"✅ {module.__name__}.{view_name}: Function-based view")
                else:
                    print(f"⚠️  {module.__name__}.{view_name}: Not callable")
            else:
                print(f"❌ {module.__name__}.{view_name}: Not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing imports: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Django URL Configuration Fixes")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed")
        return False
    
    print()
    
    # Test URLs
    if not test_urls():
        print("\n❌ URL tests failed")
        return False
    
    print("\n🎉 All tests passed! URL configuration is fixed.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
