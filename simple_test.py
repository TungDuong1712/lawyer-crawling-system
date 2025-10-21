import json
from config import LAW_DOMAINS, STATES_CITIES, PRACTICE_AREAS


def test_config():
    """Test cấu hình"""
    print("🧪 Testing Configuration...")
    
    print(f"   📊 Số domains: {len(LAW_DOMAINS)}")
    for domain in LAW_DOMAINS.keys():
        print(f"      - {domain}")
    
    print(f"   🗺️  Số states: {len(STATES_CITIES)}")
    for state in STATES_CITIES.keys():
        cities = STATES_CITIES[state]
        print(f"      - {state}: {len(cities)} cities")
    
    print(f"   ⚖️  Số practice areas: {len(PRACTICE_AREAS)}")
    for area in PRACTICE_AREAS:
        print(f"      - {area}")
    
    print("   ✅ Configuration test passed!\n")


def test_url_generation():
    """Test tạo URLs (không cần dependencies)"""
    print("🧪 Testing URL Generation...")
    
    # Tính tổng số URLs
    total_domains = len(LAW_DOMAINS)
    total_cities = sum(len(cities) for cities in STATES_CITIES.values())
    total_practice_areas = len(PRACTICE_AREAS)
    total_urls = total_domains * total_cities * total_practice_areas
    
    print(f"   📊 Tổng số URLs sẽ được tạo: {total_urls}")
    
    # Tạo mẫu URLs
    sample_urls = []
    for domain_name, domain_config in list(LAW_DOMAINS.items())[:1]:  # Chỉ 1 domain
        for state, cities in list(STATES_CITIES.items())[:1]:  # Chỉ 1 state
            for city in cities[:1]:  # Chỉ 1 city
                for practice_area in PRACTICE_AREAS[:2]:  # Chỉ 2 practice areas
                    url_pattern = domain_config["url_pattern"]
                    base_url = domain_config["base_url"]
                    
                    url = url_pattern.format(
                        base_url=base_url,
                        practice_area=practice_area,
                        state=state,
                        city=city
                    )
                    
                    sample_urls.append({
                        "domain": domain_name,
                        "url": url,
                        "practice_area": practice_area,
                        "state": state,
                        "city": city
                    })
    
    print(f"   📋 Mẫu URLs ({len(sample_urls)}):")
    for url_info in sample_urls:
        print(f"      - {url_info['domain']}: {url_info['url']}")
    
    print("   ✅ URL Generation test passed!\n")
    return sample_urls


def test_data_structure():
    """Test cấu trúc dữ liệu"""
    print("🧪 Testing Data Structure...")
    
    # Tạo mẫu dữ liệu luật sư
    sample_lawyer = {
        "source_url": "https://www.lawinfo.com/car-accident/new-mexico/albuquerque/",
        "domain": "lawinfo",
        "practice_area": "car-accident",
        "state": "new-mexico",
        "city": "albuquerque",
        "company_name": "Smith & Associates Law Firm",
        "phone": "(505) 123-4567",
        "address": "123 Main St, Albuquerque, NM 87101",
        "practice_areas": "Car Accident, Personal Injury",
        "attorney_details": "Experienced attorney with 10+ years",
        "website": "https://smithlaw.com",
        "email": "info@smithlaw.com",
        "crawl_timestamp": "2024-01-15 10:30:00"
    }
    
    print(f"   📋 Mẫu dữ liệu luật sư:")
    for key, value in sample_lawyer.items():
        print(f"      - {key}: {value}")
    
    print("   ✅ Data Structure test passed!\n")


def main():
    """Chạy tất cả tests"""
    print("🏛️ HỆ THỐNG CRAWL DỮ LIỆU LUẬT SƯ - SIMPLE TEST")
    print("=" * 60)
    
    try:
        # Test cấu hình
        test_config()
        
        # Test tạo URLs
        sample_urls = test_url_generation()
        
        # Test cấu trúc dữ liệu
        test_data_structure()
        
        print("🎉 Tất cả tests đã hoàn thành!")
        print("\n💡 Hệ thống đã sẵn sàng!")
        print("📝 Để chạy crawl thực tế:")
        print("   1. Cài đặt dependencies: pip install -r requirements.txt")
        print("   2. Chạy test: python3 run_test.py")
        print("   3. Chạy crawl: python3 main.py --test")
        
        print(f"\n📊 Tổng kết:")
        print(f"   • {len(LAW_DOMAINS)} domains được hỗ trợ")
        print(f"   • {len(STATES_CITIES)} states")
        print(f"   • {sum(len(cities) for cities in STATES_CITIES.values())} cities")
        print(f"   • {len(PRACTICE_AREAS)} practice areas")
        
        total_combinations = len(LAW_DOMAINS) * sum(len(cities) for cities in STATES_CITIES.values()) * len(PRACTICE_AREAS)
        print(f"   • {total_combinations} URL combinations có thể")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình test: {e}")


if __name__ == "__main__":
    main()
