# NHIỆM VỤ CỦA MODEL DISCOVERYURL

## 🎯 **NHIỆM VỤ CHÍNH**

`DiscoveryURL` là model trung tâm trong hệ thống crawling, có nhiệm vụ:

### 1. **URL Management**
- Lưu trữ từng URL cụ thể để crawl
- Parse URL để extract domain, state, city, practice_area
- Track trạng thái crawl của từng URL

### 2. **Progress Tracking**
- Monitor tiến độ crawl từng URL
- Lưu kết quả crawl (số lawyers tìm được)
- Track lỗi và retry cho từng URL

### 3. **Task Coordination**
- Liên kết với Celery tasks
- Quản lý parallel processing
- Handle error recovery

## 📊 **CẤU TRÚC DỮ LIỆU**

```
DiscoveryURL:
├── source_config (ForeignKey) → SourceConfiguration
├── url (URLField) → URL cụ thể để crawl
├── domain (CharField) → lawinfo.com, superlawyers.com
├── state (CharField) → Arizona, New Mexico
├── city (CharField) → Chandler, Albuquerque
├── practice_area (CharField) → personal-injury, family-law
├── status (CharField) → PENDING, RUNNING, COMPLETED, FAILED
├── lawyers_found (IntegerField) → Số lawyers tìm được
├── error_message (TextField) → Thông báo lỗi
└── celery_task_id (CharField) → ID của Celery task
```

## 🔄 **WORKFLOW**

```
SourceConfiguration
    ↓ (start_urls)
DiscoveryURL Creation
    ↓ (parse URL)
Domain/State/City/PracticeArea
    ↓ (Celery task)
crawl_basic_lawyer_info_task
    ↓ (extract data)
Lawyer Objects Created
    ↓ (update results)
DiscoveryURL.lawyers_found
    ↓ (update progress)
SourceConfiguration Progress
```

## 🎯 **VÍ DỤ CỤ THỂ**

### **Input URL:**
```
https://www.lawinfo.com/personal-injury/arizona/chandler/
```

### **Parsed DiscoveryURL:**
```
- domain: "lawinfo.com"
- state: "Arizona" 
- city: "Chandler"
- practice_area: "personal-injury"
- url: "https://www.lawinfo.com/personal-injury/arizona/chandler/"
```

### **Crawl Process:**
1. **PENDING** → URL được tạo, chờ crawl
2. **RUNNING** → Celery task đang crawl
3. **COMPLETED** → Tìm được 15 lawyers
4. **FAILED** → Lỗi crawl, cần retry

## ✅ **LỢI ÍCH**

### **1. Granular Tracking**
- Track từng URL riêng biệt
- Monitor progress chi tiết
- Identify problematic URLs

### **2. Error Handling**
- Xử lý lỗi cho từng URL
- Retry mechanism
- Error logging

### **3. Parallel Processing**
- Crawl nhiều URL cùng lúc
- Load balancing
- Resource optimization

### **4. Data Organization**
- Tổ chức dữ liệu theo URL
- Easy querying và filtering
- Historical tracking

## 🚀 **ADMIN INTERFACE**

### **List Display:**
- source_config, domain, practice_area, city
- status, lawyers_found, created_at

### **Actions:**
- retry_failed_urls
- mark_as_pending

### **Filters:**
- status, domain, practice_area, state, created_at

## 📈 **STATISTICS**

### **Progress Tracking:**
```
SourceConfiguration:
├── total_urls: 60
├── crawled_urls: 45
├── success_count: 40
├── error_count: 5
└── progress_percentage: 75%
```

### **DiscoveryURL Status:**
```
- PENDING: 15 URLs
- RUNNING: 5 URLs  
- COMPLETED: 40 URLs
- FAILED: 5 URLs
```

## 🎯 **KẾT LUẬN**

`DiscoveryURL` là **core component** của hệ thống crawling:

- **URL Management**: Quản lý từng URL cụ thể
- **Progress Tracking**: Monitor tiến độ chi tiết  
- **Error Handling**: Xử lý lỗi và retry
- **Parallel Processing**: Crawl song song
- **Data Organization**: Tổ chức dữ liệu hiệu quả

**→ DiscoveryURL đảm bảo crawling process được quản lý chặt chẽ và hiệu quả!**
