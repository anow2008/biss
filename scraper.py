import requests
from bs4 import BeautifulSoup
import json
import re
import os

def parse_sat_data(text):
    # 1. الـ Regex ده مخصص لجلب 16 حرف (Hex) فقط لا غير
    # بيدور على كلمة CW وبعدها بيعد 8 مجموعات (كل مجموعة حرفين)
    cw_pattern = re.compile(r'CW[:\s#]*(([0-9A-F]{2}[\s:-]*){8})', re.IGNORECASE)
    cw_match = cw_pattern.search(text)
    
    if not cw_match:
        return None

    data = {}
    try:
        # تنظيف الشفرة: مسح المسافات وأي حروف زيادة بعد الـ 16 حرف
        raw_cw = cw_match.group(1).strip()
        clean_cw = re.sub(r'[\s:-]', '', raw_cw).upper()
        clean_cw = clean_cw[:16] # تأكيد قاطع إننا واخدين 16 حرف بس (بيتجاهل الـ Views)

        # 2. استخراج التردد (أول 5 أرقام بيظهروا في النص)
        freq_match = re.search(r'(\d{5})', text)
        
        # 3. استخراج اسم القمر (أول سطر في الرسالة)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        data['satellite'] = lines[0] if lines else "Unknown Satellite"
        data['frequency'] = freq_match.group(1) if freq_match else "N/A"
        data['cw'] = clean_cw
        
    except Exception:
        return None
    return data

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Error: Telegram returned status {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # بنسحب النصوص من كلاس الرسائل المباشر لضمان دقة المحتوى
        posts = soup.find_all('div', class_='tgme_widget_message_text')
        
        extracted_list = []
        for post in posts:
            content = post.get_text(separator="\n").strip()
            structured_item = parse_sat_data(content)
            if structured_item:
                extracted_list.append(structured_item)
        return extracted_list
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

if __name__ == "__main__":
    filename = 'feeds.json'
    
    # تحميل البيانات القديمة عشان نحافظ عليها
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                database = json.load(f)
            except:
                database = []
    else:
        database = []

    # سحب البيانات الجديدة من تليجرام
    print("Scraping latest feeds...")
    scraped_results = run_scraper()
    
    # دمج الجديد مع القديم ومنع التكرار (الجديد بينزل في الأول)
    count_added = 0
    for item in scraped_results:
        # التأكد إن الشفرة مش موجودة في الـ Database قبل كدة
        if not any(d['cw'] == item['cw'] for d in database):
            database.insert(0, item)
            count_added += 1
    
    # الحفاظ على آخر 500 شفرة فقط لضمان سرعة الملف
    database = database[:500]

    # حفظ الملف النهائي
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Process Completed!")
    print(f"Added: {count_added} new codes. Total in database: {len(database)}")
