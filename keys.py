import cloudscraper
import re
import json

def clean_text(text):
    """تنظيف النصوص وإزالة الفراغات الزائدة"""
    return text.strip() if text else "N/A"

def scrape_fury_biss():
    # استخدام cloudscraper لتخطي حماية الصفحات والعمل كمتصفح ويندوز
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://t.me/s/furybiss"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch channel. Status: {response.status_code}")
            return

        content = response.text
        active_feeds = []

        # استخراج كتل الرسائل من كود الصفحة
        msg_blocks = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', content, re.DOTALL)

        for block in msg_blocks:
            # تحويل أي وسوم HTML داخل الرسالة إلى سطور جديدة لتسهيل الفحص بالـ Regex
            block_clean = re.sub(r'<[^>]+>', '\n', block)
            
            # التحقق من وجود وسام الشفرة (CW) لضمان أن الرسالة تحتوي على مفاتيح
            if "#CW:" in block_clean.upper() or "CW:" in block_clean.upper():
                
                # 1. استخراج التردد (5 أرقام + القطبية + الترميز)
                freq_match = re.search(r'(\d{5})\s+([VH])\s+(\d{4,5})', block_clean)
                
                # 2. استخراج الـ ID (يتوقف عند نهاية السطر أو وسم جديد)
                id_match = re.search(r'ID:\s*([^\n<]+)', block_clean, re.IGNORECASE)
                
                # 3. استخراج الشفرة (تدعم الحروف والأرقام والمسافات حتى 40 حرف)
                cw_match = re.search(r'(?:#CW|CW):\s*([A-F0-9\s]{16,40})', block_clean, re.IGNORECASE)
                
                # 4. استخراج القمر الصناعي (مثل 7.0°E أو 30.0°W)
                sat_match = re.search(r'([^\n]*?@\s?\d+\.?\d?°\s?[EW])', block_clean, re.IGNORECASE)

                if freq_match and cw_match:
                    feed_item = {
                        "satellite": clean_text(sat_match.group(1)) if sat_match else "N/A",
                        "frequency": f"{freq_match.group(1)} {freq_match.group(2)} {freq_match.group(3)}",
                        "id": clean_text(id_match.group(1)) if id_match else "N/A",
                        "key": clean_text(cw_match.group(1)) # يحافظ على المسافات كما طلبت في bisskey.py
                    }
                    
                    if feed_item not in active_feeds:
                        active_feeds.append(feed_item)

        # حفظ النتائج في ملف keys.json بنفس تنسيق bisskeys.json
        with open('keys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Done! Found {len(active_feeds)} keys from FuryBiss channel.")

    except Exception as e:
        print(f"Error during scraping: {e}")

if __name__ == "__main__":
    scrape_fury_biss()
