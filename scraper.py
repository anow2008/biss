import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """حذف الإيموجي والرموز مع الإبقاء على النصوص والأرقام"""
    if not text: return ""
    clean = re.sub(r'[^\w\s\d\u0600-\u06FF\.\-\/]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # البحث عن الشفرة أولاً للتأكد من أن البوست يحتوي على بيانات مفيدة
    cw_pattern = re.compile(r'CW[:\s#]*(([A-F0-9]{2}[\s:-]*){8})', re.IGNORECASE)
    cw_match = cw_pattern.search(text)
    
    if not cw_match:
        return None

    data = {}
    try:
        # 1. استخراج الـ 16 حرف وتنسيقها
        raw_cw = re.sub(r'[\s:-]', '', cw_match.group(1)).upper()
        if len(raw_cw) != 16: return None
        formatted_key = " ".join([raw_cw[i:i+2] for i in range(0, 16, 2)])

        # --- الترتيب الجديد المطلوب ---
        
        # 2. اسم القمر
        sat_match = re.search(r'(?:📡|SATELLITE)[:\s]*(.*)', text, re.IGNORECASE)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        # 3. التردد
        freq_line = re.search(r'(?:📶|FREQ)[:\s]*(.*)', text, re.IGNORECASE)
        data['frequency'] = clean_for_json(freq_line.group(1)) if freq_line else "N/A"
        
        # 4. الـ ID (اسم القناة)
        id_match = re.search(r'(?:🆔|ID|SERVICE)[:\s]*(.*)', text, re.IGNORECASE)
        data['id'] = clean_for_json(id_match.group(1)) if id_match else "N/A"

        # 5. الشفرة (Key) في الآخر
        data['key'] = formatted_key

    except Exception:
        return None
        
    return data

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # قراءة من الأحدث للأقدم
    for post in reversed(posts):
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        if structured_data:
            # منع التكرار بناءً على الشفرة
            if not any(d['key'] == structured_data['key'] for d in database):
                database.append(structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    if results:
        with open('feeds.json', 'w', encoding='utf-8') as f:
            # استخدام indent=4 عشان الملف يكون مقروء ومرتب
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        print(f"✅ تم الحفظ بنجاح! {len(results)} عنصر بالترتيب المطلوب.")
    else:
        print("⚠️ لم يتم العثور على بيانات.")
