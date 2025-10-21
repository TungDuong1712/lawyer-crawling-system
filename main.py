"""
Script chính để chạy hệ thống crawl dữ liệu luật sư
"""

import argparse
import time
from url_generator import URLGenerator
from lawyer_crawler import LawyerCrawler
from config import LAW_DOMAINS, STATES_CITIES


def main():
    """Hàm main để chạy hệ thống crawl"""
    
    parser = argparse.ArgumentParser(description="Hệ thống crawl dữ liệu luật sư")
    parser.add_argument("--domain", help="Domain cụ thể để crawl (lawinfo, superlawyers, avvo)")
    parser.add_argument("--state", help="Bang cụ thể để crawl")
    parser.add_argument("--practice-area", help="Lĩnh vực pháp lý cụ thể")
    parser.add_argument("--limit", type=int, default=10, help="Giới hạn số URLs để crawl")
    parser.add_argument("--output", default="lawyers_data.csv", help="Tên file output")
    parser.add_argument("--test", action="store_true", help="Chạy test với 3 URLs")
    
    args = parser.parse_args()
    
    print("🏛️ HỆ THỐNG CRAWL DỮ LIỆU LUẬT SƯ")
    print("=" * 50)
    
    # Khởi tạo components
    url_generator = URLGenerator()
    crawler = LawyerCrawler()
    
    # Tạo danh sách URLs
    print("📋 Đang tạo danh sách URLs...")
    
    if args.test:
        # Test mode - chỉ crawl 3 URLs
        urls = url_generator.generate_urls()[:3]
        print(f"🧪 Test mode: {len(urls)} URLs")
    else:
        # Tạo URLs theo tham số
        if args.domain:
            urls = url_generator.generate_urls_for_domain(args.domain)
        elif args.state:
            urls = url_generator.generate_urls_for_state(args.state)
        else:
            urls = url_generator.generate_urls()
        
        # Lọc theo practice area nếu có
        if args.practice_area:
            urls = [url for url in urls if url["practice_area"] == args.practice_area]
        
        # Giới hạn số URLs
        urls = urls[:args.limit]
    
    print(f"📊 Tổng số URLs: {len(urls)}")
    
    # Hiển thị thông tin URLs
    domains = set(url["domain"] for url in urls)
    states = set(url["state"] for url in urls)
    practice_areas = set(url["practice_area"] for url in urls)
    
    print(f"🌐 Domains: {', '.join(domains)}")
    print(f"🗺️  States: {', '.join(states)}")
    print(f"⚖️  Practice Areas: {', '.join(practice_areas)}")
    
    # Bắt đầu crawl
    print(f"\n🚀 Bắt đầu crawl {len(urls)} URLs...")
    start_time = time.time()
    
    try:
        results = crawler.crawl_multiple_urls(urls)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Hoàn thành crawl trong {duration:.2f} giây")
        print(f"📈 Kết quả: {len(results)} luật sư")
        
        # Lưu dữ liệu
        if results:
            crawler.save_to_csv(args.output)
            
            # Hiển thị thống kê
            stats = crawler.get_crawl_stats()
            print(f"\n📊 THỐNG KÊ:")
            print(f"   • Tổng luật sư: {stats['total_lawyers']}")
            print(f"   • Có số điện thoại: {stats['with_phone']}")
            print(f"   • Có email: {stats['with_email']}")
            print(f"   • Có website: {stats['with_website']}")
            
            print(f"\n📁 Dữ liệu đã lưu vào: {args.output}")
        else:
            print("❌ Không crawl được dữ liệu nào")
    
    except KeyboardInterrupt:
        print("\n⏹️  Dừng crawl theo yêu cầu người dùng")
        if crawler.crawled_data:
            crawler.save_to_csv(args.output)
            print(f"💾 Đã lưu {len(crawler.crawled_data)} records vào {args.output}")
    
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        if crawler.crawled_data:
            crawler.save_to_csv(args.output)
            print(f"💾 Đã lưu dữ liệu tạm thời vào {args.output}")


def show_help():
    """Hiển thị hướng dẫn sử dụng"""
    print("""
🏛️ HỆ THỐNG CRAWL DỮ LIỆU LUẬT SƯ
=====================================

CÁCH SỬ DỤNG:

1. Test nhanh (3 URLs):
   python main.py --test

2. Crawl tất cả:
   python main.py --limit 50

3. Crawl domain cụ thể:
   python main.py --domain lawinfo --limit 20

4. Crawl bang cụ thể:
   python main.py --state new-mexico --limit 30

5. Crawl lĩnh vực cụ thể:
   python main.py --practice-area car-accident --limit 15

6. Crawl với output file tùy chỉnh:
   python main.py --output my_lawyers.csv --limit 25

THAM SỐ:
  --domain        Domain để crawl (lawinfo, superlawyers, avvo)
  --state         Bang để crawl (new-mexico, texas, california, etc.)
  --practice-area Lĩnh vực pháp lý (car-accident, business-litigation, etc.)
  --limit         Giới hạn số URLs (mặc định: 10)
  --output        Tên file output (mặc định: lawyers_data.csv)
  --test          Chạy test với 3 URLs

VÍ DỤ:
  python main.py --domain lawinfo --state new-mexico --practice-area car-accident --limit 10
    """)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1 or "--help" in sys.argv or "-h" in sys.argv:
        show_help()
    else:
        main()
