import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """حذف الإيموجي والرموز غير المرغوبة وإبقاء النصوص والأرقام فقط"""
    if not text: return ""
    # حذف أي حرف غير موجود في نطاق الأسكي الأساسي (حذف الإيموجي والرموز)
    clean = re.sub(r'[^\x00-\x7F]+', '', text)
    # تنظيف المسافات الزائدة في البداية والنهاية
    return clean.strip()

def parse_sat_data(text):
    # 1. استخراج الشفرة (CW) وتنسيقها بمسافات (كل حرفين)
    cw_pattern = re.compile(r'CW[:\s#]*(([A-F0-9]{2}[\s:-]*){8})', re.IGNORECASE)
    cw_match = cw_pattern.search(text)
    
    if not cw_match:
        return None

    data = {}
    try:
        # استخراج الـ 16 حرف ووضع مسافة بين كل زوج
        raw_cw = re.sub(r'[\s:-]', '', cw_match.group(1)).upper()
        formatted_key = " ".join([raw_cw[i:i+2] for i in range(0, 16, 2)])
        data['key'] = formatted_key

        # 2. اسم القمر (تنظيف من الإيموجي)
        sat_match = re.search(r'📡\s*(.*)', text)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        # 3. التردد بالكامل (الرقم والقطبية والترميز)
        freq_line = re.search(r'📶\s*(.*)', text)
        data['frequency'] = clean_for_json(freq_line.group(1)) if freq_line else "N/A"
        
        # 4. الـ ID (اسم القناة)
        id_match = re.search(r'(🆔|ID[:\s]*)\s*(.*)', text, re.IGNORECASE)
        data['id'] = clean_for_json(id_match.group(2)) if id_match else "N/A"

    except Exception:
        return None
        
    return data

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    for post in posts:
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        if structured_data:
            # منع تكرار نفس الشفرة في الملف
            if not any(d['key'] == structured_data['key'] for d in database):
                database.append(structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # حفظ الملف بتنسيق JSON نظيف
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"✅ تم إنشاء feeds.json بنجاح. يحتوي على {len(results)} عنصر.")
