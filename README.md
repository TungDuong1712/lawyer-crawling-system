# 🏛️ Lawyer Data Crawling System

A comprehensive Django-based web scraping system for collecting lawyer information from various legal websites.

## 🚀 Features

- **Multi-domain crawling**: Support for lawinfo.com, superlawyers.com
- **2-Step Crawling**: Basic info + detailed information extraction
- **Domain-specific configurations**: Real states and cities from LawInfo
- **Django Admin Interface**: Full admin interface for data management
- **Background tasks**: Celery-based asynchronous crawling
- **Docker support**: Complete containerization with Docker Compose
- **Data quality scoring**: Automatic completeness and quality scoring
- **Anti-detection**: Cloudflare bypass and anti-bot measures

## 📋 Requirements

- Python 3.10+
- Django 4.2+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

## 🛠️ Installation

### Docker Setup (Recommended)

#### Simple Setup (Fastest)
```bash
# Clone repository
git clone <repository-url>
cd lawyer-crawling-system

# Start services
docker compose -f docker-compose.simple.yml up --build

# Run migrations
docker compose exec web python manage.py migrate

# Create sample data
docker compose exec web python manage.py create_sample_data
```

#### Full Setup
```bash
# Start all services
docker compose up --build

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
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
| web | Django application | 8001 |
| db | PostgreSQL database | 5432 |
| redis | Redis cache/broker | 6379 |
| celery | Background task worker | - |
| celery-beat | Scheduled task scheduler | - |

## 🚀 Quick Start Guide

### Step 1: Start the System
```bash
# Clone and start
git clone <repository-url>
cd lawyer-crawling-system
docker compose -f docker-compose.simple.yml up --build

# Run migrations
docker compose exec web python manage.py migrate
```

### Step 2: Setup Source Configurations
```bash
# Setup LawInfo (62 URLs, 40 selectors: 13 list + 27 detail)
docker compose exec web python manage.py setup_lawinfo

# Setup SuperLawyers (60 URLs, 34 selectors: 12 list + 22 detail)
docker compose exec web python manage.py setup_superlawyers
```

### Step 3: Start Crawling
```bash
# Access admin interface to start crawling
# http://localhost:8001/admin/crawler/sourceconfiguration/
```

### Step 4: Access Admin Interface
- **Admin**: http://localhost:8001/admin/
- **Source Configurations**: http://localhost:8001/admin/crawler/sourceconfiguration/
- **Discovery URLs**: http://localhost:8001/admin/crawler/discoveryurl/
- **Lawyers**: http://localhost:8001/admin/lawyers/lawyer/

### Step 6: Check Results
```bash
# View crawled lawyers
docker compose exec web python manage.py shell -c "
from apps.lawyers.models import Lawyer
print(f'Total lawyers: {Lawyer.objects.count()}')
for lawyer in Lawyer.objects.all()[:5]:
    print(f'- {lawyer.company_name} ({lawyer.phone}) - Quality: {lawyer.quality_score}')
"
```

## 🔧 Configuration

### SourceConfiguration Model
SourceConfiguration defines crawling behavior with start URLs and selectors:

#### Configuration Fields
- **Basic Info**: name, description, status, created_by
- **Start URLs**: List of URLs to crawl (e.g., `["www.lawinfo.com/personal-injury/arizona/chandler/"]`)
- **Selectors**: JSON field with structured selectors:
  - `list`: Selectors for listing pages (basic lawyer info)
  - `detail`: Selectors for detail pages (comprehensive info)
- **Crawling Settings**: delay_between_requests, max_retries, timeout
- **Progress Tracking**: total_urls, crawled_urls, success_count, error_count, progress_percentage

#### Selector Structure
```json
{
  "list": {
    "lawyer_name": "//h2[@class='listing-details-header']//a",
    "phone": "//a[@class='directory_phone']//span",
    "detail_url": "//a[@class='directory_profile']/@href"
  },
  "detail": {
    "firm_name": "//h1[@class='org listing-details-header']",
    "address": "//p[@class='listing-desc-address']",
    "attorney_name": "//h4[contains(text(), 'Attorney')]"
  }
}
```


#### Domain-Specific Settings
The system supports domain-specific configurations:

#### LawInfo Domain
- **31 states** with **61 cities**
- **6 practice areas**: personal-injury, car-accident, immigration, bankruptcy, family-law, drunk-driving
- **URL pattern**: `https://www.lawinfo.com/{practice_area}/{state}/{city}/`

#### SuperLawyers Domain
- **6 states** with **4 cities per state**
- **6 practice areas**: business-litigation, personal-injury, criminal-defense, family-law, employment-law, real-estate-law
- **URL pattern**: `https://attorneys.superlawyers.com/{practice_area}/{state}/{city}/`

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

## 📈 Usage

### Management Commands


#### Create Source Configuration
```bash
# Quick setup with full configuration (recommended)
docker compose exec web python manage.py setup_lawinfo

# Quick setup for SuperLawyers
docker compose exec web python manage.py setup_superlawyers

# List existing configurations
docker compose exec web python manage.py shell -c "
from apps.crawler.models import SourceConfiguration
configs = SourceConfiguration.objects.all()
for config in configs:
    print(f'ID: {config.id}, Name: {config.name}, URLs: {len(config.start_urls)}')
"
```

#### Start Crawling
```bash
# Start crawl workflow
docker compose exec web python manage.py start_crawl_workflow \
  --session-id 1 \
  --domains lawinfo \
  --states texas california \
  --practice-areas personal-injury car-accident \
  --limit 50
```

#### Check Results
```bash
# View SourceConfigurations
docker compose exec web python manage.py shell -c "
from apps.crawler.models import SourceConfiguration
configs = SourceConfiguration.objects.all()
for config in configs:
    print(f'ID: {config.id}, Name: {config.name}, Status: {config.status}')
"

# View Lawyers
docker compose exec web python manage.py shell -c "
from apps.lawyers.models import Lawyer
lawyers = Lawyer.objects.all()
print(f'Total lawyers: {lawyers.count()}')
for lawyer in lawyers[:5]:
    print(f'- {lawyer.company_name} ({lawyer.phone})')
"
```

## 🧪 Testing

### Test System Setup
```bash
# Test simple config
docker compose exec web python manage.py simple_config --list-options

# Test crawl workflow
docker compose exec web python manage.py start_crawl_workflow \
  --session-id 1 \
  --domains lawinfo \
  --states texas \
  --practice-areas personal-injury \
  --limit 10
```

### Test Data Quality
```bash
# Check data quality scores
docker compose exec web python manage.py shell -c "
from apps.lawyers.models import Lawyer
lawyers = Lawyer.objects.all()
for lawyer in lawyers:
    print(f'{lawyer.company_name}: Completeness={lawyer.completeness_score}, Quality={lawyer.quality_score}')
"
```

## 🔍 Troubleshooting

### Common Issues

1. **Docker container not starting**:
   ```bash
   # Check container status
   docker compose ps
   
   # Check logs
   docker compose logs web
   ```

2. **Database connection issues**:
   ```bash
   # Check database service
   docker compose exec web python manage.py dbshell
   ```

3. **Migration issues**:
   ```bash
   # Run migrations
   docker compose exec web python manage.py migrate
   ```

4. **Permission errors**:
   ```bash
   # Fix permissions
   docker compose exec web chmod -R 777 /app
   ```

## 📁 Project Structure

```
lawyer-crawling-system/
├── apps/
│   ├── crawler/                    # Crawling logic
│   │   ├── models.py              # SourceConfiguration, DiscoveryURL, CrawlTemplate
│   │   ├── tasks.py               # Celery tasks for crawling
│   │   ├── detail_tasks.py        # 2-step crawling helpers
│   │   ├── simple_config.py       # Domain-specific configurations
│   │   └── management/commands/   # Management commands
│   ├── lawyers/                    # Lawyer data models
│   │   ├── models.py              # Lawyer model with quality scoring
│   │   └── admin.py               # Admin interface
│   └── tasks/                     # Task scheduling
├── lawyers_project/               # Django settings
├── static/                        # Static files
├── templates/                     # HTML templates
├── docker-compose.simple.yml     # Simple Docker setup
├── docker-compose.yml            # Full Docker setup
├── Dockerfile                    # Docker image
└── requirements.txt              # Python dependencies
```

## 🚀 Deployment

### Production Setup
1. Update environment variables in `docker-compose.yml`
2. Configure database settings
3. Set up reverse proxy (Nginx)
4. Configure SSL certificates
5. Set up monitoring and logging

### Scaling
- Use multiple Celery workers
- Set up Redis cluster
- Use PostgreSQL read replicas
- Implement caching strategies

## 📊 Key Features

### 2-Step Crawling Process
1. **Step 1**: Crawl basic lawyer information + detail URLs from listing pages
2. **Step 2**: Crawl detailed information from individual lawyer pages

### Domain-Specific Data
- **LawInfo**: 31 states, 61 cities, 6 practice areas
- **SuperLawyers**: 6 states, 4 cities per state, 6 practice areas

### Data Quality Scoring
- **Completeness Score**: Based on filled fields
- **Quality Score**: Based on data validation (phone, email, address format)

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