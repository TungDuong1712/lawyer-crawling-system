# 🏛️ Hệ Thống Crawl Dữ Liệu Luật Sư - Tóm Tắt

## ✅ Đã Hoàn Thành

### 🏗️ Cấu Trúc Dự Án
```
website_joel/
├── config.py           # ✅ Cấu hình domains, selectors, settings
├── url_generator.py    # ✅ S1: Generate StartURLs
├── lawyer_crawler.py   # ✅ S2: Crawl Company Info
├── main.py            # ✅ Script chính với CLI
├── requirements.txt    # ✅ Dependencies
├── README.md          # ✅ Hướng dẫn chi tiết
├── setup.sh         # ✅ Script setup tự động
├── demo.py           # ✅ Demo hệ thống
├── run_test.py       # ✅ Test với dependencies
├── simple_test.py    # ✅ Test không cần dependencies
└── SUMMARY.md        # ✅ Tóm tắt dự án
```

### 🎯 Tính Năng Chính

#### S1: Generate StartURLs ✅
- **Input**: Domains + Cities/States + Practice Areas
- **Output**: URLs có cấu trúc chuẩn
- **Ví dụ**: `www.lawinfo.com/car-accident/new-mexico/albuquerque/`
- **Tổng số**: 600 URL combinations

#### S2: Crawl Company Info ✅
- **Company Name** - Tên công ty luật
- **Phone** - Số điện thoại
- **Address** - Địa chỉ
- **Practice Areas** - Lĩnh vực hành nghề
- **Attorney Details** - Chi tiết luật sư
- **Website** - Website công ty
- **Email** - Email liên hệ
- **Metadata** - Domain, state, city, timestamp

### 🌐 Domains Hỗ Trợ
- **lawinfo.com** - LawInfo directory
- **superlawyers.com** - Super Lawyers directory
- **avvo.com** - Avvo attorney directory

### 🗺️ Địa Lý Hỗ Trợ
- **5 States**: New Mexico, Texas, California, Florida, New York
- **20 Cities**: 4 cities mỗi bang
- **10 Practice Areas**: Car Accident, Business Litigation, Personal Injury, etc.

### 🚀 Cách Sử Dụng

#### Setup
```bash
# Cài đặt tự động
./setup.sh

# Hoặc thủ công
pip install -r requirements.txt
```

#### Test
```bash
# Test không cần dependencies
python3 simple_test.py

# Test với dependencies
python3 run_test.py

# Demo hệ thống
python3 demo.py
```

#### Crawl
```bash
# Test nhanh
python3 main.py --test

# Crawl cơ bản
python3 main.py --limit 10

# Crawl domain cụ thể
python3 main.py --domain lawinfo --limit 20

# Crawl bang cụ thể
python3 main.py --state new-mexico --limit 30

# Crawl lĩnh vực cụ thể
python3 main.py --practice-area car-accident --limit 15
```

### 📊 Thống Kê Hệ Thống
- **3 Domains** được hỗ trợ
- **5 States** với 20 cities
- **10 Practice Areas** pháp lý
- **600 URL Combinations** có thể
- **Smart Data Extraction** với regex patterns
- **Export CSV** với đầy đủ metadata

### 🔧 Tính Năng Nâng Cao
- **Random User Agents** để tránh detection
- **Delay giữa requests** để tránh rate limit
- **Error Handling** và retry logic
- **Progress Tracking** với thống kê real-time
- **Configurable Selectors** cho từng domain
- **Flexible URL Patterns** dễ mở rộng

### 📁 Output Format
Dữ liệu được lưu vào CSV với các cột:
- source_url, domain, practice_area, state, city
- company_name, phone, address, practice_areas
- attorney_details, website, email
- crawl_timestamp

## 🎉 Kết Quả

Hệ thống crawl dữ liệu luật sư đã được thiết lập hoàn chỉnh với:

✅ **S1: Generate StartURLs** - Tạo 600 URL combinations  
✅ **S2: Crawl Company Info** - Thu thập 7 trường dữ liệu chính  
✅ **Multi-domain Support** - 3 trang web pháp lý  
✅ **Smart Extraction** - Regex patterns + CSS selectors  
✅ **CLI Interface** - Dễ sử dụng với nhiều tùy chọn  
✅ **Error Handling** - Robust và reliable  
✅ **Documentation** - Hướng dẫn chi tiết  
✅ **Testing** - Test suite đầy đủ  
✅ **Demo** - Ví dụ sử dụng thực tế  

## 🚀 Sẵn Sàng Sử Dụng!

Hệ thống đã sẵn sàng để crawl dữ liệu luật sư từ các trang web pháp lý hàng đầu. Chỉ cần chạy `./setup.sh` và bắt đầu crawl!

---

**Happy Crawling! 🕷️⚖️**
