import requests
from bs4 import BeautifulSoup
import json
import re

def clean_data(text):
    """تنظيف النص من أي رموز غريبة مع الحفاظ على الأرقام والنصوص"""
    if not text: return ""
    # تحويل المسافات البرمجية لمسافات عادية
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # تنظيف النص مع الإبقاء على الحروف والأرقام والدرجة ° و @
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن الشفرة (🔑) أولاً عشان نضمن إن البلوك ده فيه شفرة
    # بندور على أي 16 حرف هكس بييجوا بعد إيموجي المفتاح أو كلمة CW
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    data = {}
    try:
        # تنسيق الشفرة (Key)
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # 2. سحب اسم القمر من جنب إيموجي 📡
        sat_match = re.search(r'📡\s*(.*)', text)
        data['satellite'] = clean_data(sat_match.group(1)) if sat_match else "Unknown"

        # 3. سحب التردد من جنب إيموجي 📶
        freq_match = re.search(r'📶\s*(.*)', text)
        data['frequency'] = clean_data(freq_match.group(1)) if freq_match else "N/A"

        # 4. سحب اسم القناة من جنب إيموجي 🆔
        id_match = re.search(r'🆔\s*(.*)', text)
        if id_match and id_match.group(1).strip():
            data['id'] = clean_data(id_match.group(1))
        else:
            # لو ملقاش الإيموجي، يشوف السطر اللي فوق الشفرة مباشرة (احتياطي لـ Unname)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            key_line_index = -1
            for i, line in enumerate(lines):
                if key_match.group(0) in line:
                    key_line_index = i
                    break
            if key_line_index > 0:
                potential_id = lines[key_line_index - 1]
                if not any(x in potential_id for x in ['📡', '📶', '🔑']):
                    data['id'] = clean_data(potential_id)
                else:
                    data['id'] = "N/A"
            else:
                data['id'] = "N/A"

        # 5. وضع الشفرة في مكانها
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
        print(f"❌ Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # المعالجة لضمان سحب كل البلوكات
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
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"✅ تم سحب {len(results)} بلوك بنجاح بناءً على الإيموجي.")
