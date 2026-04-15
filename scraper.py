import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def clean_for_json(text):
    """تنظيف النصوص مع الإبقاء على الدرجات المدارية ورموز الأقمار"""
    if not text: return ""
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # السماح بالأرقام، الحروف، النقط، السلاش، وعلامة الدرجة ° و @
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    """سحب البيانات فقط إذا وجدت شفرة مكونة من 16 حرفاً"""
    # بحث مرن جداً عن الشفرة: يبحث عن 16 حرف Hex بغض النظر عن الرموز التي تسبقها
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

        # سحب القمر من بعد رمز الطبق 📡
        sat_match = re.search(r'📡\s*([^\n]+)', text)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        # سحب التردد من بعد رمز الإشارة 📶
        freq_match = re.search(r'📶\s*([^\n🎬📊🆔]+)', text)
        data['frequency'] = clean_for_json(freq_match.group(1)) if freq_match else "N/A"
        
        # سحب اسم القناة من بعد رمز الهوية 🆔
        id_match = re.search(r'🆔\s*([^\n🔑]+)', text)
        data['id'] = clean_for_json(id_match.group(1)) if id_match else "N/A"

        # إضافة الشفرة في الحقل الرابع كما طلبت لبلجن BissPro-Smart
        data['key'] = formatted_key
        return data
    except Exception:
        return None

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # تحديد علامة بداية اليوم (مثلاً 15 April 2026)
    today_marker = datetime.now().strftime("%d %B %Y").lstrip('0')
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    found_today_session = False
    
    for post in posts:
        content = post.get_text(separator="\n").strip()
        
        # التأكد من أننا نسحب فقط ما نُشر بعد إعلان بداية الجلسة اليومية
        if today_marker in content and "Daily Scan Session" in content:
            found_today_session = True
            continue
            
        if found_today_session:
            structured_data = parse_sat_data(content)
            if structured_data:
                # منع التكرار وإضافة الأحدث في البداية
                if not any(d['key'] == structured_data['key'] for d in database):
                    database.insert(0, structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # مسح الملف القديم وكتابة البيانات الجديدة فقط
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ تم سحب {len(results)} شفرة بنجاح وتحديث ملف feeds.json")
    else:
        print("⚠️ لم يتم العثور على شفرات جديدة بعد إعلان بداية اليوم.")
