# RocketReach API Integration

## 📧 Tích hợp RocketReach API để tìm email cho lawyers

Hệ thống đã được tích hợp với [RocketReach API](https://docs.rocketreach.co/reference/rocketreach-api) để tự động tìm email addresses cho các lawyers đã được crawl từ LawInfo và SuperLawyers.

## 🏗️ Kiến trúc hệ thống

### Models
- **`RocketReachLookup`**: Lưu trữ kết quả lookup từ RocketReach API
- **`Lawyer`**: Model chính với field `entity_type` để phân biệt law firm vs individual attorney

### Services
- **`RocketReachAPI`**: Service class để gọi RocketReach API
- **`RocketReachLookupService`**: Service class để quản lý lookups trong database

### Celery Tasks
- **`lookup_lawyer_email_task`**: Lookup email cho 1 lawyer
- **`bulk_lookup_lawyers_task`**: Lookup email cho nhiều lawyers
- **`lookup_lawyers_without_email_task`**: Lookup email cho lawyers chưa có email
- **`update_lawyer_emails_from_rocketreach_task`**: Cập nhật email từ successful lookups

## 🚀 Cách sử dụng

### 1. Cấu hình API Key

Thêm vào `settings.py`:
```python
ROCKETREACH_API_KEY = "your_rocketreach_api_key_here"
```

### 2. Management Commands

```bash
# Lookup emails cho lawyers chưa có email
docker compose exec web python manage.py lookup_emails --mode missing --limit 100

# Lookup email cho 1 lawyer cụ thể
docker compose exec web python manage.py lookup_emails --mode single --lawyer-id 1

# Lookup email cho nhiều lawyers
docker compose exec web python manage.py lookup_emails --mode bulk --lawyer-ids 1 2 3 4 5

# Cập nhật email từ successful lookups
docker compose exec web python manage.py lookup_emails --mode update

# Cleanup old failed lookups
docker compose exec web python manage.py lookup_emails --mode cleanup --days-old 7

# Chạy async với Celery
docker compose exec web python manage.py lookup_emails --mode missing --async
```

### 3. Admin Interface

Truy cập Django Admin để:
- Xem danh sách lawyers và RocketReach lookups
- Chạy bulk actions để lookup emails
- Cập nhật emails từ successful lookups
- Retry failed lookups

### 4. Celery Tasks

```python
# Lookup email cho 1 lawyer
from apps.lawyers.rocketreach_tasks import lookup_lawyer_email_task
task = lookup_lawyer_email_task.delay(lawyer_id=1)

# Bulk lookup
from apps.lawyers.rocketreach_tasks import bulk_lookup_lawyers_task
task = bulk_lookup_lawyers_task.delay([1, 2, 3, 4, 5])

# Lookup lawyers without email
from apps.lawyers.rocketreach_tasks import lookup_lawyers_without_email_task
task = lookup_lawyers_without_email_task.delay(domain='lawinfo.com', limit=100)
```

## 📊 Tính năng chính

### 1. Entity Type Detection
- **LawInfo**: Tự động detect là `law_firm`
- **SuperLawyers**: Tự động detect là `individual_attorney`
- **Name-based detection**: Phân tích tên để detect entity type

### 2. Email Lookup Strategies
- **Domain-based lookup**: Sử dụng domain của website
- **Company-based lookup**: Sử dụng tên công ty luật
- **Name-based lookup**: Sử dụng tên luật sư cá nhân
- **Location-based lookup**: Sử dụng địa điểm

### 3. Data Quality
- **Confidence scoring**: Đánh giá độ tin cậy của email
- **Duplicate prevention**: Tránh lookup trùng lặp
- **Error handling**: Xử lý lỗi và retry logic

### 4. Admin Actions
- **Lookup emails**: Queue lookup cho selected lawyers
- **Update emails**: Cập nhật email từ successful lookups
- **Retry failed**: Retry failed lookups
- **Bulk operations**: Xử lý hàng loạt

## 🔧 Cấu hình nâng cao

### RocketReach API Settings
```python
ROCKETREACH_SETTINGS = {
    'BASE_URL': 'https://api.rocketreach.co/v2',
    'TIMEOUT': 30,
    'MAX_RETRIES': 3,
    'RATE_LIMIT_DELAY': 1,
    'BATCH_SIZE': 10,
}
```

### Celery Task Settings
```python
ROCKETREACH_CELERY_SETTINGS = {
    'TASK_SOFT_TIME_LIMIT': 300,
    'TASK_TIME_LIMIT': 600,
    'TASK_MAX_RETRIES': 3,
    'TASK_DEFAULT_RETRY_DELAY': 60,
}
```

## 📈 Monitoring & Analytics

### Statistics
- Total lawyers in database
- Lawyers with/without email
- Email coverage percentage
- RocketReach lookup success rate
- API credits usage

### Admin Dashboard
- Real-time lookup status
- Success/failure rates
- Email confidence scores
- API usage tracking

## 🚨 Lưu ý quan trọng

### 1. API Credits
- RocketReach API sử dụng credits
- Mỗi lookup tốn 1 credit
- Monitor credits usage trong admin

### 2. Rate Limiting
- API có rate limits
- Sử dụng delays giữa các requests
- Implement retry logic

### 3. Data Privacy
- Tuân thủ GDPR và privacy laws
- Chỉ lookup emails cho business purposes
- Có thể cần consent từ lawyers

## 🎯 Workflow đề xuất

1. **Setup**: Cấu hình RocketReach API key
2. **Crawl**: Chạy crawl từ LawInfo và SuperLawyers
3. **Lookup**: Chạy email lookup cho lawyers without email
4. **Update**: Cập nhật emails từ successful lookups
5. **Monitor**: Theo dõi success rate và credits usage
6. **Cleanup**: Dọn dẹp old failed lookups

## 📞 Support

- RocketReach API Documentation: https://docs.rocketreach.co/reference/rocketreach-api
- Contact: support@rocketreach.co
- Rate Limits: https://docs.rocketreach.co/guides/rate-limits
