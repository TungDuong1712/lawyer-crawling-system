"""
Script test nhanh hệ thống crawl
"""

from url_generator import URLGenerator
from lawyer_crawler import LawyerCrawler


def test_url_generator():
    """Test URL Generator"""
    print("🧪 Testing URL Generator...")
    
    generator = URLGenerator()
    
    # Test tổng số URLs
    total_urls = generator.get_total_urls_count()
    print(f"   📊 Tổng số URLs: {total_urls}")
    
    # Test tạo URLs cho domain cụ thể
    lawinfo_urls = generator.generate_urls_for_domain("lawinfo")
    print(f"   🌐 LawInfo URLs: {len(lawinfo_urls)}")
    
    # Test tạo URLs cho bang cụ thể
    nm_urls = generator.generate_urls_for_state("new-mexico")
    print(f"   🗺️  New Mexico URLs: {len(nm_urls)}")
    
    # Hiển thị mẫu URLs
    sample_urls = generator.generate_urls()[:3]
    print(f"   📋 Mẫu URLs:")
    for url_info in sample_urls:
        print(f"      - {url_info['domain']}: {url_info['url']}")
    
    print("   ✅ URL Generator test passed!\n")
    return sample_urls


def test_lawyer_crawler(sample_urls):
    """Test Lawyer Crawler"""
    print("🧪 Testing Lawyer Crawler...")
    
    crawler = LawyerCrawler()
    
    # Test crawl 1 URL
    if sample_urls:
        test_url = sample_urls[0]
        print(f"   🕷️  Testing crawl: {test_url['url']}")
        
        try:
            results = crawler.crawl_lawyer_info(test_url)
            print(f"   📈 Kết quả: {len(results)} luật sư")
            
            if results:
                lawyer = results[0]
                print(f"   👤 Mẫu luật sư:")
                print(f"      - Tên: {lawyer.get('company_name', 'N/A')}")
                print(f"      - Phone: {lawyer.get('phone', 'N/A')}")
                print(f"      - Email: {lawyer.get('email', 'N/A')}")
            
            # Test lưu CSV
            crawler.save_to_csv("test_output.csv")
            print(f"   💾 Đã lưu test data vào test_output.csv")
            
            # Test thống kê
            stats = crawler.get_crawl_stats()
            print(f"   📊 Thống kê: {stats}")
            
        except Exception as e:
            print(f"   ❌ Lỗi khi test crawl: {e}")
    
    print("   ✅ Lawyer Crawler test completed!\n")


def main():
    """Chạy tất cả tests"""
    print("🏛️ HỆ THỐNG CRAWL DỮ LIỆU LUẬT SƯ - TEST")
    print("=" * 50)
    
    try:
        # Test URL Generator
        sample_urls = test_url_generator()
        
        # Test Lawyer Crawler
        test_lawyer_crawler(sample_urls)
        
        print("🎉 Tất cả tests đã hoàn thành!")
        print("💡 Để chạy crawl thực tế, sử dụng: python main.py --test")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình test: {e}")
        print("🔧 Hãy kiểm tra:")
        print("   - Đã cài đặt dependencies: pip install -r requirements.txt")
        print("   - Internet connection ổn định")
        print("   - Cấu hình trong config.py đúng")


if __name__ == "__main__":
    main()
