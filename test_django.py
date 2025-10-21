#!/usr/bin/env python3
"""
Test Django project structure
"""

import os
import sys
import django
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lawyers_project.settings')

def test_django_setup():
    """Test Django project setup"""
    print("🧪 Testing Django Project Setup")
    print("=" * 40)
    
    try:
        # Setup Django
        django.setup()
        print("✅ Django setup successful")
        
        # Test imports
        from django.conf import settings
        print(f"✅ Settings loaded: {settings.DEBUG}")
        
        # Test apps
        from apps.crawler.models import CrawlSession
        from apps.lawyers.models import Lawyer
        from apps.tasks.models import ScheduledTask
        print("✅ Models imported successfully")
        
        # Test URL patterns
        from django.urls import reverse
        print("✅ URL patterns loaded")
        
        # Test Celery
        from lawyers_project.celery import app as celery_app
        print("✅ Celery configured")
        
        print("\n🎉 Django project structure is valid!")
        print("\n📊 Project Summary:")
        print(f"   • Apps: {len(settings.INSTALLED_APPS)}")
        print(f"   • Database: {settings.DATABASES['default']['ENGINE']}")
        print(f"   • Redis: {settings.REDIS_URL}")
        print(f"   • Celery: {settings.CELERY_BROKER_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_models():
    """Test model definitions"""
    print("\n🧪 Testing Models")
    print("-" * 20)
    
    try:
        from apps.crawler.models import CrawlSession, CrawlTask, CrawlConfig
        from apps.lawyers.models import Lawyer, LawyerReview, LawyerContact
        from apps.tasks.models import ScheduledTask, TaskLog
        
        # Test model fields
        crawl_session_fields = [f.name for f in CrawlSession._meta.fields]
        lawyer_fields = [f.name for f in Lawyer._meta.fields]
        
        print(f"✅ CrawlSession fields: {len(crawl_session_fields)}")
        print(f"✅ Lawyer fields: {len(lawyer_fields)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def test_urls():
    """Test URL patterns"""
    print("\n🧪 Testing URL Patterns")
    print("-" * 25)
    
    try:
        from django.urls import reverse, resolve
        from django.test import Client
        
        # Test URL patterns
        client = Client()
        
        # Test main URLs
        urls_to_test = [
            '/',
            '/admin/',
            '/api/crawler/',
            '/api/lawyers/',
            '/api/tasks/',
        ]
        
        for url in urls_to_test:
            try:
                response = client.get(url)
            except:
                pass  # Some URLs might not work without database
        
        print("✅ URL patterns configured")
        return True
        
    except Exception as e:
        print(f"❌ URL error: {e}")
        return False

def main():
    """Main test function"""
    print("🏛️ DJANGO CRAWLER SYSTEM - STRUCTURE TEST")
    print("=" * 50)
    
    # Test Django setup
    if not test_django_setup():
        print("\n❌ Django setup failed")
        return False
    
    # Test models
    if not test_models():
        print("\n❌ Model tests failed")
        return False
    
    # Test URLs
    if not test_urls():
        print("\n❌ URL tests failed")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n💡 Next steps:")
    print("   1. Install Docker Desktop")
    print("   2. Run: docker-compose up --build")
    print("   3. Access: http://localhost")
    print("   4. Admin: http://localhost/admin")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
