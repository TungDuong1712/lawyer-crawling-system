"""
S2: Crawl Company Info - Thu thập thông tin luật sư
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import re
from fake_useragent import UserAgent
from config import CRAWL_CONFIG


class LawyerCrawler:
    """Crawler để thu thập thông tin luật sư từ các trang web pháp lý"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_session()
        self.crawled_data = []
    
    def setup_session(self):
        """Thiết lập session với headers và cấu hình"""
        self.session.headers.update(CRAWL_CONFIG["headers"])
        self.session.timeout = CRAWL_CONFIG["timeout"]
    
    def get_random_user_agent(self) -> str:
        """Lấy random user agent"""
        return self.ua.random
    
    def crawl_lawyer_info(self, url_info: Dict) -> Dict:
        """
        Crawl thông tin luật sư từ một URL
        
        Args:
            url_info: Dict chứa thông tin URL và selectors
            
        Returns:
            Dict chứa thông tin luật sư đã crawl
        """
        url = url_info["url"]
        selectors = url_info["selectors"]
        
        print(f"Đang crawl: {url}")
        
        try:
            # Thêm delay ngẫu nhiên
            time.sleep(random.uniform(1, CRAWL_CONFIG["delay_between_requests"]))
            
            # Thay đổi user agent
            self.session.headers["User-Agent"] = self.get_random_user_agent()
            
            # Gửi request
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract thông tin luật sư
            lawyer_data = self._extract_lawyer_data(soup, selectors, url_info)
            
            print(f"✓ Crawl thành công: {len(lawyer_data)} luật sư")
            return lawyer_data
            
        except requests.RequestException as e:
            print(f"✗ Lỗi khi crawl {url}: {e}")
            return []
        except Exception as e:
            print(f"✗ Lỗi không xác định khi crawl {url}: {e}")
            return []
    
    def _extract_lawyer_data(self, soup: BeautifulSoup, selectors: Dict, url_info: Dict) -> List[Dict]:
        """Extract thông tin luật sư từ HTML"""
        lawyers = []
        
        # Tìm tất cả các element chứa thông tin luật sư
        # Thường là các card, profile, hoặc listing item
        lawyer_containers = self._find_lawyer_containers(soup)
        
        for container in lawyer_containers:
            lawyer_info = self._extract_single_lawyer(container, selectors, url_info)
            if lawyer_info:
                lawyers.append(lawyer_info)
        
        return lawyers
    
    def _find_lawyer_containers(self, soup: BeautifulSoup) -> List:
        """Tìm các container chứa thông tin luật sư"""
        # Các selector phổ biến cho lawyer containers
        container_selectors = [
            ".attorney-card",
            ".lawyer-profile", 
            ".attorney-listing",
            ".lawyer-card",
            ".attorney-info",
            ".profile-card",
            ".listing-item",
            ".attorney-item"
        ]
        
        containers = []
        for selector in container_selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                break
        
        # Nếu không tìm thấy container cụ thể, tìm theo pattern chung
        if not containers:
            # Tìm các element có chứa tên luật sư
            name_elements = soup.find_all(text=re.compile(r'(attorney|lawyer|esq|esquire)', re.I))
            for element in name_elements:
                parent = element.parent
                while parent and parent.name not in ['div', 'article', 'section']:
                    parent = parent.parent
                if parent and parent not in containers:
                    containers.append(parent)
        
        return containers[:20]  # Giới hạn 20 luật sư mỗi trang
    
    def _extract_single_lawyer(self, container, selectors: Dict, url_info: Dict) -> Optional[Dict]:
        """Extract thông tin của một luật sư"""
        try:
            lawyer_data = {
                "source_url": url_info["url"],
                "domain": url_info["domain"],
                "practice_area": url_info["practice_area"],
                "state": url_info["state"],
                "city": url_info["city"],
                "crawl_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Extract company name
            lawyer_data["company_name"] = self._extract_text(container, selectors["company_name"])
            
            # Extract phone
            lawyer_data["phone"] = self._extract_phone(container, selectors["phone"])
            
            # Extract address
            lawyer_data["address"] = self._extract_address(container, selectors["address"])
            
            # Extract practice areas
            lawyer_data["practice_areas"] = self._extract_practice_areas(container, selectors["practice_areas"])
            
            # Extract attorney details
            lawyer_data["attorney_details"] = self._extract_text(container, selectors["attorney_details"])
            
            # Extract website
            lawyer_data["website"] = self._extract_website(container, selectors["website"])
            
            # Extract email
            lawyer_data["email"] = self._extract_email(container, selectors["email"])
            
            # Chỉ trả về nếu có ít nhất tên công ty
            if lawyer_data["company_name"]:
                return lawyer_data
            
        except Exception as e:
            print(f"Lỗi khi extract thông tin luật sư: {e}")
        
        return None
    
    def _extract_text(self, container, selector: str) -> str:
        """Extract text từ element"""
        if not selector:
            return ""
        
        try:
            element = container.select_one(selector)
            if element:
                return element.get_text(strip=True)
        except:
            pass
        
        return ""
    
    def _extract_phone(self, container, selector: str) -> str:
        """Extract số điện thoại"""
        phone = self._extract_text(container, selector)
        
        # Nếu không tìm thấy qua selector, tìm trong toàn bộ text
        if not phone:
            text = container.get_text()
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            match = re.search(phone_pattern, text)
            if match:
                phone = match.group()
        
        return phone
    
    def _extract_address(self, container, selector: str) -> str:
        """Extract địa chỉ"""
        address = self._extract_text(container, selector)
        
        # Nếu không tìm thấy qua selector, tìm pattern địa chỉ
        if not address:
            text = container.get_text()
            # Pattern cho địa chỉ (số + tên đường)
            address_pattern = r'\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard)'
            match = re.search(address_pattern, text)
            if match:
                address = match.group()
        
        return address
    
    def _extract_practice_areas(self, container, selector: str) -> str:
        """Extract lĩnh vực hành nghề"""
        practice_areas = self._extract_text(container, selector)
        
        # Nếu không tìm thấy, sử dụng practice area từ URL
        if not practice_areas:
            practice_areas = container.get("practice_area", "")
        
        return practice_areas
    
    def _extract_website(self, container, selector: str) -> str:
        """Extract website"""
        website = ""
        
        try:
            if selector:
                element = container.select_one(selector)
                if element:
                    if element.name == 'a':
                        website = element.get('href', '')
                    else:
                        website = element.get_text(strip=True)
            
            # Tìm links trong container
            if not website:
                links = container.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if href.startswith('http') and not any(domain in href for domain in ['lawinfo.com', 'superlawyers.com', 'avvo.com']):
                        website = href
                        break
            
            # Clean URL
            if website and not website.startswith('http'):
                website = 'https://' + website
            
        except:
            pass
        
        return website
    
    def _extract_email(self, container, selector: str) -> str:
        """Extract email"""
        email = self._extract_text(container, selector)
        
        # Nếu không tìm thấy qua selector, tìm pattern email
        if not email:
            text = container.get_text()
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            match = re.search(email_pattern, text)
            if match:
                email = match.group()
        
        return email
    
    def crawl_multiple_urls(self, url_list: List[Dict]) -> List[Dict]:
        """Crawl nhiều URLs"""
        all_lawyers = []
        
        for i, url_info in enumerate(url_list, 1):
            print(f"\n[{i}/{len(url_list)}] Crawling {url_info['domain']} - {url_info['practice_area']}")
            
            lawyers = self.crawl_lawyer_info(url_info)
            all_lawyers.extend(lawyers)
            
            # Lưu dữ liệu tạm thời
            if lawyers:
                self.crawled_data.extend(lawyers)
        
        return all_lawyers
    
    def save_to_csv(self, filename: str = "lawyers_data.csv"):
        """Lưu dữ liệu ra file CSV"""
        if not self.crawled_data:
            print("Không có dữ liệu để lưu")
            return
        
        df = pd.DataFrame(self.crawled_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Đã lưu {len(self.crawled_data)} records vào {filename}")
    
    def get_crawl_stats(self) -> Dict:
        """Thống kê kết quả crawl"""
        if not self.crawled_data:
            return {"total": 0}
        
        df = pd.DataFrame(self.crawled_data)
        
        stats = {
            "total_lawyers": len(df),
            "by_domain": df["domain"].value_counts().to_dict(),
            "by_state": df["state"].value_counts().to_dict(),
            "by_practice_area": df["practice_area"].value_counts().to_dict(),
            "with_phone": len(df[df["phone"].notna() & (df["phone"] != "")]),
            "with_email": len(df[df["email"].notna() & (df["email"] != "")]),
            "with_website": len(df[df["website"].notna() & (df["website"] != "")])
        }
        
        return stats


if __name__ == "__main__":
    # Test crawler
    from url_generator import URLGenerator
    
    # Tạo URLs mẫu
    generator = URLGenerator()
    sample_urls = generator.generate_urls_for_domain("lawinfo")[:3]  # Test 3 URLs
    
    # Crawl
    crawler = LawyerCrawler()
    results = crawler.crawl_multiple_urls(sample_urls)
    
    # Hiển thị kết quả
    print(f"\nKết quả crawl: {len(results)} luật sư")
    for lawyer in results[:2]:  # Hiển thị 2 luật sư đầu tiên
        print(f"- {lawyer.get('company_name', 'N/A')} - {lawyer.get('phone', 'N/A')}")
    
    # Lưu dữ liệu
    crawler.save_to_csv("test_lawyers.csv")
    
    # Thống kê
    stats = crawler.get_crawl_stats()
    print(f"\nThống kê: {stats}")
