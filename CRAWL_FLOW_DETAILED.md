# FLOW CRAWL CHI TIẾT

## 🎯 **TỔNG QUAN FLOW CRAWL**

Hệ thống crawling sử dụng **2-step crawling process** với Celery tasks để xử lý song song:

```
SourceConfiguration → DiscoveryURL → Step 1 → Step 2 → Lawyer Objects
```

## 📋 **STEP 1: CRAWL BASIC LAWYER INFO**

### **1.1 Khởi tạo Crawl Session**
```python
# Admin action: start_crawl_workflow
crawl_session_task.delay(source.id)
```

### **1.2 Tạo DiscoveryURL Objects**
```python
# crawl_session_task()
for url in session.start_urls:
    # Parse URL để extract thông tin
    domain = 'lawinfo' if 'lawinfo.com' in url else 'superlawyers'
    practice_area = url_parts[4].replace('-', ' ').title()
    state = url_parts[5].replace('-', ' ').title()
    city = url_parts[6].replace('-', ' ').title()
    
    # Tạo DiscoveryURL
    DiscoveryURL.objects.create(
        source_config=session,
        url=url,
        domain=domain,
        practice_area=practice_area,
        state=state,
        city=city,
        status='PENDING'
    )
```

### **1.3 Crawl Basic Info (Step 1)**
```python
# crawl_basic_lawyer_info_task()
for task in tasks:
    lawyers_found = crawl_basic_lawyer_info_task(task.id)
    task.status = 'completed'
    task.lawyers_found = lawyers_found
```

### **1.4 Chi tiết Step 1 Process**
```python
# crawl_single_url_basic()
1. Fetch HTML content từ URL
2. Parse HTML với BeautifulSoup
3. Extract basic lawyer info:
   - company_name
   - attorney_name
   - phone, address, website
   - practice_areas
   - detail_url (cho Step 2)
4. Tạo Lawyer objects với is_detail_crawled=False
5. Return số lawyers tìm được
```

## 📋 **STEP 2: CRAWL DETAIL INFO**

### **2.1 Trigger Step 2**
```python
# Tự động trigger sau Step 1 hoặc manual
crawl_lawyer_detail_task.delay(lawyer_id)
```

### **2.2 Crawl Detail Info**
```python
# crawl_lawyer_detail_task()
1. Get lawyer với is_detail_crawled=False
2. Fetch detail_url HTML content
3. Parse HTML với BeautifulSoup
4. Extract detailed info:
   - attorney_details
   - law_school, bar_admissions
   - education, experience
   - badges, awards
   - lead_counsel_attorneys
5. Update Lawyer object với detailed info
6. Set is_detail_crawled=True
```

## 🔄 **DETAILED FLOW DIAGRAM**

```
┌─────────────────────────────────────────────────────────────────┐
│                        CRAWL FLOW CHI TIẾT                      │
└─────────────────────────────────────────────────────────────────┘

1. ADMIN ACTION
   └── start_crawl_workflow()
       └── crawl_session_task.delay(source.id)

2. SESSION INITIALIZATION
   ├── session.status = 'DISCOVERING'
   ├── Create DiscoveryURL objects from start_urls
   │   ├── Parse URL: domain, practice_area, state, city
   │   ├── Create DiscoveryURL với status='PENDING'
   │   └── Log: "Created X discovery URLs"
   └── update_crawl_progress(session_id)

3. STEP 1: BASIC CRAWL
   ├── For each DiscoveryURL:
   │   ├── crawl_basic_lawyer_info_task(discovery_url_id)
   │   │   ├── discovery_url.status = 'RUNNING'
   │   │   ├── crawl_single_url_basic(discovery_url)
   │   │   │   ├── Fetch HTML content
   │   │   │   ├── Parse với BeautifulSoup
   │   │   │   ├── Extract basic info:
   │   │   │   │   ├── company_name
   │   │   │   │   ├── attorney_name
   │   │   │   │   ├── phone, address, website
   │   │   │   │   ├── practice_areas
   │   │   │   │   └── detail_url
   │   │   │   ├── Create Lawyer objects
   │   │   │   └── Return lawyers_found count
   │   │   ├── discovery_url.lawyers_found = lawyers_found
   │   │   ├── discovery_url.status = 'COMPLETED'
   │   │   └── discovery_url.completed_at = now()
   │   └── Update success_count/error_count
   └── session.status = 'DONE'

4. STEP 2: DETAIL CRAWL (Optional)
   ├── For lawyers with is_detail_crawled=False:
   │   ├── crawl_lawyer_detail_task(lawyer_id)
   │   │   ├── Fetch detail_url HTML content
   │   │   ├── Parse với BeautifulSoup
   │   │   ├── Extract detailed info:
   │   │   │   ├── attorney_details
   │   │   │   ├── law_school, bar_admissions
   │   │   │   ├── education, experience
   │   │   │   ├── badges, awards
   │   │   │   └── lead_counsel_attorneys
   │   │   ├── Update Lawyer object
   │   │   └── Set is_detail_crawled=True
   │   └── Log: "Updated detailed info for lawyer"
   └── Complete detail crawling

5. PROGRESS TRACKING
   ├── update_crawl_progress(session_id)
   │   ├── Calculate progress_percentage
   │   ├── Update last_updated
   │   └── Save session
   └── Log: "Session completed: X success, Y errors"
```

## 🎯 **CRAWL TASKS BREAKDOWN**

### **Task 1: crawl_session_task**
```python
@shared_task
def crawl_session_task(session_id):
    """
    Main crawl session coordinator
    - Create DiscoveryURL objects
    - Trigger Step 1 for each URL
    - Update session progress
    """
```

### **Task 2: crawl_basic_lawyer_info_task**
```python
@shared_task(bind=True, max_retries=3)
def crawl_basic_lawyer_info_task(self, discovery_url_id):
    """
    Step 1: Crawl basic lawyer info
    - Extract basic information
    - Save detail URLs
    - Create Lawyer objects
    """
```

### **Task 3: crawl_lawyer_detail_task**
```python
@shared_task(bind=True, max_retries=3)
def crawl_lawyer_detail_task(self, lawyer_id):
    """
    Step 2: Crawl detailed lawyer info
    - Fetch detail URLs
    - Extract comprehensive information
    - Update Lawyer objects
    """
```

### **Task 4: update_crawl_progress**
```python
@shared_task
def update_crawl_progress(session_id):
    """
    Update crawl progress metrics
    - Calculate progress percentage
    - Update success/error counts
    - Save session status
    """
```

## 📊 **DATA FLOW**

### **Input:**
```
SourceConfiguration:
├── start_urls: ["https://www.lawinfo.com/personal-injury/arizona/chandler/"]
├── selectors: {"list": {...}, "detail": {...}}
└── configuration: delay, retries, timeout
```

### **Processing:**
```
DiscoveryURL:
├── url: "https://www.lawinfo.com/personal-injury/arizona/chandler/"
├── domain: "lawinfo"
├── practice_area: "Personal Injury"
├── state: "Arizona"
├── city: "Chandler"
└── status: "PENDING" → "RUNNING" → "COMPLETED"
```

### **Output:**
```
Lawyer Objects:
├── company_name: "Smith & Associates"
├── attorney_name: "John Smith"
├── phone: "(555) 123-4567"
├── address: "123 Main St, Chandler, AZ"
├── website: "https://smithlaw.com"
├── detail_url: "https://www.lawinfo.com/attorney/john-smith"
├── is_detail_crawled: False
└── crawl_timestamp: "2025-10-24T10:30:00Z"
```

## 🔧 **ERROR HANDLING**

### **Retry Mechanism:**
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def crawl_basic_lawyer_info_task(self, discovery_url_id):
    try:
        # Crawl logic
        pass
    except Exception as exc:
        # Update status to FAILED
        discovery_url.status = 'FAILED'
        discovery_url.error_message = str(exc)
        discovery_url.save()
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
```

### **Memory Management:**
```python
finally:
    # Memory cleanup
    try:
        if discovery_url: del discovery_url
        import gc
        collected = gc.collect()
        logger.debug(f"Memory cleanup: {collected} objects collected")
    except Exception as cleanup_error:
        logger.warning(f"Error during memory cleanup: {cleanup_error}")
```

## 📈 **PROGRESS TRACKING**

### **Session Level:**
```
SourceConfiguration:
├── total_urls: 60
├── crawled_urls: 45
├── success_count: 40
├── error_count: 5
├── progress_percentage: 75.0
└── last_updated: "2025-10-24T10:30:00Z"
```

### **URL Level:**
```
DiscoveryURL:
├── status: "COMPLETED"
├── lawyers_found: 15
├── started_at: "2025-10-24T10:25:00Z"
├── completed_at: "2025-10-24T10:30:00Z"
└── error_message: ""
```

## 🚀 **PARALLEL PROCESSING**

### **Celery Configuration:**
```python
# settings.py
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

### **Concurrency:**
```python
# Multiple workers can process different URLs simultaneously
# Each DiscoveryURL is processed independently
# Progress is tracked at session level
```

## 📋 **ADMIN INTERFACE**

### **SourceConfiguration Admin:**
- **Actions**: start_crawl_workflow, download_lawyers_data
- **Display**: name, status, progress_percentage, created_at
- **Filters**: status, created_at, created_by

### **DiscoveryURL Admin:**
- **Actions**: retry_failed_urls, mark_as_pending
- **Display**: source_config, domain, practice_area, city, status, lawyers_found
- **Filters**: status, domain, practice_area, state, created_at

## 🎯 **KẾT LUẬN**

**Flow crawl chi tiết bao gồm:**

1. **Session Initialization** - Tạo DiscoveryURL objects
2. **Step 1: Basic Crawl** - Extract basic lawyer info
3. **Step 2: Detail Crawl** - Extract comprehensive info
4. **Progress Tracking** - Monitor tiến độ real-time
5. **Error Handling** - Retry và error recovery
6. **Memory Management** - Cleanup resources
7. **Parallel Processing** - Xử lý song song hiệu quả

**→ Hệ thống đảm bảo crawling process được quản lý chặt chẽ, hiệu quả và có thể scale!**
