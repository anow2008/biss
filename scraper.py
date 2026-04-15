import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """تنظيف النصوص لضمان عملها على الرسيفر بدون مشاكل"""
    if not text: return ""
    # استبدال المسافات المخفية بمسافات عادية
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # السماح بالأرقام، الحروف، النقط، السلاش، وعلامة الدرجة ° و @
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    """سحب البيانات فقط إذا وجدت شفرة 16 حرفاً"""
    # بحث مرن جداً عن أي 16 حرف Hex متتالية (BISS أو CW)
    # هذا النمط سيلتقط الشفرة حتى لو كان قبلها رموز أو مسافات غريبة
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    data = {}
    try:
        # تنسيق الشفرة لتصبح XX XX XX XX XX XX XX XX
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # سحب البيانات بناءً على الرموز (📡، 📶، 🆔)
        sat_match = re.search(r'📡\s*([^\n]+)', text)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        freq_match = re.search(r'📶\s*([^\n🎬📊🆔]+)', text)
        data['frequency'] = clean_for_json(freq_match.group(1)) if freq_match else "N/A"
        
        id_match = re.search(r'🆔\s*([^\n🔑]+)', text)
        data['id'] = clean_for_json(id_match.group(1)) if id_match else "N/A"

        # الشفرة هي الحقل الرابع والأخير
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
    # سحب كل المنشورات الظاهرة التي تحتوي على شفرة
    for post in posts:
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        if structured_data:
            # منع التكرار ووضع الأحدث في البداية
            if not any(d['key'] == structured_data['key'] for d in database):
                database.insert(0, structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # مسح الملف القديم تماماً وكتابة النتائج الجديدة
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ Success! Found {len(results)} keys.")
    else:
        print("⚠️ Still empty? Check if the Telegram page is loading correctly in your browser.")
