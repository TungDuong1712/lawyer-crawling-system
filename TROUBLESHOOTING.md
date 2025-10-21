# 🔧 Troubleshooting Guide

## 🚨 Common Issues and Solutions

### 1. Docker Build Timeout Error

**Error**: `ReadTimeoutError: HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Read timed out.`

### 2. Django Logging Error

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '/app/logs/django.log'`

**Solutions**:
```bash
# Use minimal setup (recommended)
docker-compose -f docker-compose.minimal-only.yml up --build

# Or fix logging in settings.py
# Remove file logging, use console only
```

### 3. Django URL Configuration Error

**Error**: `AttributeError: 'function' object has no attribute 'as_view'`

**Solutions**:
```bash
# Use minimal-only setup (recommended)
docker-compose -f docker-compose.minimal-only.yml up --build

# Or fix URL configuration
# Function-based views don't need .as_view()
```

### 4. Multiple URL Configuration Errors

**Error**: Multiple function-based views called as class-based views

**Fixed Views**:
- `apps.crawler.views.StartCrawlView`
- `apps.crawler.views.StopCrawlView`
- `apps.lawyers.views.LawyerStatsView`
- `apps.tasks.views.ScheduleTaskView`

**Solutions**:
```bash
# Test URL fixes
python test_urls_fixed.py

# Use minimal-only setup
docker-compose -f docker-compose.minimal-only.yml up --build
```

**Solutions**:

#### Option A: Use Simple Setup (Recommended)
```bash
# Use simplified Docker setup
docker-compose -f docker-compose.simple.yml up --build
```

#### Option B: Fix Network Issues
```bash
# Increase Docker timeout
export DOCKER_BUILDKIT=0
docker-compose up --build

# Or use different pip index
# Edit Dockerfile to use different pip source
```

#### Option C: Install Dependencies Locally
```bash
# Install Python dependencies locally first
pip install -r requirements.txt

# Then build Docker image
docker-compose up --build
```

### 2. Database Connection Issues

**Error**: `django.db.utils.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### 3. Django Migration Issues

**Error**: `django.db.utils.ProgrammingError: relation does not exist`

**Solutions**:
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load sample data (if available)
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
```

### 4. Port Conflicts

**Error**: `bind: address already in use`

**Solutions**:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :5432

# Kill processes using the ports
sudo kill -9 $(lsof -t -i:8000)
sudo kill -9 $(lsof -t -i:5432)

# Or change ports in docker-compose.yml
```

### 5. Permission Issues

**Error**: `Permission denied`

**Solutions**:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Make scripts executable
chmod +x start.sh
chmod +x test_docker_simple.sh
```

## 🛠️ Alternative Setup Methods

### Method 1: Local Development (No Docker)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up PostgreSQL locally
# Create database: lawyers_db
# Create user: crawler with password: password

# Run Django
python manage.py migrate
python manage.py runserver
```

### Method 2: Docker with Local Database

```bash
# Start only database
docker-compose up db

# Run Django locally
export DATABASE_URL=postgresql://crawler:password@localhost:5432/lawyers_db
python manage.py migrate
python manage.py runserver
```

### Method 3: Minimal Docker Setup

```bash
# Use simple Docker setup
docker-compose -f docker-compose.simple.yml up --build

# This uses minimal dependencies to avoid timeout issues
```

## 🔍 Debugging Commands

### Check Service Status
```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose logs web
docker-compose logs db
```

### Access Container Shell
```bash
# Access web container
docker-compose exec web bash

# Access database container
docker-compose exec db psql -U crawler -d lawyers_db
```

### Test Database Connection
```bash
# Test from web container
docker-compose exec web python manage.py dbshell

# Test from host
psql -h localhost -U crawler -d lawyers_db
```

### Check Network Connectivity
```bash
# Test web service
curl http://localhost:8000

# Test database
docker-compose exec web python -c "import psycopg2; print('DB connection OK')"
```

## 📊 Performance Optimization

### For Slow Networks
```bash
# Use local pip cache
pip install --cache-dir ~/.pip/cache -r requirements.txt

# Use different pip index
pip install -i https://pypi.douban.com/simple/ -r requirements.txt
```

### For Limited Resources
```bash
# Reduce Docker resources
docker-compose -f docker-compose.simple.yml up --build

# Use lighter base image
# Edit Dockerfile to use python:3.10-alpine
```

## 🆘 Emergency Recovery

### Reset Everything
```bash
# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v
docker system prune -a

# Rebuild from scratch
docker-compose up --build
```

### Backup and Restore
```bash
# Backup database
docker-compose exec db pg_dump -U crawler lawyers_db > backup.sql

# Restore database
docker-compose exec -T db psql -U crawler lawyers_db < backup.sql
```

## 📞 Getting Help

### Check Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs db
docker-compose logs celery
```

### Common Log Locations
- Django logs: `/app/logs/django.log`
- Application logs: `docker-compose logs web`
- Database logs: `docker-compose logs db`

### Useful Commands
```bash
# Restart specific service
docker-compose restart web

# Rebuild specific service
docker-compose up --build web

# View real-time logs
docker-compose logs -f web
```

---

**Need more help? Check the logs and try the solutions above! 🔧**
