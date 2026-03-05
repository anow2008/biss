import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    # تنظيف النص من الإيموشنات والرموز الغريبة
    if not text: return "N/A"
    return text.encode('ascii', 'ignore').decode('ascii').strip()

def scrape_to_json():
    scraper = cloudscraper.create_scraper() 
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(separator="\n")
        
        # نمط البحث عن البيانات الأربعة
        pattern = re.compile(
            r'(?P<sat>.*?@.*?\d+\.\d°[EW]).*?'        # 1. اسم القمر
            r'(?P<freq>\d{5}\s+[VH]\s+\d{4,5}).*?'     # 2. التردد
            r'ID:\s*(?P<id>.*?)\n.*?'                  # 3. ID
            r'#CW:\s*(?P<cw>[A-F0-9 ]{17,24})',        # 4. الشفرة
            re.DOTALL | re.IGNORECASE
        )
        
        matches = pattern.finditer(content)
        
        active_feeds = []
        for match in matches:
            start_pos = match.start()
            context = content[max(0, start_pos-300):match.end()]
            
            # التأكد أن الشفرة شغالة (KEY FOUND)
            if "KEY FOUND" in context.upper():
                # وضع كل معلومة في حقل مستقل ونظيف
                feed_item = {
                    "satellite": clean_text(match.group('sat')),
                    "frequency": clean_text(match.group('freq')),
                    "id": clean_text(match.group('id')),
                    "key": clean_text(match.group('cw'))
                }
                
                if feed_item not in active_feeds:
                    active_feeds.append(feed_item)
        
        # حفظ الملف بالاسم bisskeys.json
        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Success! Extracted {len(active_feeds)} structured entries.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
