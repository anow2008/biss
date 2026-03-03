import requests
from bs4 import BeautifulSoup
import json
import re

def parse_sat_data(text):
    # البحث عن الشفرة بتنسيق مرن جداً
    cw_match = re.search(r'CW:?\s*([A-F0-9\s]{15,})', text, re.IGNORECASE)
    if not cw_match:
        return None

    data = {"raw_text": text}
    try:
        # استخراج اسم القمر (عادة يكون أول سطر)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        data['satellite'] = lines[0] if lines else "Unknown"
        
        # استخراج التردد
        freq_match = re.search(r'(\d{5})', text)
        data['frequency'] = freq_match.group(1) if freq_match else "N/A"
        
        # استخراج الشفرة وتنظيفها
        data['cw'] = cw_match.group(1).strip().replace('\n', ' ')
    except:
        return None
    return data

def run_scraper():
    # استخدام محرك RSS لجلب البيانات (أكثر استقراراً)
    rss_url = "https://rsshub.app/telegram/channel/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    print("جاري محاولة سحب البيانات عبر RSS...")
    try:
        response = requests.get(rss_url, headers=headers, timeout=20)
        # إذا فشل الرابط البديل، نعود للرابط الأصلي بتعديل بسيط
        if response.status_code != 200:
            print("الرابط البديل فشل، محاولة الرابط الأساسي...")
            response = requests.get("https://t.me/s/live_sat_feeds", headers=headers)
    except:
        return []

    soup = BeautifulSoup(response.content, 'xml' if 'xml' in response.headers.get('Content-Type', '') else 'html.parser')
    
    # البحث عن النصوص سواء في الـ RSS أو الـ HTML العادي
    descriptions = soup.find_all('description') # للـ RSS
    if not descriptions:
        descriptions = soup.select('.tgme_widget_message_text') # للـ HTML

    print(f"تم العثور على {len(descriptions)} منشور.")
    
    database = []
    for item in descriptions:
        # الحصول على النص سواء من تاغ RSS أو HTML
        content = item.get_text(separator="\n").strip()
        
        structured_data = parse_sat_data(content)
        if structured_data:
            # التأكد من عدم إضافة نفس الشفرة مرتين
            if not any(d['cw'] == structured_data['cw'] for d in database):
                database.append(structured_data)
            
    return database

if __name__ == "__main__":
    results = run_scraper()
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"تم بنجاح! تم حفظ {len(results)} شفرة.")
