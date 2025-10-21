#!/usr/bin/env python3
"""
Check Django project structure
"""

import os
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if file exists and report"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ Missing: {description}: {filepath}")
        return False

def check_directory_structure():
    """Check Django project directory structure"""
    print("🏛️ DJANGO CRAWLER SYSTEM - STRUCTURE CHECK")
    print("=" * 50)
    
    files_to_check = [
        # Django project files
        ("lawyers_project/__init__.py", "Django project init"),
        ("lawyers_project/settings.py", "Django settings"),
        ("lawyers_project/urls.py", "Django URLs"),
        ("lawyers_project/wsgi.py", "Django WSGI"),
        ("lawyers_project/celery.py", "Celery configuration"),
        
        # Django apps
        ("apps/__init__.py", "Apps package init"),
        ("apps/crawler/__init__.py", "Crawler app init"),
        ("apps/crawler/models.py", "Crawler models"),
        ("apps/crawler/views.py", "Crawler views"),
        ("apps/crawler/urls.py", "Crawler URLs"),
        ("apps/crawler/admin.py", "Crawler admin"),
        ("apps/crawler/serializers.py", "Crawler serializers"),
        ("apps/crawler/tasks.py", "Crawler tasks"),
        
        ("apps/lawyers/__init__.py", "Lawyers app init"),
        ("apps/lawyers/models.py", "Lawyers models"),
        ("apps/lawyers/views.py", "Lawyers views"),
        ("apps/lawyers/urls.py", "Lawyers URLs"),
        ("apps/lawyers/admin.py", "Lawyers admin"),
        ("apps/lawyers/serializers.py", "Lawyers serializers"),
        ("apps/lawyers/tasks.py", "Lawyers tasks"),
        ("apps/lawyers/filters.py", "Lawyers filters"),
        
        ("apps/tasks/__init__.py", "Tasks app init"),
        ("apps/tasks/models.py", "Tasks models"),
        ("apps/tasks/views.py", "Tasks views"),
        ("apps/tasks/urls.py", "Tasks URLs"),
        ("apps/tasks/serializers.py", "Tasks serializers"),
        ("apps/tasks/tasks.py", "Tasks tasks"),
        
        # Docker files
        ("Dockerfile", "Docker configuration"),
        ("docker-compose.yml", "Docker Compose"),
        ("nginx.conf", "Nginx configuration"),
        ("start.sh", "Start script"),
        
        # Requirements and config
        ("requirements.txt", "Python requirements"),
        ("init.sql", "Database initialization"),
    ]
    
    all_good = True
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_good = False
    
    return all_good

def check_django_structure():
    """Check Django-specific structure"""
    print("\n🧪 Django Structure Check")
    print("-" * 30)
    
    # Check for Django project structure
    django_files = [
        "lawyers_project/settings.py",
        "lawyers_project/urls.py",
        "lawyers_project/wsgi.py",
    ]
    
    for file in django_files:
        if os.path.exists(file):
            print(f"✅ Django file: {file}")
        else:
            print(f"❌ Missing Django file: {file}")
            return False
    
    # Check for Django apps
    apps = ["crawler", "lawyers", "tasks"]
    for app in apps:
        app_path = f"apps/{app}"
        if os.path.exists(app_path):
            print(f"✅ Django app: {app}")
        else:
            print(f"❌ Missing Django app: {app}")
            return False
    
    return True

def check_docker_structure():
    """Check Docker configuration"""
    print("\n🐳 Docker Structure Check")
    print("-" * 30)
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml",
        "nginx.conf",
        "start.sh",
    ]
    
    for file in docker_files:
        if os.path.exists(file):
            print(f"✅ Docker file: {file}")
        else:
            print(f"❌ Missing Docker file: {file}")
            return False
    
    return True

def show_project_summary():
    """Show project summary"""
    print("\n📊 PROJECT SUMMARY")
    print("=" * 20)
    
    # Count files
    total_files = 0
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(('.py', '.yml', '.yaml', '.conf', '.sh', '.sql', '.txt')):
                total_files += 1
    
    print(f"📁 Total files: {total_files}")
    
    # Django apps
    apps = ["crawler", "lawyers", "tasks"]
    print(f"🏛️ Django apps: {len(apps)}")
    for app in apps:
        print(f"   • {app}")
    
    # Docker services
    services = ["web", "db", "redis", "celery", "celery-beat", "nginx"]
    print(f"🐳 Docker services: {len(services)}")
    for service in services:
        print(f"   • {service}")
    
    # Features
    features = [
        "Crawl Session Management",
        "Lawyer Database",
        "Task Scheduling",
        "REST API",
        "Admin Panel",
        "Background Processing",
        "Data Export",
        "Quality Scoring"
    ]
    print(f"⚡ Features: {len(features)}")
    for feature in features:
        print(f"   • {feature}")

def main():
    """Main check function"""
    print("🔍 Checking Django Crawler System Structure...")
    
    # Check file structure
    structure_ok = check_directory_structure()
    
    # Check Django structure
    django_ok = check_django_structure()
    
    # Check Docker structure
    docker_ok = check_docker_structure()
    
    # Show summary
    show_project_summary()
    
    print("\n" + "=" * 50)
    if structure_ok and django_ok and docker_ok:
        print("🎉 All structure checks passed!")
        print("\n💡 Next steps:")
        print("   1. Install Docker Desktop")
        print("   2. Run: docker-compose up --build")
        print("   3. Access: http://localhost")
        print("   4. Admin: http://localhost/admin")
        return True
    else:
        print("❌ Some structure checks failed")
        print("   Please check the missing files above")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
