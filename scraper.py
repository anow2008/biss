import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """حذف الإيموجي والرموز مع الإبقاء على النصوص والأرقام والدرجة"""
    if not text: return ""
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن الشفرة أولاً (المحرك الأساسي)
    cw_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    cw_match = cw_pattern.search(text)
    
    if not cw_match:
        return None

    data = {}
    try:
        # تنسيق الشفرة
        raw_cw = re.sub(r'[\s:-]', '', cw_match.group(0)).upper()
        if len(raw_cw) != 16: return None
        formatted_key = " ".join([raw_cw[i:i+2] for i in range(0, 16, 2)])

        # تقسيم النص لأسطر للبحث عن "الاسم المجرد" مثل Unname
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        key_line_index = -1
        for i, line in enumerate(lines):
            if cw_match.group(0) in line:
                key_line_index = i
                break

        # 2. اسم القمر
        sat_match = re.search(r'(?:📡|SATELLITE)[:\s]*(.*)', text, re.IGNORECASE)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        # 3. التردد
        freq_match = re.search(r'(?:📶|FREQ)[:\s]*(.*)', text, re.IGNORECASE)
        data['frequency'] = clean_for_json(freq_match.group(1)) if freq_match else "N/A"
        
        # 4. الـ ID (اسم القناة) - البحث الذكي عن Unname وأمثالها
        id_search = re.search(r'(?:🆔|ID|SERVICE)[:\s]*(.*)', text, re.IGNORECASE)
        
        if id_search and id_search.group(1).strip():
            data['id'] = clean_for_json(id_search.group(1))
        elif key_line_index > 0:
            # لو ملقاش رمز، بياخد السطر اللي فوق الشفرة مباشرة (عشان Unname تظهر)
            potential_id = lines[key_line_index - 1]
            # التأكد إن السطر اللي فوقها مش هو التردد أو القمر
            if not any(x in potential_id for x in ['📡', '📶', '@']) and not re.search(r'\d{5}\s+[HV]', potential_id):
                data['id'] = clean_for_json(potential_id)
            else:
                data['id'] = "N/A"
        else:
            data['id'] = "N/A"

        # 5. الشفرة (Key) في الآخر للبلجن
        data['key'] = formatted_key

    except Exception:
        return None
        
    return data

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
            if not any(d['key'] == structured_data['key'] for d in database):
                database.append(structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    if results:
        with open('feeds.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"✅ تم الحفظ! سحب {len(results)} عنصر بنجاح.")
    else:
        print("⚠️ لم يتم العثور على بيانات.")
