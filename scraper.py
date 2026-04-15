import requests
from bs4 import BeautifulSoup
import json
import re

def super_clean(text):
    """تنظيف شامل لإزالة كل العوائق البرمجية والمسافات الخفية"""
    if not text: return ""
    # استبدال المسافات البرمجية \xa0 بمسافات عادية لضمان قراءة النص
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # الإبقاء على النصوص، الأرقام، علامات الدرجة ° و @
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن الشفرة (16 حرف هكس) بأي تنسيق (مسافات، نقط، شرطات)
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    try:
        # تنسيق الشفرة لتكون XX XX XX XX XX XX XX XX المطلوبة لـ BissPro-Smart
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # تقسيم النص لأسطر نظيفة للبحث عن التفاصيل
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        key_line_index = -1
        for i, line in enumerate(lines):
            if key_match.group(0) in line:
                key_line_index = i
                break

        sat, freq, cid = "Unknown", "N/A", "N/A"

        # 2. استخراج البيانات (مسح شامل لكل الأسطر)
        for line in lines:
            line_low = line.lower()
            # كشف القمر: بالرمز أو علامة @ أو كلمات مشهورة
            if '📡' in line or '@' in line or any(s in line_low for s in ['eutelsat', 'astra', 'hotbird']):
                sat = super_clean(line)
            # كشف التردد: بالرمز أو نمط الأرقام (مثل 11000 H)
            elif '📶' in line or re.search(r'\d{5}\s+[hv]', line_low):
                freq = super_clean(line)
            # كشف الـ ID: بالرمز الصريح
            elif '🆔' in line:
                cid = super_clean(line.replace('🆔', ''))

        # 3. الحل "الإجباري" لاسم القناة (مثل VRT أو GCUK):
        # لو الـ ID لسه فاضي، خد السطر اللي فوق الشفرة مباشرة غصب عنه
        if (cid == "N/A" or cid == "") and key_line_index > 0:
            potential_id = lines[key_line_index - 1]
            # التأكد إن السطر ده مش هو التردد أو القمر
            if not any(x in potential_id for x in ['📡', '📶', '@']) and not re.search(r'\d{5}', potential_id):
                cid = super_clean(potential_id)

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
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    # سحب كل المنشورات المتاحة في الصفحة حالياً
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    for post in posts:
        content = post.get_text(separator="\n").strip()
        data = parse_sat_data(content)
        if data:
            # منع التكرار بناءً على الشفرة لضمان نظافة الملف
            if not any(d['key'] == data['key'] for d in database):
                database.insert(0, data) # وضع الأحدث في البداية
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    # كتابة الملف وحفظه
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"✅ Success: Captured {len(results)} blocks.")
