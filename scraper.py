import requests
from bs4 import BeautifulSoup
import json
import re

def super_clean(text):
    """تنظيف جراحي للنص لإزالة كل الرموز المخفية والمسافات الغريبة"""
    if not text: return ""
    # تحويل كافة أنواع المسافات المخفية لمسافات عادية
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # حذف الرموز التعبيرية مع الإبقاء على الدرجة ° و @ والأرقام والنصوص
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن الشفرة (16 حرف هكس) - المحرك الأساسي
    # النمط الجديد يتجاهل أي رموز أو كلمات تسبق الشفرة (مثل CW)
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    try:
        # تنسيق الشفرة: XX XX XX XX XX XX XX XX
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # تقسيم النص لأسطر نظيفة
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        key_line_index = -1
        for i, line in enumerate(lines):
            if key_match.group(0) in line:
                key_line_index = i
                break

        sat, freq, cid = "Unknown", "N/A", "N/A"

        # 2. استخراج البيانات بالاعتماد على الرموز أو الكلمات الدالة
        for i, line in enumerate(lines):
            line_clean = line.lower()
            if '📡' in line or '@' in line or 'eutelsat' in line_clean or 'hotbird' in line_clean:
                sat = super_clean(line)
            elif '📶' in line or re.search(r'\d{5}\s+[hv]', line_clean):
                freq = super_clean(line)
            elif '🆔' in line:
                cid = super_clean(line.replace('🆔', ''))

        # 3. الحل الذكي لـ GCUK Enc 3 وأمثالها:
        # إذا لم نجد رمز 🆔، نأخذ السطر الذي يسبق الشفرة مباشرة
        if (cid == "N/A" or cid == "") and key_line_index > 0:
            potential_id = lines[key_line_index - 1]
            # التأكد أن السطر ليس هو التردد أو القمر
            if not any(x in potential_id for x in ['📡', '📶', '@']) and not re.search(r'\d{5}\s+[HV]', potential_id):
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
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # المعالجة لضمان سحب كل ما هو متاح في الصفحة
    for post in posts:
        content = post.get_text(separator="\n").strip()
        data = parse_sat_data(content)
        if data:
            # منع التكرار بناءً على الشفرة
            if not any(d['key'] == data['key'] for d in database):
                database.insert(0, data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # حفظ الملف بصيغة JSON نظيفة ومرتبة
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ Success! Captured {len(results)} feed blocks.")
    else:
        print("⚠️ No valid feeds found. Check the Telegram source.")
