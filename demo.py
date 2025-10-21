"""
Demo hệ thống crawl dữ liệu luật sư
"""

from url_generator import URLGenerator
import json


def demo_url_generation():
    """Demo tạo URLs"""
    print("🔗 DEMO: Tạo danh sách URLs")
    print("-" * 40)
    
    generator = URLGenerator()
    
    # Demo tạo URLs cho domain cụ thể
    print("1. URLs cho LawInfo domain:")
    lawinfo_urls = generator.generate_urls_for_domain("lawinfo")
    print(f"   📊 Tổng số: {len(lawinfo_urls)} URLs")
    
    # Hiển thị 3 URLs đầu tiên
    for i, url_info in enumerate(lawinfo_urls[:3], 1):
        print(f"   {i}. {url_info['url']}")
        print(f"      Practice: {url_info['practice_area']}")
        print(f"      Location: {url_info['city']}, {url_info['state']}")
        print()
    
    # Demo tạo URLs cho bang cụ thể
    print("2. URLs cho New Mexico:")
    nm_urls = generator.generate_urls_for_state("new-mexico")
    print(f"   📊 Tổng số: {len(nm_urls)} URLs")
    
    # Hiển thị 2 URLs đầu tiên
    for i, url_info in enumerate(nm_urls[:2], 1):
        print(f"   {i}. {url_info['url']}")
        print(f"      Domain: {url_info['domain']}")
        print(f"      Practice: {url_info['practice_area']}")
        print()
    
    return lawinfo_urls[:5]  # Trả về 5 URLs để demo


def demo_data_structure():
    """Demo cấu trúc dữ liệu"""
    print("📊 DEMO: Cấu trúc dữ liệu luật sư")
    print("-" * 40)
    
    # Mẫu dữ liệu luật sư
    sample_lawyers = [
        {
            "source_url": "https://www.lawinfo.com/car-accident/new-mexico/albuquerque/",
            "domain": "lawinfo",
            "practice_area": "car-accident",
            "state": "new-mexico",
            "city": "albuquerque",
            "company_name": "Smith & Associates Law Firm",
            "phone": "(505) 123-4567",
            "address": "123 Main St, Albuquerque, NM 87101",
            "practice_areas": "Car Accident, Personal Injury",
            "attorney_details": "Experienced attorney with 10+ years in car accident cases",
            "website": "https://smithlaw.com",
            "email": "info@smithlaw.com",
            "crawl_timestamp": "2024-01-15 10:30:00"
        },
        {
            "source_url": "https://attorneys.superlawyers.com/business-litigation/texas/houston/",
            "domain": "superlawyers",
            "practice_area": "business-litigation",
            "state": "texas",
            "city": "houston",
            "company_name": "Johnson Legal Group",
            "phone": "(713) 555-0123",
            "address": "456 Business Ave, Houston, TX 77002",
            "practice_areas": "Business Litigation, Corporate Law",
            "attorney_details": "Board certified in business litigation",
            "website": "https://johnsonlegal.com",
            "email": "contact@johnsonlegal.com",
            "crawl_timestamp": "2024-01-15 10:35:00"
        }
    ]
    
    print("Mẫu dữ liệu luật sư:")
    for i, lawyer in enumerate(sample_lawyers, 1):
        print(f"\n{i}. {lawyer['company_name']}")
        print(f"   📞 Phone: {lawyer['phone']}")
        print(f"   📧 Email: {lawyer['email']}")
        print(f"   🌐 Website: {lawyer['website']}")
        print(f"   📍 Address: {lawyer['address']}")
        print(f"   ⚖️  Practice: {lawyer['practice_areas']}")
        print(f"   🏢 Domain: {lawyer['domain']}")
        print(f"   📅 Crawled: {lawyer['crawl_timestamp']}")


def demo_usage_examples():
    """Demo các cách sử dụng"""
    print("\n🚀 DEMO: Các cách sử dụng hệ thống")
    print("-" * 40)
    
    examples = [
        {
            "title": "Test nhanh (3 URLs)",
            "command": "python3 main.py --test",
            "description": "Chạy test với 3 URLs để kiểm tra hệ thống"
        },
        {
            "title": "Crawl domain cụ thể",
            "command": "python3 main.py --domain lawinfo --limit 20",
            "description": "Crawl 20 URLs từ LawInfo domain"
        },
        {
            "title": "Crawl bang cụ thể",
            "command": "python3 main.py --state new-mexico --limit 30",
            "description": "Crawl 30 URLs từ New Mexico"
        },
        {
            "title": "Crawl lĩnh vực cụ thể",
            "command": "python3 main.py --practice-area car-accident --limit 15",
            "description": "Crawl 15 URLs về car accident"
        },
        {
            "title": "Crawl với output tùy chỉnh",
            "command": "python3 main.py --output my_lawyers.csv --limit 25",
            "description": "Lưu kết quả vào file my_lawyers.csv"
        },
        {
            "title": "Crawl kết hợp nhiều tham số",
            "command": "python3 main.py --domain lawinfo --state new-mexico --practice-area car-accident --limit 10",
            "description": "Crawl 10 URLs từ LawInfo, New Mexico, car accident"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}")
        print(f"   💻 Command: {example['command']}")
        print(f"   📝 Mô tả: {example['description']}")
        print()


def demo_statistics():
    """Demo thống kê"""
    print("\n📈 DEMO: Thống kê hệ thống")
    print("-" * 40)
    
    generator = URLGenerator()
    
    # Thống kê tổng quan
    total_urls = generator.get_total_urls_count()
    domains = len(generator.domains)
    states = len(generator.states_cities)
    cities = sum(len(cities) for cities in generator.states_cities.values())
    practice_areas = len(generator.practice_areas)
    
    print(f"📊 Tổng quan hệ thống:")
    print(f"   • Domains: {domains}")
    print(f"   • States: {states}")
    print(f"   • Cities: {cities}")
    print(f"   • Practice Areas: {practice_areas}")
    print(f"   • Total URL Combinations: {total_urls}")
    
    # Thống kê theo domain
    print(f"\n🌐 URLs theo domain:")
    for domain_name in generator.domains.keys():
        domain_urls = generator.generate_urls_for_domain(domain_name)
        print(f"   • {domain_name}: {len(domain_urls)} URLs")
    
    # Thống kê theo bang
    print(f"\n🗺️  URLs theo bang:")
    for state_name in generator.states_cities.keys():
        state_urls = generator.generate_urls_for_state(state_name)
        print(f"   • {state_name}: {len(state_urls)} URLs")


def main():
    """Chạy demo hoàn chỉnh"""
    print("🏛️ HỆ THỐNG CRAWL DỮ LIỆU LUẬT SƯ - DEMO")
    print("=" * 60)
    
    try:
        # Demo tạo URLs
        sample_urls = demo_url_generation()
        
        # Demo cấu trúc dữ liệu
        demo_data_structure()
        
        # Demo cách sử dụng
        demo_usage_examples()
        
        # Demo thống kê
        demo_statistics()
        
        print("\n🎉 Demo hoàn thành!")
        print("\n💡 Bước tiếp theo:")
        print("   1. Cài đặt dependencies: pip install -r requirements.txt")
        print("   2. Chạy test: python3 run_test.py")
        print("   3. Chạy crawl: python3 main.py --test")
        print("   4. Xem hướng dẫn: python3 main.py --help")
        
    except Exception as e:
        print(f"❌ Lỗi trong demo: {e}")


if __name__ == "__main__":
    main()
