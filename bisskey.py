import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text: return "N/A"
    clean = re.sub(r'[📡📶🎬📊🆔🔑🔓]|BISS • KEY FOUND', '', text)
    return clean.strip()

def format_key(raw_key):
    # تنظيف الشفرة من أي مسافات أو سطور جديدة أولاً
    clean_key = raw_key.strip().replace("\n", "").replace(" ", "")
    # تقسيم الشفرة كل حرفين ووضع مسافة بينهم
    return " ".join(clean_key[i:i+2] for i in range(0, len(clean_key), 2))

def scrape_to_json():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"فشل الوصول للموقع: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        active_feeds = []

        elements = soup.find_all(['div', 'p', 'article'])

        for element in elements:
            block_text = element.get_text(separator="\n")
            
            if "KEY FOUND" in block_text:
                freq_match = re.search(r'(\d{5})\s*([VH])\s*(\d{4,5})', block_text)
                cw_match = re.search(r'(?:🔑|CW:?)\s*([A-F0-9\s]{16,50})', block_text, re.IGNORECASE)

                if freq_match and cw_match:
                    sat_match = re.search(r'(\d+\.?\d?°\s?[EW])', block_text)
                    id_match = re.search(r'(?:🆔|ID:?)\s*([^\n\r]+)', block_text)
                    
                    sat_name = sat_match.group(1) if sat_match else "Unknown"
                    channel_id = clean_text(id_match.group(1)) if id_match else "N/A"
                    
                    # استخدام الدالة الجديدة لتنسيق الشفرة بمسافات
                    formatted_key = format_key(cw_match.group(1))
                    
                    feed_item = {
                        "satellite": sat_name,
                        "frequency": f"{freq_match.group(1)} {freq_match.group(2)} {freq_match.group(3)}",
                        "id": channel_id,
                        "key": formatted_key
                    }
                    
                    if feed_item not in active_feeds:
                        active_feeds.append(feed_item)

        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"تم بنجاح! تم العثور على {len(active_feeds)} تردد مشفر بالتنسيق الجديد.")

    except Exception as e:
        print(f"حدث خطأ: {e}")

if __name__ == "__main__":
    scrape_to_json()
