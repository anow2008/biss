import requests
from bs4 import BeautifulSoup
import json
import re

def clean_val(text):
    if not text: return ""
    # تحويل أي مسافات غريبة لمسافات عادية عشان الـ JSON يقبلها
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # حذف الإيموجي من النتيجة النهائية مع الإبقاء على الكلام والدرجات °
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # 1. البحث عن الشفرة (🔑) - دي أهم حاجة
    # بندور على الـ 16 حرف اللي بييجوا بعد الإيموجي أو كلمة CW
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    try:
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # 2. البحث الذكي بالإيموجي (📡، 📶، 🆔)
        sat, freq, cid = "Unknown", "N/A", "N/A"
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        for line in lines:
            # لو السطر فيه رادار القمر
            if '📡' in line:
                sat = clean_val(line.split('📡')[-1])
            # لو السطر فيه رادار التردد
            elif '📶' in line:
                freq = clean_val(line.split('📶')[-1])
            # لو السطر فيه رادار اسم القناة
            elif '🆔' in line:
                cid = clean_val(line.split('🆔')[-1])

        # 3. تأكيد إضافي لاسم القناة (زي حالة GCUK Enc 3)
        # لو الـ id لسه فاضي، بنشوف السطر اللي فوق الشفرة مباشرة
        if cid == "N/A" or cid == "":
            for i, line in enumerate(lines):
                if key_match.group(0) in line and i > 0:
                    potential_id = lines[i-1]
                    if not any(x in potential_id for x in ['📡', '📶', '🔑']):
                        cid = clean_val(potential_id)

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
    for post in posts:
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
