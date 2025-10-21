# 🏛️ Lawyer Data Crawling System

A comprehensive Django-based web scraping system for collecting lawyer information from various legal websites.

## 🚀 Features

- **Multi-domain crawling**: Support for lawinfo.com, superlawyers.com, avvo.com
- **Django REST API**: Full RESTful API for data management
- **Background tasks**: Celery-based asynchronous crawling
- **Docker support**: Complete containerization with Docker Compose
- **Data export**: CSV/JSON export functionality
- **Search & filtering**: Advanced search and filtering capabilities
- **Statistics**: Real-time crawling statistics and analytics

## 📋 Requirements

- Python 3.10+
- Django 4.2+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

## 🛠️ Installation

### Option 1: Docker Setup (Recommended)

#### Minimal Setup (Fastest)
```bash
# Clone repository
git clone <repository-url>
cd website_joel

# Start minimal services
docker-compose -f docker-compose.minimal-only.yml up --build

# Test setup
./test_minimal_only.sh
```

#### Full Setup
```bash
# Start all services
docker-compose up --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
# Create database: lawyers_db
# Create user: crawler with password: password

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## 🐳 Docker Services

| Service | Description | Port |
|---------|-------------|------|
| web | Django application | 8000 |
| db | PostgreSQL database | 5432 |
| redis | Redis cache/broker | 6379 |
| celery | Background task worker | - |
| celery-beat | Scheduled task scheduler | - |
| nginx | Web server (full setup) | 80 |

## 📊 API Endpoints

### Crawler API
- `GET /api/crawler/` - List crawl sessions
- `POST /api/crawler/sessions/` - Create new session
- `POST /api/crawler/sessions/{id}/start/` - Start crawling
- `POST /api/crawler/sessions/{id}/stop/` - Stop crawling

### Lawyers API
- `GET /api/lawyers/` - List lawyers
- `GET /api/lawyers/search/` - Search lawyers
- `GET /api/lawyers/export/` - Export data
- `GET /api/lawyers/stats/` - Get statistics

### Tasks API
- `GET /api/tasks/` - List scheduled tasks
- `POST /api/tasks/schedule/` - Schedule new task

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

### Crawling Configuration
Edit `config.py` to customize:
- Target domains and URLs
- CSS selectors for data extraction
- Crawling delays and retry settings
- User agents and headers

## 📈 Usage

### Start Crawling Session
```bash
# Via API
curl -X POST http://localhost:8000/api/crawler/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Session", "config": {...}}'

# Start crawling
curl -X POST http://localhost:8000/api/crawler/sessions/1/start/
```

### Export Data
```bash
# CSV export
curl http://localhost:8000/api/lawyers/export/?format=csv

# JSON export
curl http://localhost:8000/api/lawyers/export/?format=json
```

### View Statistics
```bash
curl http://localhost:8000/api/lawyers/stats/
```

## 🧪 Testing

### Test URL Configuration
```bash
python test_urls_fixed.py
```

### Test Docker Setup
```bash
# Minimal setup
./test_minimal_only.sh

# Simple setup
./test_docker_simple.sh

# Full setup
./test_minimal.sh
```

## 🔍 Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

### Common Issues
1. **Docker build timeout**: Use minimal setup
2. **Database connection**: Check PostgreSQL service
3. **URL configuration**: Run URL test script
4. **Permission errors**: Check file permissions

## 📁 Project Structure

```
website_joel/
├── apps/
│   ├── crawler/          # Crawling logic
│   ├── lawyers/          # Lawyer data models
│   └── tasks/            # Task scheduling
├── lawyers_project/      # Django settings
├── static/               # Static files
├── templates/            # HTML templates
├── docker-compose*.yml  # Docker configurations
├── Dockerfile*          # Docker images
└── requirements.txt     # Python dependencies
```

## 🚀 Deployment

### Production Setup
1. Update environment variables
2. Configure database settings
3. Set up reverse proxy (Nginx)
4. Configure SSL certificates
5. Set up monitoring and logging

### Scaling
- Use multiple Celery workers
- Set up Redis cluster
- Use PostgreSQL read replicas
- Implement caching strategies

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Create an issue on GitHub
- Contact the development team

---

**Happy Crawling! 🕷️**