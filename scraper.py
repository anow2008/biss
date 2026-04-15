import requests
from bs4 import BeautifulSoup
import json
import re

def clean_val(text):
    """تنظيف النص مع الحفاظ على الأرقام والدرجة ° و @ والعربي"""
    if not text: return ""
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # حذف الإيموجي فقط من النتيجة النهائية
    clean = re.sub(r'[^\w\s\d\u0600-\u06FF\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن الشفرة (16 حرف هكس)
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    try:
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # تقسيم النص لأسطر نظيفة
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        sat, freq, cid = "Unknown", "N/A", "N/A"
        key_line_index = -1

        for i, line in enumerate(lines):
            if key_match.group(0) in line:
                key_line_index = i
                break

        # 2. المسح الشامل لكل الأسطر
        for line in lines:
            line_low = line.lower()
            if '📡' in line or '@' in line:
                sat = clean_val(line)
            elif '📶' in line or re.search(r'\d{5}\s+[hv]', line_low):
                freq = clean_val(line)
            elif '🆔' in line:
                cid = clean_val(line)

        # 3. الحل "العبقري" لاسم القناة (ID) المفقود
        # لو ملقيناش رمز 🆔، هنطلع من سطر الشفرة لفوق "سطر بسطر" لحد ما نلاقي أول نص
        if (cid == "N/A" or cid == "") and key_line_index > 0:
            for j in range(key_line_index - 1, -1, -1):
                potential = lines[j]
                # لو السطر فيه نص ومش هو التردد ولا القمر ولا فيه كلمة CW
                if not any(x in potential for x in ['📡', '📶', '@', '🔑', 'CW']):
                    if not re.search(r'\d{5}', potential): # مش تردد
                        cid = clean_val(potential)
                        break # لقينا الاسم، وقف بحث

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
    for post in reversed(posts):
        content = post.get_text(separator="\n").strip()
        data = parse_sat_data(content)
        if data:
            if not any(d['key'] == data['key'] for d in database):
                database.insert(0, data)
    return database

if __name__ == "__main__":
    results = run_scraper()
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"✅ Success: Captured {len(results)} items.")
