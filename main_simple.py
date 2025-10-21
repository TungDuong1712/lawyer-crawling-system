"""
Simple main script (no dependencies) to demo crawling system
"""

import argparse
import time
from url_generator import URLGenerator
from config import LAW_DOMAINS, STATES_CITIES


def simulate_crawl(url_info):
    """Simulate crawling (not actual crawling)"""
    print(f"🕷️  Crawling: {url_info['url']}")
    
    # Simulate delay
    time.sleep(0.5)
    
    # Generate sample data
    sample_lawyers = [
        {
            "source_url": url_info["url"],
            "domain": url_info["domain"],
            "practice_area": url_info["practice_area"],
            "state": url_info["state"],
            "city": url_info["city"],
            "company_name": f"Sample Law Firm {url_info['city'].title()}",
            "phone": f"(555) {url_info['city'][:3].upper()}-{url_info['practice_area'][:4].upper()}",
            "address": f"123 {url_info['city'].title()} St, {url_info['state'].title()}",
            "practice_areas": url_info["practice_area"].replace("-", " ").title(),
            "attorney_details": f"Experienced {url_info['practice_area']} attorney",
            "website": f"https://{url_info['city']}law.com",
            "email": f"info@{url_info['city']}law.com",
            "crawl_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    print(f"   ✅ Tìm thấy {len(sample_lawyers)} luật sư")
    return sample_lawyers


def main():
    """Main function to run crawling system"""
    
    parser = argparse.ArgumentParser(description="Lawyer data crawling system (Demo)")
    parser.add_argument("--domain", help="Specific domain to crawl (lawinfo, superlawyers, avvo)")
    parser.add_argument("--state", help="Specific state to crawl")
    parser.add_argument("--practice-area", help="Specific legal practice area")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of URLs to crawl")
    parser.add_argument("--output", default="lawyers_data.csv", help="Output filename")
    parser.add_argument("--test", action="store_true", help="Run test with 3 URLs")
    
    args = parser.parse_args()
    
    print("🏛️ LAWYER DATA CRAWLING SYSTEM (DEMO)")
    print("=" * 50)
    
    # Initialize components
    url_generator = URLGenerator()
    
    # Generate URL list
    print("📋 Generating URL list...")
    
    if args.test:
        # Test mode - crawl 3 URLs only
        urls = url_generator.generate_urls()[:3]
        print(f"🧪 Test mode: {len(urls)} URLs")
    else:
        # Generate URLs based on parameters
        if args.domain:
            urls = url_generator.generate_urls_for_domain(args.domain)
        elif args.state:
            urls = url_generator.generate_urls_for_state(args.state)
        else:
            urls = url_generator.generate_urls()
        
        # Filter by practice area if specified
        if args.practice_area:
            urls = [url for url in urls if url["practice_area"] == args.practice_area]
        
        # Limit number of URLs
        urls = urls[:args.limit]
    
    print(f"📊 Total URLs: {len(urls)}")
    
    # Display URL information
    domains = set(url["domain"] for url in urls)
    states = set(url["state"] for url in urls)
    practice_areas = set(url["practice_area"] for url in urls)
    
    print(f"🌐 Domains: {', '.join(domains)}")
    print(f"🗺️  States: {', '.join(states)}")
    print(f"⚖️  Practice Areas: {', '.join(practice_areas)}")
    
    # Start crawling (simulation)
    print(f"\n🚀 Starting crawl of {len(urls)} URLs...")
    start_time = time.time()
    
    all_lawyers = []
    
    try:
        for i, url_info in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Crawling {url_info['domain']} - {url_info['practice_area']}")
            
            lawyers = simulate_crawl(url_info)
            all_lawyers.extend(lawyers)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Crawl completed in {duration:.2f} seconds")
        print(f"📈 Results: {len(all_lawyers)} lawyers")
        
        # Display sample data
        if all_lawyers:
            print(f"\n📋 Sample data:")
            for i, lawyer in enumerate(all_lawyers[:3], 1):
                print(f"{i}. {lawyer['company_name']}")
                print(f"   📞 Phone: {lawyer['phone']}")
                print(f"   📧 Email: {lawyer['email']}")
                print(f"   🌐 Website: {lawyer['website']}")
                print(f"   📍 Address: {lawyer['address']}")
                print(f"   ⚖️  Practice: {lawyer['practice_areas']}")
                print()
            
            # Save sample data
            print(f"💾 Generated sample data for {len(all_lawyers)} lawyers")
            print(f"📁 Data will be saved to: {args.output}")
            
            # Statistics
            domains_count = {}
            states_count = {}
            practice_areas_count = {}
            
            for lawyer in all_lawyers:
                domain = lawyer['domain']
                state = lawyer['state']
                practice = lawyer['practice_area']
                
                domains_count[domain] = domains_count.get(domain, 0) + 1
                states_count[state] = states_count.get(state, 0) + 1
                practice_areas_count[practice] = practice_areas_count.get(practice, 0) + 1
            
            print(f"\n📊 STATISTICS:")
            print(f"   • Total lawyers: {len(all_lawyers)}")
            print(f"   • By domain: {domains_count}")
            print(f"   • By state: {states_count}")
            print(f"   • By practice area: {practice_areas_count}")
        else:
            print("❌ No data crawled")
    
    except KeyboardInterrupt:
        print("\n⏹️  Stopped crawling by user request")
        print(f"💾 Crawled {len(all_lawyers)} lawyers")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def show_help():
    """Show usage instructions"""
    print("""
🏛️ HỆ THỐNG CRAWL DỮ LIỆU LUẬT SƯ (DEMO)
==========================================

CÁCH SỬ DỤNG:

1. Test nhanh (3 URLs):
   python3 main_simple.py --test

2. Crawl tất cả:
   python3 main_simple.py --limit 50

3. Crawl domain cụ thể:
   python3 main_simple.py --domain lawinfo --limit 20

4. Crawl bang cụ thể:
   python3 main_simple.py --state new-mexico --limit 30

5. Crawl lĩnh vực cụ thể:
   python3 main_simple.py --practice-area car-accident --limit 15

6. Crawl với output file tùy chỉnh:
   python3 main_simple.py --output my_lawyers.csv --limit 25

THAM SỐ:
  --domain        Domain để crawl (lawinfo, superlawyers, avvo)
  --state         Bang để crawl (new-mexico, texas, california, etc.)
  --practice-area Lĩnh vực pháp lý (car-accident, business-litigation, etc.)
  --limit         Giới hạn số URLs (mặc định: 10)
  --output        Tên file output (mặc định: lawyers_data.csv)
  --test          Chạy test với 3 URLs

VÍ DỤ:
  python3 main_simple.py --domain lawinfo --state new-mexico --practice-area car-accident --limit 10

LƯU Ý: Đây là phiên bản demo mô phỏng crawl. 
Để crawl thực tế, cần cài đặt dependencies và sử dụng main.py
    """)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1 or "--help" in sys.argv or "-h" in sys.argv:
        show_help()
    else:
        main()
