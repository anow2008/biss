import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """تنظيف النص مع الحفاظ على الأرقام والدرجات واللغة العربية"""
    if not text: return ""
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # السماح بالحروف (عربي وإنجليزي)، الأرقام، والرموز الأساسية للفيد
    clean = re.sub(r'[^\w\s\d\u0600-\u06FF\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن أي شفرة 16 حرف (Hex) في المنشور بالكامل
    # النمط الجديد يبحث عن 16 حرف بغض النظر عن المسافات أو الرموز بينهم
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    data = {}
    try:
        # تنسيق الشفرة لتكون ثابتة: XX XX XX XX XX XX XX XX
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # تقسيم النص لأسطر للبحث عن البيانات المرافقة
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        key_line_index = -1
        for i, line in enumerate(lines):
            if key_match.group(0) in line:
                key_line_index = i
                break

        # 2. استخراج القمر (بناءً على الرمز أو الكلمات المفتاحية)
        sat_match = re.search(r'(?:📡|SATELLITE|SAT)[:\s]*(.*)', text, re.IGNORECASE)
        if sat_match:
            data['satellite'] = clean_for_json(sat_match.group(1))
        else:
            # محاولة البحث عن سطر يحتوي على علامة @ (مثل 7.0E @)
            data['satellite'] = "Unknown"
            for line in lines:
                if '@' in line:
                    data['satellite'] = clean_for_json(line)
                    break

        # 3. استخراج التردد
        freq_match = re.search(r'(?:📶|FREQ)[:\s]*(.*)', text, re.IGNORECASE)
        if freq_match:
            data['frequency'] = clean_for_json(freq_match.group(1))
        else:
            # البحث عن نمط التردد الرقمي (مثل 11000 H 5000)
            freq_pattern = re.search(r'\d{5}\s+[HV]\s+\d+', text)
            data['frequency'] = clean_for_json(freq_pattern.group(0)) if freq_pattern else "N/A"
        
        # 4. استخراج اسم القناة (ID) - الحل الذكي لـ Unname وأخواتها
        id_match = re.search(r'(?:🆔|ID|SERVICE)[:\s]*(.*)', text, re.IGNORECASE)
        if id_match and id_match.group(1).strip():
            data['id'] = clean_for_json(id_match.group(1))
        elif key_line_index > 0:
            # إذا لم يوجد رمز، نأخذ السطر الذي يسبق الشفرة مباشرة (مثل Unname)
            potential_id = lines[key_line_index - 1]
            if not any(x in potential_id for x in ['📡', '📶', '@']) and len(potential_id) < 30:
                data['id'] = clean_for_json(potential_id)
            else:
                data['id'] = "N/A"
        else:
            data['id'] = "N/A"

        # 5. المفتاح في النهاية
        data['key'] = formatted_key

    except Exception:
        return None
        
    return data

def run_scraper():
    # استخدام رابط القناة الأصلي للسحب
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ خطأ اتصال: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    # التقاط كافة الحاويات التي قد تحتوي على نص (لضمان عدم فوات شيء)
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # المعالجة من الأحدث للأقدم (reversed لضمان أن الأحدث يظهر أولاً في الملف)
    for post in reversed(posts):
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        if structured_data:
            # منع التكرار بناءً على الشفرة (Key)
            if not any(d['key'] == structured_data['key'] for d in database):
                database.insert(0, structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    if results:
        with open('feeds.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"✅ تم سحب {len(results)} شفرة كاملة بنجاح.")
    else:
        print("⚠️ لم يتم العثور على شفرات جديدة.")
