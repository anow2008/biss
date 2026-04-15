import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """Cleaning text for Enigma2 receivers."""
    if not text: return ""
    # استبدال المسافات المخفية بمسافات عادية لضمان القراءة الصحيحة
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # الإبقاء على الدرجات المدارية والأرقام والنصوص
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    """Extracts data if '🔑 CW' and a 16-character key are found."""
    # تنظيف النص داخلياً من المسافات المخفية قبل البحث
    clean_content = text.replace('\xa0', ' ')
    
    # البحث عن نمط المفتاح مع CW: (🔑 CW) مع مراعاة وجود مسافات أو رموز بينهما
    # ثم البحث عن الـ 16 حرف الخاصة بالشفرة
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(clean_content)
    
    # شرطك الأساسي: يجب أن يحتوي البلوك على "CW" وشفرة 16 حرف
    if not key_match or "CW" not in clean_content.upper():
        return None

    data = {}
    try:
        # تنسيق الشفرة: XX XX XX XX XX XX XX XX
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # 1. القمر (بجوار 📡)
        sat_match = re.search(r'📡\s*([^\n]+)', clean_content)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        # 2. التردد (بجوار 📶)
        freq_match = re.search(r'📶\s*([^\n🎬📊🆔]+)', clean_content)
        data['frequency'] = clean_for_json(freq_match.group(1)) if freq_match else "N/A"
        
        # 3. المعرف/اسم القناة (بجوار 🆔)
        id_match = re.search(r'🆔\s*([^\n🔑]+)', clean_content)
        data['id'] = clean_for_json(id_match.group(1)) if id_match else "N/A"

        # 4. الشفرة (الحقل المطلوب لـ BissPro-Smart)
        data['key'] = formatted_key
        
        return data
    except Exception:
        return None

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # سحب كل ما هو موجود في الصفحة حالياً
    for post in posts:
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        if structured_data:
            # منع التكرار بناءً على الشفرة
            if not any(d['key'] == structured_data['key'] for d in database):
                database.insert(0, structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # مسح ملف JSON القديم تماماً وكتابة الجديد
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ Success! Captured {len(results)} blocks containing CW keys.")
    else:
        print("⚠️ No blocks with '🔑 CW' were found in the current view.")
