# FLOW CRAWL VỚI GIAO DIỆN ADMIN

## 🎯 **TỔNG QUAN ADMIN FLOW**

Hệ thống crawling được quản lý hoàn toàn thông qua Django Admin interface với các thao tác đơn giản:

```
Admin Interface → SourceConfiguration → DiscoveryURL → Lawyer Objects
```

## 📋 **STEP 1: TẠO SOURCE CONFIGURATION**

### **1.1 Truy cập Admin**
```
URL: http://localhost:8001/admin/
Login: admin / admin
```

### **1.2 Tạo Source Configuration**
```
Navigation: Crawler → Source Configurations → Add Source Configuration

Fields to fill:
├── Name: "LawInfo Personal Injury Attorneys"
├── Description: "Crawl personal injury attorneys from LawInfo.com"
├── Created by: admin (auto-selected)
├── Start URLs: [
│   "https://www.lawinfo.com/personal-injury/arizona/chandler/",
│   "https://www.lawinfo.com/personal-injury/arizona/phoenix/",
│   "https://www.lawinfo.com/personal-injury/california/los-angeles/"
│ ]
├── Selectors: {
│   "list": {
│     "company_name": "//div[@class='lawyer-name']/text()",
│     "phone": "//div[@class='phone']/text()",
│     "address": "//div[@class='address']/text()"
│   },
│   "detail": {
│     "attorney_details": "//div[@class='attorney-info']/text()",
│     "education": "//div[@class='education']/text()"
│   }
│ }
├── Delay between requests: 2.0
├── Max retries: 3
└── Timeout: 30
```

### **1.3 Save Configuration**
```
Click: "Save" button
Result: SourceConfiguration created with status "PENDING"
```

## 📋 **STEP 2: QUẢN LÝ SOURCE CONFIGURATION**

### **2.1 List View - Source Configurations**
```
URL: http://localhost:8001/admin/crawler/sourceconfiguration/

Display columns:
├── Name: "LawInfo Personal Injury Attorneys"
├── Status: "PENDING"
├── Progress: 0.0%
├── Total URLs: 0
├── Crawled URLs: 0
├── Success Count: 0
├── Error Count: 0
├── Created At: "2025-10-24 10:30:00"
└── Created By: "admin"
```

### **2.2 Filter & Search**
```
Filters available:
├── Status: PENDING, CRAWLING, PAUSED, RETRYING, FAILED, DONE, CANCELLED
├── Created At: Date range picker
├── Created By: User dropdown
└── Domain: lawinfo, superlawyers

Search fields:
├── Name: "LawInfo"
├── Description: "personal injury"
└── Start URLs: "chandler"
```

### **2.3 Detail View - Source Configuration**
```
URL: http://localhost:8001/admin/crawler/sourceconfiguration/1/change/

Sections:
├── Basic Information
│   ├── Source URL
│   ├── Domain
│   ├── Practice Area
│   ├── State
│   ├── City
│   └── Entity Type
├── Multiple Emails
│   ├── Company Emails (JSONField)
│   ├── Employee Contacts (JSONField)
│   └── All Emails Display (readonly)
├── Professional Information
├── SuperLawyers Specific
├── Additional Metadata
├── Lead Counsel (LawInfo)
├── Related Information
├── Crawling Information
└── Quality Scores
```

## 📋 **STEP 3: BẮT ĐẦU CRAWL SESSION**

### **3.1 Admin Actions - Source Configuration**
```
Select Source Configuration → Actions dropdown → "Start crawl workflow"

Available actions:
├── start_crawl_workflow: "Start crawl workflow"
├── download_lawyers_data: "Download lawyers data"
└── Custom actions
```

### **3.2 Start Crawl Workflow**
```
Action: start_crawl_workflow
Process:
├── Change status to "CRAWLING"
├── Create DiscoveryURL objects from start_urls
├── Parse URLs to extract domain, state, city, practice_area
├── Trigger crawl_basic_lawyer_info_task for each URL
└── Update progress in real-time
```

### **3.3 Progress Monitoring**
```
Real-time updates:
├── Status: PENDING → CRAWLING → DONE
├── Progress: 0.0% → 25.0% → 50.0% → 100.0%
├── Crawled URLs: 0 → 1 → 2 → 3
├── Success Count: 0 → 1 → 2 → 3
├── Error Count: 0 → 0 → 0 → 0
└── Last Updated: "2025-10-24 10:35:00"
```

## 📋 **STEP 4: QUẢN LÝ DISCOVERY URLS**

### **4.1 List View - Discovery URLs**
```
URL: http://localhost:8001/admin/crawler/discoveryurl/

Display columns:
├── Source Config: "LawInfo Personal Injury Attorneys"
├── Domain: "lawinfo"
├── Practice Area: "Personal Injury"
├── City: "Chandler"
├── Status: "COMPLETED"
├── Lawyers Found: 15
└── Created At: "2025-10-24 10:30:00"
```

### **4.2 Filter & Search Discovery URLs**
```
Filters available:
├── Status: PENDING, RUNNING, COMPLETED, FAILED, RETRYING
├── Domain: lawinfo, superlawyers
├── Practice Area: Personal Injury, Family Law
├── State: Arizona, California
└── Created At: Date range picker

Search fields:
├── URL: "chandler"
├── Domain: "lawinfo"
├── City: "phoenix"
└── Source Config: "LawInfo"
```

### **4.3 Detail View - Discovery URL**
```
URL: http://localhost:8001/admin/crawler/discoveryurl/1/change/

Sections:
├── Lookup Information
│   ├── Source Config
│   ├── URL
│   ├── Domain
│   ├── Practice Area
│   ├── State
│   ├── City
│   └── Status
├── Results
│   ├── Lawyers Found
│   ├── Error Message
│   ├── Started At
│   └── Completed At
└── Celery Task
    ├── Task ID
    └── Task Status
```

### **4.4 Admin Actions - Discovery URLs**
```
Select Discovery URLs → Actions dropdown → Available actions

Available actions:
├── retry_failed_urls: "Retry failed URLs"
├── mark_as_pending: "Mark as pending"
└── Custom actions
```

## 📋 **STEP 5: QUẢN LÝ LAWYER OBJECTS**

### **5.1 List View - Lawyers**
```
URL: http://localhost:8001/admin/lawyers/lawyer/

Display columns:
├── Company Name: "Smith & Associates"
├── Attorney Name: "John Smith"
├── Entity Type: "individual_attorney"
├── City: "Chandler"
├── State: "Arizona"
├── Domain: "lawinfo"
├── Practice Area: "Personal Injury"
├── Email Count: 3
├── Is Verified: True
└── Completeness Score: 85.0
```

### **5.2 Filter & Search Lawyers**
```
Filters available:
├── Entity Type: law_firm, individual_attorney, unknown
├── Domain: lawinfo, superlawyers
├── State: Arizona, California
├── Practice Area: Personal Injury, Family Law
├── Is Verified: True, False
├── Is Active: True, False
└── Crawl Timestamp: Date range picker

Search fields:
├── Company Name: "Smith"
├── Attorney Name: "John"
├── Phone: "555"
├── Email: "smith@"
└── Address: "Main St"
```

### **5.3 Detail View - Lawyer**
```
URL: http://localhost:8001/admin/lawyers/lawyer/1/change/

Sections:
├── Basic Information
├── Lawyer Details
├── Multiple Emails (NEW)
│   ├── Company Emails (JSONField)
│   ├── Employee Contacts (JSONField)
│   └── All Emails Display (readonly)
├── Professional Information
├── SuperLawyers Specific
├── Additional Metadata
├── Lead Counsel (LawInfo)
├── Related Information
├── Crawling Information
└── Quality Scores
```

### **5.4 Admin Actions - Lawyers**
```
Select Lawyers → Actions dropdown → Available actions

Available actions:
├── lookup_email_rocketreach: "Lookup emails with RocketReach"
├── update_emails_from_rocketreach: "Update emails from RocketReach"
├── add_company_email: "Add company email"
├── view_all_emails: "View all emails"
└── Custom actions
```

## 📋 **STEP 6: ROCKETREACH INTEGRATION**

### **6.1 RocketReach Lookup**
```
Action: lookup_email_rocketreach
Process:
├── Queue lookup_lawyer_email_task for selected lawyers
├── Use RocketReach API to find emails
├── Create RocketReachLookup records
└── Update lawyer emails if found
```

### **6.2 RocketReach Lookup Admin**
```
URL: http://localhost:8001/admin/lawyers/rocketreachlookup/

Display columns:
├── Lawyer: "Smith & Associates"
├── Lookup Name: "John Smith"
├── Email: "john@smithlaw.com"
├── Status: "completed"
├── Confidence Score: 95.0
├── Email Validation Status: "valid"
└── Lookup Timestamp: "2025-10-24 10:35:00"
```

### **6.3 RocketReach Admin Actions**
```
Select RocketReach Lookups → Actions dropdown

Available actions:
├── retry_failed_lookups: "Retry failed lookups"
├── update_lawyer_emails: "Update lawyer emails"
└── Custom actions
```

## 📋 **STEP 7: MONITORING & TROUBLESHOOTING**

### **7.1 Progress Monitoring**
```
Real-time monitoring:
├── Source Configuration progress
├── Discovery URL status
├── Lawyer creation count
├── Error tracking
└── Performance metrics
```

### **7.2 Error Handling**
```
Error scenarios:
├── Failed Discovery URLs
├── Network timeouts
├── Parsing errors
├── API rate limits
└── Memory issues
```

### **7.3 Admin Actions for Troubleshooting**
```
Troubleshooting actions:
├── Retry failed URLs
├── Mark URLs as pending
├── Update emails from RocketReach
├── View all emails
└── Download lawyers data
```

## 🎯 **COMPLETE ADMIN WORKFLOW**

### **Workflow Summary:**
```
1. Create Source Configuration
   ├── Fill basic information
   ├── Add start URLs
   ├── Configure selectors
   └── Save configuration

2. Start Crawl Session
   ├── Select configuration
   ├── Run "Start crawl workflow" action
   ├── Monitor progress
   └── Check Discovery URLs

3. Monitor Discovery URLs
   ├── View Discovery URL list
   ├── Check status and results
   ├── Handle failed URLs
   └── Retry if needed

4. Manage Lawyer Objects
   ├── View created lawyers
   ├── Check data quality
   ├── Run RocketReach lookups
   └── Update email information

5. Export Results
   ├── Download lawyers data
   ├── Export to CSV/Excel
   └── Generate reports
```

### **Key Admin Features:**
- **One-click crawl start**
- **Real-time progress monitoring**
- **Error handling and retry**
- **Data quality tracking**
- **RocketReach integration**
- **Export capabilities**
- **Comprehensive filtering**
- **Bulk operations**

## 🚀 **ADVANCED ADMIN FEATURES**

### **Bulk Operations:**
```
- Bulk start crawl sessions
- Bulk retry failed URLs
- Bulk RocketReach lookups
- Bulk email updates
- Bulk data export
```

### **Custom Actions:**
```
- Custom crawl configurations
- Custom data extraction
- Custom email lookups
- Custom reporting
- Custom integrations
```

### **Monitoring Dashboard:**
```
- Real-time progress
- Error tracking
- Performance metrics
- Data quality scores
- System health
```

## 📋 **KẾT LUẬN**

**Admin interface cung cấp:**

1. **Simple Workflow** - One-click crawl start
2. **Real-time Monitoring** - Progress tracking
3. **Error Handling** - Retry và troubleshooting
4. **Data Management** - View và edit lawyers
5. **Integration** - RocketReach email lookup
6. **Export** - Download results
7. **Bulk Operations** - Handle multiple items
8. **Customization** - Flexible configurations

**→ Admin interface đảm bảo crawling process được quản lý dễ dàng và hiệu quả!**
