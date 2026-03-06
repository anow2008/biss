import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text: return "N/A"
    # تحويل النص لـ ASCII لتجنب مشاكل الرموز التعبيرية (Emoji)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # قائمة الكلمات التي سيتم مسحها من النصوص المستخرجة
    junk_words = ["LIVE FEED", "SHOW OFF FEEDS: OFF", "SHOW BISS-2: OFF", "SCAN STATUS:", "ACTIVE"]
    for word in junk_words:
        text = text.replace(word, "")
    return text.strip()

def scrape_to_json():
    scraper = cloudscraper.create_scraper() 
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"Failed to load page. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        # استخراج النص مع الحفاظ على الفواصل
        content = soup.get_text(separator="\n")
        # تنظيف الأسطر الفارغة الزائدة التي تسبب مشاكل في البحث
        content = re.sub(r'\n\s*\n', '\n', content)

        # 1. البحث عن كل الأقمار كعلامات لبداية كل بلوك بيانات
        # بيبحث عن أي نص يحتوي على @ وبعده درجات مدارية
        sat_pattern = re.compile(r'([^\n]*?@\s?\d+\.?\d?°\s?[EW])')
        sat_matches = list(sat_pattern.finditer(content))
        
        active_feeds = []

        # 2. تقسيم الصفحة لمقاطع (Blocks)
        for i in range(len(sat_matches)):
            start = sat_matches[i].start()
            # نهاية المقطع هي بداية القمر اللي بعده، أو آخر الصفحة
            end = sat_matches[i+1].start() if i+1 < len(sat_matches) else len(content)
            block = content[start:end]

            # 3. الفلترة الذكية للمقطع:
            # - لازم يحتوي على KEY FOUND
            # - لازم ميكونش CLEAR أو FTA أو NO KEY
            block_upper = block.upper()
            if "KEY FOUND" in block_upper and \
               "CLEAR" not in block_upper and \
               "(FTA)" not in block_upper and \
               "NO KEY" not in block_upper:
                
                # البحث عن التردد (النمط: 5 أرقام + V/H + 4 أو 5 أرقام)
                freq_match = re.search(r'(\d{5}\s+[VH]\s+\d{4,5})', block)
                
                # البحث عن الـ ID (بيأخد كل اللي بعد كلمة ID: لحد آخر السطر)
                id_match = re.search(r'ID:\s*(.*)', block, re.IGNORECASE)
                
                # البحث عن الشفرة (بيبحث عن CW: أو #CW: ويأخد الحروف والأرقام والمسافات بعدها)
                cw_match = re.search(r'(?:#CW|CW):\s*([A-F0-9\s]{16,32})', block, re.IGNORECASE)

                # لو لقى التردد والشفرة (أهم حاجتين)، بيضيفهم للقائمة
                if freq_match and cw_match:
                    feed_item = {
                        "satellite": clean_text(sat_matches[i].group(1)),
                        "frequency": clean_text(freq_match.group(1)),
                        "id": clean_text(id_match.group(1)) if id_match else "N/A",
                        "key": clean_text(cw_match.group(1))
                    }
                    
                    # منع التكرار
                    if feed_item not in active_feeds:
                        active_feeds.append(feed_item)

        # 4. حفظ النتائج في ملف JSON
        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Success! Total valid feeds found: {len(active_feeds)}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    scrape_to_json()
