import requests
from bs4 import BeautifulSoup
import json
import re
import os

def parse_sat_data(text):
    # نمط محسن لجلب الشفرات (16 أو 32 حرف/رقم)
    cw_pattern = re.compile(r'CW[:\s#]*([A-F0-9\s]{16,40})', re.IGNORECASE)
    cw_match = cw_pattern.search(text)
    
    if not cw_match:
        return None

    data = {"raw_text": text}
    try:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        data['satellite'] = lines[0] if lines else "Unknown"
        
        # استخراج التردد (5 أرقام)
        freq_match = re.search(r'(\d{5})', text)
        data['frequency'] = freq_match.group(1) if freq_match else "N/A"
        
        # تنظيف الشفرة وتوحيد شكلها (كلها Upper Case وبدون مسافات زيادة)
        clean_cw = cw_match.group(1).strip().replace(' ', '').replace('\n', '').upper()
        data['cw'] = clean_cw
    except:
        return None
    return data

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200: return []
    except:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_bubble')
    
    new_data = []
    for post in posts:
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        if structured_data:
            new_data.append(structured_data)
            
    return new_data

if __name__ == "__main__":
    # 1. تحميل البيانات القديمة لو موجودة
    filename = 'feeds.json'
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                database = json.load(f)
            except:
                database = []
    else:
        database = []

    # 2. سحب البيانات الجديدة
    scraped_results = run_scraper()
    
    # 3. دمج الجديد مع القديم بدون تكرار (بناءً على الشفرة CW)
    count_added = 0
    for item in scraped_results:
        if not any(d['cw'] == item['cw'] for d in database):
            database.append(item)
            count_added += 1
    
    # 4. حفظ الكل
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
    
    print(f"تمت العملية: أضفنا {count_added} شفرات جديدة. الإجمالي الآن: {len(database)}")
