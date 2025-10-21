# 🐳 Django Crawler System with Docker

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Django Web    │    │   PostgreSQL    │
│   (Port 80)     │◄──►│   (Port 8000)   │◄──►│   (Port 5432)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery        │    │   Redis         │
                       │   Worker        │◄──►│   (Port 6379)    │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Build and Start Services
```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### 2. Initialize Database
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 3. Access Application
- **Web Interface**: http://localhost
- **Admin Panel**: http://localhost/admin
- **API**: http://localhost/api/

## 📱 Services

### Web Service (Django)
- **Port**: 8000 (internal), 80 (external)
- **Features**: REST API, Admin Panel, Dashboard
- **Dependencies**: PostgreSQL, Redis

### Database Service (PostgreSQL)
- **Port**: 5432
- **Database**: lawyers_db
- **User**: crawler / password

### Cache Service (Redis)
- **Port**: 6379
- **Purpose**: Celery broker, caching

### Background Tasks (Celery)
- **Worker**: Processes crawl tasks
- **Beat**: Schedules periodic tasks

### Web Server (Nginx)
- **Port**: 80
- **Purpose**: Static files, load balancing

## 🏛️ Django Apps

### 1. Crawler App (`apps.crawler`)
- **Models**: CrawlSession, CrawlTask, CrawlConfig
- **Features**: Session management, task scheduling
- **API**: `/api/crawler/`

### 2. Lawyers App (`apps.lawyers`)
- **Models**: Lawyer, LawyerReview, LawyerContact
- **Features**: Data management, search, export
- **API**: `/api/lawyers/`

### 3. Tasks App (`apps.tasks`)
- **Models**: ScheduledTask, TaskLog
- **Features**: Task scheduling, logging
- **API**: `/api/tasks/`

## 🔧 Configuration

### Environment Variables
```bash
# Database
DB_NAME=lawyers_db
DB_USER=crawler
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Docker Compose Services
- **web**: Django application
- **db**: PostgreSQL database
- **redis**: Redis cache
- **celery**: Background worker
- **celery-beat**: Task scheduler
- **nginx**: Web server

## 📊 API Endpoints

### Crawler Management
```
GET    /api/crawler/sessions/          # List crawl sessions
POST   /api/crawler/sessions/          # Create crawl session
GET    /api/crawler/sessions/{id}/     # Get session details
POST   /api/crawler/sessions/{id}/start/  # Start crawling
POST   /api/crawler/sessions/{id}/stop/   # Stop crawling
```

### Lawyers Data
```
GET    /api/lawyers/                   # List lawyers
GET    /api/lawyers/{id}/              # Get lawyer details
GET    /api/lawyers/search/            # Search lawyers
GET    /api/lawyers/export/            # Export data
GET    /api/lawyers/stats/             # Get statistics
```

### Task Management
```
GET    /api/tasks/                     # List tasks
POST   /api/tasks/schedule/            # Schedule task
GET    /api/tasks/logs/                # Get task logs
```

## 🛠️ Development

### Run Commands
```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Run Django commands
docker-compose exec web python manage.py <command>

# View logs
docker-compose logs web
docker-compose logs celery

# Restart services
docker-compose restart web
```

### Database Operations
```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Load sample data
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
```

## 📈 Monitoring

### Health Checks
- **Web**: http://localhost/health
- **Database**: `docker-compose exec db pg_isready`
- **Redis**: `docker-compose exec redis redis-cli ping`

### Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs celery
docker-compose logs db
```

## 🔒 Security

### Production Settings
1. Change default passwords
2. Use environment variables for secrets
3. Enable HTTPS
4. Configure firewall rules
5. Regular security updates

### Database Security
- Use strong passwords
- Enable SSL connections
- Regular backups
- Access control

## 📦 Deployment

### Production Deployment
```bash
# Set production environment
export DEBUG=False
export SECRET_KEY=your-production-secret-key

# Build production image
docker-compose -f docker-compose.prod.yml up --build
```

### Scaling
```bash
# Scale workers
docker-compose up --scale celery=3

# Scale web instances
docker-compose up --scale web=2
```

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Check DB_HOST, DB_PORT
2. **Redis Connection**: Check REDIS_URL
3. **Permission Issues**: Check file ownership
4. **Port Conflicts**: Change port mappings

### Debug Mode
```bash
# Enable debug logging
export DEBUG=True
docker-compose up --build
```

## 📚 Documentation

- **Django**: https://docs.djangoproject.com/
- **Celery**: https://docs.celeryproject.org/
- **Docker**: https://docs.docker.com/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

**Happy Crawling! 🕷️⚖️**
