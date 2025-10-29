# 🏛️ Lawyer Data Crawling & Email Discovery System

A comprehensive Django-based web scraping system for collecting lawyer information and discovering professional email addresses using RocketReach API integration.

## 🚀 Features

- **Multi-domain crawling**: Support for lawinfo.com, superlawyers.com
- **2-Step Crawling**: Basic info + detailed information extraction
- **RocketReach Integration**: Professional email discovery and validation
- **Email Management**: Primary emails, company emails, employee contact discovery
- **Domain-specific configurations**: Real states and cities from LawInfo
- **Django Admin Interface**: Streamlined admin interface focused on email data
- **Background tasks**: Celery-based asynchronous crawling and email lookup
- **Docker support**: Complete containerization with Docker Compose
- **Data Export**: CSV export with detailed email information
- **Anti-detection**: Cloudflare bypass and anti-bot measures

## 📋 Requirements

- Python 3.10+
- Django 4.2+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- RocketReach API Key (for email discovery)

## 🛠️ Installation

### Docker Setup (Recommended)
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
docker compose up --build

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

### Step 3: Configure RocketReach API
```bash
# Set RocketReach API key in environment
export ROCKETREACH_API_KEY="your_api_key_here"

# Or add to docker-compose.yml environment section
```

### Step 4: Start Crawling
```bash
# Access admin interface to start crawling
# http://localhost:8001/admin/crawler/sourceconfiguration/
```

### Step 5: Access Admin Interface
- **Admin**: http://localhost:8001/admin/
- **Source Configurations**: http://localhost:8001/admin/crawler/sourceconfiguration/
- **Lawyers**: http://localhost:8001/admin/lawyers/lawyer/
- **RocketReach Lookups**: http://localhost:8001/admin/lawyers/rocketreachlookup/

### Step 6: Start Email Discovery
```bash
# Start RocketReach email lookup for lawyers
# Use admin interface: Lawyers -> Select lawyers -> "Lookup emails with RocketReach"
```

### Step 6b: Orchestrated Crawl + Lookup Flow (New)
```bash
# Trigger end-to-end workflow for a session (crawl listings then RocketReach lookups)
docker compose exec web python manage.py start_crawl_workflow <SESSION_ID> --lookup-limit 1000

# Example
docker compose exec web python manage.py start_crawl_workflow 1 --lookup-limit 500
```

### Step 6c: RocketReach Web Automation (Playwright) (New)
Requirements:
- Set credentials via env vars: `ROCKETREACH_EMAIL`, `ROCKETREACH_PASSWORD` (or use hardcoded credentials)
- Uses Microsoft's official Playwright Docker image for better compatibility

**Note**: If you encounter font/dependency issues with the original Dockerfile, the system automatically uses `Dockerfile.playwright` which is based on Microsoft's official Playwright image.

Test login first:
```bash
# Test login only (headed mode to see what happens)
docker compose exec web python manage.py rocketreach_api "test" --test-login --headed

# Test login in headless mode
docker compose exec web python manage.py rocketreach_api "test" --test-login
```

Run a web lookup by keyword (opens person search and clicks "Get Contact Info"):
```bash
# Synchronous execution (immediate results)
docker compose exec web python manage.py rocketreach_api "jayson shaw"

# Debug with visible browser
docker compose exec web python manage.py rocketreach_api "jayson shaw" --headed

# Run as Celery task (async)
docker compose exec web python manage.py rocketreach_api "jayson shaw" --async
```

**Note**: If login requires MFA/captcha, check the debug screenshots saved to `/tmp/` directory.

### Step 7: Check Results
```bash
# View crawled lawyers with email data
docker compose exec web python manage.py shell -c "
from apps.lawyers.models import Lawyer, RocketReachLookup
print(f'Total lawyers: {Lawyer.objects.count()}')
print(f'Lawyers with emails: {Lawyer.objects.exclude(email=\"\").count()}')
print(f'RocketReach lookups: {RocketReachLookup.objects.count()}')
print(f'Successful lookups: {RocketReachLookup.objects.filter(status=\"found\").count()}')
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

# RocketReach API
ROCKETREACH_API_KEY=your_api_key_here
```

## 📈 Usage

### Email Discovery Workflow

1. **Crawl Lawyer Data**: Use admin interface to start crawling
2. **Email Lookup**: Select lawyers and run "Lookup emails with RocketReach"
3. **Review Results**: Check RocketReach Lookups for discovered emails
4. **Export Data**: Use "Download Lawyers with Emails" to export CSV

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

### RocketReach Playwright Crawl (Pagination) – New Commands

Run web crawl against RocketReach with pagination and page-size control.

```bash
# Basic crawl (headless)
docker compose exec web python manage.py rocketreach_web crawl \
  --url "https://rocketreach.co/company?domain=law&start=1&pageSize=10" \
  --start-page 1 --num-pages 1 --page-size 10 --timeout 60 --headless

# Crawl a later page and only 1 page, overriding page size
docker compose exec web python manage.py rocketreach_web crawl \
  --url "https://rocketreach.co/company?domain=law&start=1&pageSize=10" \
  --start-page 10 --num-pages 1 --page-size 1 --timeout 90 --headless
```

Diagnostics after crawl (HTML analysis) – prints MAILTO_COUNT, HAS_GET_CONTACT, CARDS, SAMPLE_CARD_ID using the saved snapshots:

```bash
docker compose exec web python manage.py rocketreach_web crawl \
  --url "https://rocketreach.co/company?domain=law&start=1&pageSize=10" \
  --start-page 10 --num-pages 1 --page-size 1 --timeout 90 --headless \
  --debug-analyze-snapshots
```

This flag reads the latest saved snapshot (e.g., `rocketreach_employees_page.html`) from the project root and prints:
- MAILTO_COUNT and up to 10 `mailto:` links
- HAS_GET_CONTACT (presence of "Get Contact Info")
- CARDS count and a SAMPLE_CARD_ID

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
│   │   ├── models.py              # SourceConfiguration, DiscoveryURL
│   │   ├── tasks.py               # Celery tasks for crawling
│   │   ├── admin.py               # Admin interface with CSV export
│   │   └── management/commands/   # Management commands
│   ├── lawyers/                    # Lawyer data models
│   │   ├── models.py              # Lawyer, RocketReachLookup models
│   │   ├── admin.py               # Streamlined admin interface
│   │   ├── rocketreach_api_service.py # RocketReach API integration
│   │   └── rocketreach_tasks.py  # Email lookup tasks
│   └── tasks/                     # Task scheduling
├── lawyers_project/               # Django settings
├── static/                        # Static files
├── templates/                     # HTML templates
├── docker-compose.yml            # Docker setup (used in README)
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

### Email Discovery System
1. **RocketReach Integration**: Professional email discovery using RocketReach API
2. **Multiple Email Types**: Primary emails, company emails, employee contact discovery
3. **Email Validation**: SMTP validation and confidence scoring
4. **Batch Processing**: Celery-based asynchronous email lookup

### Domain-Specific Data
- **LawInfo**: 31 states, 61 cities, 6 practice areas
- **SuperLawyers**: 6 states, 4 cities per state, 6 practice areas

### Data Export Features
- **CSV Export**: Detailed export with email information
- **Email Breakdown**: Primary emails, company emails, employee emails
- **Professional Context**: Title, company, LinkedIn for each email
- **Validation Status**: Email validation and type information

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