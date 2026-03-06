import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text: return "N/A"
    # تنظيف النصوص من الإيموشنات والرموز الغريبة
    text = text.encode('ascii', 'ignore').decode('ascii')
    # إزالة الكلمات الزائدة اللي بتظهر في بداية الصفحة
    junk_words = ["LIVE FEED", "SHOW OFF FEEDS: OFF", "SHOW BISS-2: OFF", "SCAN STATUS:", "ACTIVE"]
    for word in junk_words:
        text = text.replace(word, "")
    # إزالة المسافات الزائدة والأسطر الفارغة
    return text.strip()

def scrape_to_json():
    scraper = cloudscraper.create_scraper() 
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(separator="\n")
        
        # النمط الحالي بتاعك
        pattern = re.compile(
            r'(?P<sat>[^\n]*?@\s?\d+\.\d°[EW]).*?'        
            r'(?P<freq>\d{5}\s+[VH]\s+\d{4,5}).*?'     
            r'ID:\s*(?P<id>.*?)\n.*?'                  
            r'#CW:\s*(?P<cw>[A-F0-9 ]{17,24})',        
            re.DOTALL | re.IGNORECASE
        )
        
        matches = pattern.finditer(content)
        
        active_feeds = []
        for match in matches:
            start_pos = match.start()
            context = content[max(0, start_pos-300):match.end()]
            
            # التعديل الذهبي:
            # 1. لازم يكون فيه KEY FOUND
            # 2. لازم ميكنش CLEAR (يعني مش مفتوحة)
            # 3. لازم ميكنش NO KEY (يعني الموقع لسه منشرش الشفرة)
            if "KEY FOUND" in context.upper() and \
               "CLEAR" not in context.upper() and \
               "NO KEY" not in context.upper():
                
                raw_sat = match.group('sat')
                clean_sat = raw_sat.split('\n')[-1].strip()
                
                feed_item = {
                    "satellite": clean_text(clean_sat),
                    "frequency": clean_text(match.group('freq')),
                    "id": clean_text(match.group('id')),
                    "key": clean_text(match.group('cw'))
                }
                
                if feed_item not in active_feeds:
                    active_feeds.append(feed_item)
        
        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Success! Found {len(active_feeds)} valid entries.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
