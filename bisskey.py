import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text: return "N/A"
    # تنظيف شامل للإيموجي والرموز التعبيرية والكلمات الزائدة
    clean = re.sub(r'[📡📶🎬📊🆔🔑🔓]|BISS • KEY FOUND', '', text)
    # تنظيف المسافات الزائدة في البداية والنهاية
    return clean.strip()

def scrape_to_json():
    # إنشاء السكرابر لتخطي حماية الموقع
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"Failed. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        # الحصول على النص مع الحفاظ على بنية السطور
        content = soup.get_text(separator="\n")
        
        # تقسيم الصفحة لبلوكات بناءً على جملة KEY FOUND لأنها تتكرر مع كل تردد مشفر
        blocks = re.split(r'(?=BISS • KEY FOUND)', content)
        
        active_feeds = []

        for block in blocks:
            # تخطي البلوكات الفارغة أو التي لا تحتوي على تردد
            if "KEY FOUND" not in block: continue
            
            # 1. لقط التردد (القلب النابض للبلوك)
            freq_match = re.search(r'(\d{5})\s*([VH])\s*(\d{4,5})', block)
            
            # 2. لقط الشفرة (بيدور بعد إيموجي المفتاح حتى لو في سطر جديد)
            cw_match = re.search(r'🔑\s*\n*\s*([A-F0-9\s]{16,50})', block, re.IGNORECASE | re.UNICODE)

            # شرط أساسي: لازم يكون فيه تردد ومعاه شفرة عشان يدخل الـ JSON
            if freq_match and cw_match:
                
                # 3. لقط اسم القمر (بيدور على السطر اللي فيه علامة الدرجة °)
                sat_match = re.search(r'(?:📡)?([^\n]*?\d+\.?\d?°\s?[EW][^\n]*)', block, re.IGNORECASE)
                
                # 4. لقط الـ ID أو اسم القناة (بعد إيموجي 🆔)
                id_match = re.search(r'🆔\s*([^\n\r]+)', block, re.UNICODE)
                
                # تنظيف البيانات المستخرجة
                sat_name = clean_text(sat_match.group(1)) if sat_match else "N/A"
                channel_id = clean_text(id_match.group(1)) if id_match else "N/A"
                # تنظيف الشفرة من السطور الجديدة والمسافات الزائدة
                clean_key = cw_match.group(1).strip().replace("\n", "")
                
                feed_item = {
                    "satellite": sat_name,
                    "frequency": f"{freq_match.group(1)} {freq_match.group(2)} {freq_match.group(3)}",
                    "id": channel_id,
                    "key": clean_key
                }
                
                # إضافة الفيد لو مش موجود قبل كدة عشان نمنع التكرار
                if feed_item not in active_feeds:
                    active_feeds.append(feed_item)

        # حفظ كل النتائج في ملف JSON
        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Done! Found {len(active_feeds)} active feeds with keys.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
