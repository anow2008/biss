import requests
from bs4 import BeautifulSoup
import json
import re
import sys

def clean_for_json(text):
    if not text: return ""
    # تحويل المسافات البرمجية لمسافات عادية لضمان نجاح السحب
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # بحث شامل عن شفرة 16 حرف (Hex) في أي مكان
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    try:
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        lines = [l.strip() for l in text.split('\n') if l.strip()]
        key_line_index = -1
        for i, line in enumerate(lines):
            if key_match.group(0) in line:
                key_line_index = i
                break

        # سحب القمر
        sat = "Unknown"
        sat_match = re.search(r'(?:📡|SATELLITE)[:\s]*(.*)', text, re.IGNORECASE)
        if sat_match: sat = clean_for_json(sat_match.group(1))
        else:
            for line in lines:
                if '@' in line: 
                    sat = clean_for_json(line)
                    break

        # سحب التردد
        freq = "N/A"
        freq_match = re.search(r'(?:📶|FREQ)[:\s]*(.*)', text, re.IGNORECASE)
        if freq_match: freq = clean_for_json(freq_match.group(1))
        else:
            f_p = re.search(r'\d{5}\s+[HV]\s+\d+', text)
            if f_p: freq = clean_for_json(f_p.group(0))

        # سحب الـ ID (مثل VRT أو Unname)
        cid = "N/A"
        id_match = re.search(r'(?:🆔|ID|SERVICE)[:\s]*(.*)', text, re.IGNORECASE)
        if id_match: cid = clean_for_json(id_match.group(1))
        elif key_line_index > 0:
            potential_id = lines[key_line_index - 1]
            if not any(x in potential_id for x in ['📡', '📶', '@']):
                cid = clean_for_json(potential_id)

        return {"satellite": sat, "frequency": freq, "id": cid, "key": formatted_key}
    except:
        return None

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    print(f"--- Starting Scraper at {url} ---")
    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    print(f"🔍 Found {len(posts)} potential posts on page.")
    
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
    
    # التأكد من كتابة الملف حتى لو كانت النتائج فارغة (لتجنب تعليق GitHub)
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ SUCCESS: {len(results)} feeds saved to feeds.json")
    else:
        print("⚠️ WARNING: No valid keys found in the posts.")
