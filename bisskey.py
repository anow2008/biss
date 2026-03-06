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
        
        # نمط (Regex) مرن جداً للتعامل مع اختلاف المسافات وتنسيق الترددات والشفرات
        pattern = re.compile(
            r'(?P<sat>[^\n]*?@\s?\d+\.?\d?°\s?[EW]).*?'    # جعل النقطة والدرجة اختيارية لضمان لقط كل الأقمار
            r'(?P<freq>\d{5}\s+[VH]\s+\d{4,5}).*?'         # التردد والاستقطاب
            r'ID:\s*(?P<id>.*?)\n.*?'                      # معرف القناة
            r'#?CW:\s*(?P<cw>[A-F0-9\s]{16,32})',          # جعل الـ # اختيارية وقبول مسافات أكثر في الشفرة
            re.DOTALL | re.IGNORECASE
        )
        
        matches = pattern.finditer(content)
        
        active_feeds = []
        for match in matches:
            start_pos = match.start()
            # فحص السياق (350 حرف) لزيادة دقة الفلترة
            context = content[max(0, start_pos-350):match.end()]
            
            # الشروط النهائية لضمان أن الفيد مشفر، متاح، وليس مجرد قالب فارغ
            if "KEY FOUND" in context.upper() and \
               "CLEAR" not in context.upper() and \
               "(FTA)" not in context.upper() and \
               "NO KEY" not in context.upper():
                
                raw_sat = match.group('sat')
                # استخراج سطر القمر الفعلي
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
            
        print(f"Success! Found {len(active_feeds)} high-quality entries.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
