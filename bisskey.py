import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text: return "N/A"
    # تنظيف شامل لكل الإيموجي والرموز عشان يتبقى النص بس
    text = re.sub(r'[📡📶🎬📊🆔🔑🔓]|BISS • KEY FOUND', '', text)
    return text.strip()

def scrape_to_json():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"Failed. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        # separator="\n" مهم جداً عشان نفصل السطور عن بعضها
        content = soup.get_text(separator="\n")
        
        # تقسيم المحتوى لبلوكات عند كل قمر صناعي
        blocks = re.split(r'(?=\d+\.?\d?°\s?[EW])|(?=📡)', content)
        
        active_feeds = []

        for block in blocks:
            if not block.strip(): continue
            
            # 1. القمر الصناعي
            sat_match = re.search(r'(@?\s?\d+\.?\d?°\s?[EW][^\n]*)', block, re.IGNORECASE)
            
            # 2. التردد (مرن جداً)
            freq_match = re.search(r'(\d{5})\s*([VH])\s*(\d{4,5})', block)
            
            # 3. الـ ID
            id_match = re.search(r'(?:🆔|ID):\s*([^\n\r]+)', block, re.IGNORECASE)
            
            # 4. الشفرة - التعديل الجوهري هنا:
            # بيدور على المفتاح وبعده أي مسافات أو سطور جديدة (\s*) لحد ما يلاقي الـ 16 حرف
            cw_match = re.search(r'🔑\s*\n*\s*([A-F0-9\s]{16,50})', block, re.IGNORECASE | re.UNICODE)

            if freq_match and cw_match:
                # تنظيف الشفرة من أي سطر جديد وقع في النص
                clean_key = cw_match.group(1).replace("\n", "").strip()
                
                feed_item = {
                    "satellite": clean_text(sat_match.group(1)) if sat_match else "N/A",
                    "frequency": f"{freq_match.group(1)} {freq_match.group(2)} {freq_match.group(3)}",
                    "id": clean_text(id_match.group(1)) if id_match else "N/A",
                    "key": clean_key
                }
                
                if feed_item not in active_feeds:
                    active_feeds.append(feed_item)

        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Done! Found {len(active_feeds)} feeds.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
