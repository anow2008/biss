import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """تنظيف النص مع الحفاظ على الأرقام والدرجة ° و @ والعربي"""
    if not text: return ""
    # تحويل المسافات الغريبة لمسافات عادية لضمان عدم ضياع النص
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # الإبقاء على الحروف (عربي وإنجليزي)، الأرقام، والرموز الأساسية
    clean = re.sub(r'[^\w\s\d\u0600-\u06FF\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن أي تتابع لـ 16 حرف هكس (الشفرة) - ده المحرك الأساسي
    # النمط ده هيقفش أي شفرة حتى لو وسط كلام كتير أو رموز غريبة
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    try:
        # تنسيق الشفرة لشكلها النهائي (XX XX XX XX XX XX XX XX)
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # تقسيم النص لأسطر عشان نبحث في كل سطر بشكل مستقل
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # قيم افتراضية في حالة ملقيناش الرموز
        sat, freq, cid = "Unknown", "N/A", "N/A"
        key_line_index = -1

        # تحديد سطر الشفرة
        for i, line in enumerate(lines):
            if key_match.group(0) in line:
                key_line_index = i
                break

        # 2. المسح الشامل (Scanning) لكل سطر في البلوك
        for line in lines:
            line_low = line.lower()
            # صيد القمر: بالإيموجي أو كلمة SAT أو علامة @
            if '📡' in line or 'sat' in line_low or '@' in line:
                sat = clean_for_json(line.split('📡')[-1] if '📡' in line else line)
            
            # صيد التردد: بالإيموجي أو نمط الأرقام (مثل 11000 H)
            elif '📶' in line or re.search(r'\d{5}\s+[hv]', line_low):
                freq = clean_for_json(line.split('📶')[-1] if '📶' in line else line)
            
            # صيد اسم القناة (ID): بالإيموجي الصريح
            elif '🆔' in line:
                cid = clean_for_json(line.split('🆔')[-1])

        # 3. خطة الطوارئ لاسم القناة (عشان ميفوتش GCUK أو Unname)
        # لو الـ ID لسه مجهول، بياخد السطر اللي فوق الشفرة فوراً
        if (cid == "N/A" or cid == "") and key_line_index > 0:
            potential_id = lines[key_line_index - 1]
            # نتأكد إن السطر ده مش هو التردد أو القمر اللي سحبناهم
            if not any(x in potential_id for x in ['📡', '📶', '@', '🔑']) and not re.search(r'\d{5}', potential_id):
                cid = clean_for_json(potential_id)

        return {
            "satellite": sat,
            "frequency": freq,
            "id": cid,
            "key": formatted_key
        }
    except:
        return None

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception: return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # reversed عشان نجيب الأحدث الأول في الملف
    for post in reversed(posts):
        content = post.get_text(separator="\n").strip()
        data = parse_sat_data(content)
        if data:
            # منع التكرار بناءً على الشفرة (Key)
            if not any(d['key'] == data['key'] for d in database):
                database.append(data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"✅ Success: Captured {len(results)} items.")
