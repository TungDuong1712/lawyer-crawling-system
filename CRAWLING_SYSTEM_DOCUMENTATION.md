# Hệ Thống Crawling - Lawyer Crawling System

## Tổng Quan

Hệ thống crawling thu thập thông tin luật sư từ các website pháp lý như LawInfo, SuperLawyers. Sử dụng Celery để xử lý bất đồng bộ và có tính năng anti-detection.

## Cấu Trúc Code Hiện Tại

### 1. Models (apps/crawler/models.py)
- **SourceConfiguration**: Cấu hình nguồn crawl với start URLs
- **DiscoveryURL**: Quản lý URLs cần crawl, có pagination

### 2. Tasks (apps/crawler/tasks.py)
- **AntiDetectionManager**: Tránh bị phát hiện khi crawl
- **crawl_session_task**: Task chính để crawl toàn bộ session
- **crawl_basic_lawyer_info_task**: Task crawl thông tin cơ bản + extract detail URLs
- **crawl_lawyer_detail_task**: Task crawl thông tin chi tiết từ detail URL

### 3. Lawyer Models (apps/lawyers/models.py)
- **Lawyer**: Model chính lưu thông tin luật sư
- **RocketReachLookup**: Lưu kết quả tìm email từ RocketReach

## Quy Trình Crawling

### Bước 1: Tạo Session
```python
# Tạo SourceConfiguration với start URLs
session = SourceConfiguration.objects.create(
    name="LawInfo Personal Injury",
    start_urls=[
        "https://www.lawinfo.com/personal-injury/arizona/chandler/",
        "https://www.lawinfo.com/personal-injury/new-mexico/albuquerque/"
    ]
)
```

### Bước 2: Chạy Crawl
```python
# Chạy task crawl
crawl_session_task.delay(session.id)
```

### Bước 3: Xử Lý Tự Động
1. **Tạo DiscoveryURL**: Từ start URLs
2. **Detect Pagination**: Tìm số trang và tạo URLs cho tất cả trang
3. **Crawl Basic Info**: Gọi `crawl_basic_lawyer_info_task` cho mỗi trang
4. **Extract Detail URLs**: Tìm detail URLs cho từng lawyer
5. **Crawl Detail**: Gọi `crawl_lawyer_detail_task` cho từng lawyer
6. **Lưu Database**: Lưu vào Lawyer model

## Anti-Detection Features

### AntiDetectionManager
```python
class AntiDetectionManager:
    def get_random_delay(self):
        return random.uniform(1.0, 3.0)  # Delay 1-3 giây
    
    def get_random_user_agent(self):
        return random.choice(self.user_agents)  # Random user agent
    
    def get_full_browser_headers(self):
        # Headers giống browser thật
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml...',
            'Accept-Language': 'en-US,en;q=0.9',
            # ... các headers khác
        }
```

## Data Extraction

### Selectors cho từng website
```python
selectors = {
    'lawinfo': {
        'container': '.card.firm.serp-container',
        'company_name': '.listing-details-header a',
        'phone': '.directory_phone',
        'address': '.locality, .region',
        'practice_areas': '.jobTitle',
        'website': '.directory_website',
        'email': '.directory_contact'
    },
    'superlawyers': {
        'container': '.card',
        'company_name': 'h2, h3, h4',
        'phone': '.phone-number',
        'address': '.address',
        'practice_areas': '.practice-areas',
        'website': '.website-link',
        'email': '.email-address'
    }
}
```

## Celery Tasks

### Task chính
- **crawl_session_task**: Crawl toàn bộ session (Orchestrator)
- **crawl_basic_lawyer_info_task**: Crawl thông tin cơ bản + extract detail URLs
- **crawl_lawyer_detail_task**: Crawl thông tin chi tiết từ detail URL

### Quy Trình Task Thực Tế
```
crawl_session_task (Orchestrator)
    ↓
    Tạo DiscoveryURLs từ start_urls
    ↓
    Detect pagination → tạo URLs cho tất cả trang
    ↓
    Gọi crawl_basic_lawyer_info_task cho mỗi trang
        ↓
        Gọi crawl_single_url_basic() từ detail_tasks
        ↓
        Extract basic info + detail URLs
        ↓
        Lưu basic info vào Lawyer model
        ↓
        Gọi crawl_lawyer_detail_task cho mỗi lawyer
            ↓
            Gọi crawl_lawyer_detail() từ detail_tasks
            ↓
            Extract detailed info từ detail URL
            ↓
            Update lawyer record
```

**Lưu ý:** `crawl_lawyer_info_task` là task cũ, chỉ được sử dụng trong admin và management command, không phải là phần của quy trình crawling chính.

### Chi Tiết Từng Task

#### 1. crawl_session_task
- **Chức năng**: Orchestrator - điều phối toàn bộ quá trình crawl
- **Input**: session_id
- **Quy trình**:
  1. Tạo DiscoveryURLs từ start_urls
  2. Detect pagination và tạo URLs cho tất cả trang
  3. Gọi `crawl_basic_lawyer_info_task` cho mỗi trang
  4. Update progress và status

#### 2. crawl_basic_lawyer_info_task
- **Chức năng**: Crawl thông tin cơ bản + extract detail URLs
- **Input**: discovery_url_id
- **Quy trình**:
  1. Crawl listing page (VD: danh sách lawyers)
  2. Extract basic info: tên, phone, address
  3. Extract detail URLs (link đến profile chi tiết)
  4. Lưu basic info vào Lawyer model
  5. Set detail_url cho mỗi lawyer

#### 3. crawl_lawyer_detail_task
- **Chức năng**: Crawl thông tin chi tiết từ detail URL
- **Input**: lawyer_id
- **Quy trình**:
  1. Crawl detail page (VD: profile lawyer)
  2. Extract detailed info: credentials, experience, etc.
  3. Update lawyer record với thông tin chi tiết

### Retry Logic
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def crawl_basic_lawyer_info_task(self, discovery_url_id):
    try:
        # Crawl basic info + extract detail URLs
        pass
    except Exception as exc:
        # Retry với exponential backoff
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
```

## Database Integration

### Lawyer Model Fields
- **Basic Info**: company_name, attorney_name, phone, address
- **Professional**: practice_areas, law_school, bar_admissions
- **Contact**: email, website, phone
- **Metadata**: domain, state, city, practice_area
- **Quality**: completeness_score, quality_score

### RocketReachLookup Model Fields
- **Related**: lawyer (ForeignKey to Lawyer)
- **Lookup Info**: lookup_name, lookup_company, lookup_domain
- **Contact**: email, phone, linkedin_url, twitter_url, facebook_url
- **Professional**: current_title, current_company, location, birth_year
- **Data**: job_history, education, skills, employee_emails (JSON fields)
- **Validation**: email_validation_status, phone_validation_status
- **Location**: region_latitude, region_longitude
- **Status**: status, confidence_score, lookup_timestamp
- **API**: api_credits_used, api_request_id, raw_response

### Data Validation
```python
def calculate_completeness_score(self):
    # Tính điểm hoàn thiện dựa trên fields có data
    core_filled = sum(1 for field in core_fields if field)
    return (core_filled / len(core_fields)) * 100
```

## Cách Sử Dụng

### 1. Chạy Crawl Session
```python
from apps.crawler.tasks import crawl_session_task

# Tạo session
session = SourceConfiguration.objects.create(
    name="Test Crawl",
    start_urls=["https://www.lawinfo.com/personal-injury/arizona/"]
)

# Chạy crawl
crawl_session_task.delay(session.id)
```

### 2. Ví Dụ Quy Trình Thực Tế
```python
# Bước 1: crawl_session_task
# - Tạo DiscoveryURL từ start_url
# - Detect pagination → tạo 5 URLs (trang 1-5)

# Bước 2: crawl_basic_lawyer_info_task cho mỗi trang
# - Crawl trang 1: extract 20 lawyers basic info
# - Crawl trang 2: extract 20 lawyers basic info
# - ... (trang 3, 4, 5)

# Bước 3: crawl_lawyer_detail_task cho mỗi lawyer
# - Crawl detail page của lawyer 1
# - Crawl detail page của lawyer 2
# - ... (100 lawyers total)

# Kết quả: 100 lawyers với đầy đủ thông tin
```

### 3. Xem Kết Quả
```python
# Xem lawyers đã crawl
lawyers = Lawyer.objects.filter(domain='lawinfo')
print(f"Found {lawyers.count()} lawyers")

# Xem progress
session = SourceConfiguration.objects.get(id=session_id)
print(f"Progress: {session.progress_percentage}%")

# Xem RocketReach lookups
lookups = RocketReachLookup.objects.filter(status='completed')
print(f"Found {lookups.count()} successful email lookups")

# Xem email confidence
for lookup in lookups:
    print(f"Lawyer: {lookup.lawyer.company_name}")
    print(f"Email: {lookup.email}")
    print(f"Confidence: {lookup.get_email_confidence()}")
    print(f"Social Profiles: {lookup.get_social_profiles()}")
```

### 4. Monitor Logs
```bash
# Xem Celery logs
celery -A lawyers_project worker --loglevel=info

# Xem Django logs
tail -f logs/django.log
```

## Cấu Hình

### Settings
```python
# Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Crawling
CRAWL_DELAY_MIN = 1.0
CRAWL_DELAY_MAX = 3.0
CRAWL_TIMEOUT = 30
CRAWL_MAX_RETRIES = 3
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/lawyer_db

# Redis
REDIS_URL=redis://localhost:6379/0

# RocketReach API
ROCKETREACH_API_KEY=your_api_key
```

## Troubleshooting

### Lỗi thường gặp
1. **Rate Limiting**: Tăng delay giữa requests
2. **Memory Issues**: Giảm batch size
3. **Selector không work**: Update selectors cho website mới
4. **Celery không chạy**: Check Redis connection

### Debug
```python
# Test selector
from apps.crawler.tasks import extract_lawyers_from_soup
soup = BeautifulSoup(html_content, 'html.parser')
lawyers = extract_lawyers_from_soup(soup, 'lawinfo', crawl_task)

# Check logs
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")
```

## Tích Hợp với Services Khác

### Database Service
- **PostgreSQL**: Lưu trữ data chính
- **Redis**: Cache và Celery broker

### Email Marketing (Mautic)
- **RocketReach**: Tìm email cho lawyers
- **Email Lists**: Tạo danh sách email marketing
- **Reports**: Báo cáo kết quả crawl

### Monitoring
- **Django Admin**: Quản lý sessions và data
- **Celery Flower**: Monitor tasks
- **Logs**: Debug và troubleshooting
