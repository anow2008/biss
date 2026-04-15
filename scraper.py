import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """تنظيف النصوص مع الحفاظ على الأرقام والدرجات المدارية"""
    if not text: return ""
    # استبدال المسافات المخفية بمسافات عادية لضمان نجاح السحب
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # السماح بالأرقام، الحروف، النقط، السلاش، وعلامة الدرجة ° و @
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن الشفرة (16 حرف هكس) في أي مكان داخل البوست
    # التعبير ده بيمسك الشفرة حتى لو قبلها CW أو رموز أو مسافات غريبة
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    data = {}
    try:
        # تنسيق الشفرة لتكون XX XX XX XX XX XX XX XX
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # تقسيم النص لأسطر للبحث الذكي عن القمر والتردد والاسم
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        key_line_index = -1
        for i, line in enumerate(lines):
            if key_match.group(0) in line:
                key_line_index = i
                break

        # 2. استخراج القمر (📡)
        sat_match = re.search(r'(?:📡|SATELLITE)[:\s]*(.*)', text, re.IGNORECASE)
        if sat_match and sat_match.group(1).strip():
            data['satellite'] = clean_for_json(sat_match.group(1))
        else:
            # لو ملقاش الرمز، بيدور على سطر فيه علامة @ (زي 7.0°E @)
            data['satellite'] = "Unknown"
            for line in lines:
                if '@' in line:
                    data['satellite'] = clean_for_json(line)
                    break

        # 3. استخراج التردد (📶)
        freq_match = re.search(r'(?:📶|FREQ)[:\s]*(.*)', text, re.IGNORECASE)
        if freq_match and freq_match.group(1).strip():
            data['frequency'] = clean_for_json(freq_match.group(1))
        else:
            # لو ملقاش الرمز، بيدور على نمط التردد (5 أرقام ثم H أو V)
            f_p = re.search(r'\d{5}\s+[HV]\s+\d+', text)
            data['frequency'] = clean_for_json(f_p.group(0)) if f_p else "N/A"
        
        # 4. استخراج اسم القناة (ID) - حل مشكلة VRT و Unname
        id_match = re.search(r'(?:🆔|ID|SERVICE)[:\s]*(.*)', text, re.IGNORECASE)
        if id_match and id_match.group(1).strip():
            data['id'] = clean_for_json(id_search.group(1))
        elif key_line_index > 0:
            # أهم تعديل: لو ملقاش رمز ID، ياخد السطر اللي فوق الشفرة مباشرة
            potential_id = lines[key_line_index - 1]
            # التأكد إن السطر ده مش هو التردد أو القمر
            if not any(x in potential_id for x in ['📡', '📶', '@']) and not re.search(r'\d{5}\s+[HV]', potential_id):
                data['id'] = clean_for_json(potential_id)
            else:
                data['id'] = "N/A"
        else:
            data['id'] = "N/A"

        # 5. الشفرة في النهاية للبلجن BissPro-Smart
        data['key'] = formatted_key

    except Exception:
        return None
        
    return data

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # المعالجة من الأحدث للأقدم لضمان ظهور الجديد أول الملف
    for post in reversed(posts):
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        if structured_data:
            # منع التكرار بناءً على الشفرة
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
        print("⚠️ لم يتم العثور على شفرات.")
