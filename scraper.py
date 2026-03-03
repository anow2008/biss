import requests
from bs4 import BeautifulSoup
import json
import re

def parse_sat_data(text):
    # بحث مرن جداً عن الشفرة
    cw_match = re.search(r'CW:?\s*([A-F0-9\s]{15,})', text, re.IGNORECASE)
    if not cw_match:
        return None

    data = {"raw_text": text}
    try:
        lines = text.split('\n')
        data['satellite'] = lines[0].strip() if lines else "Unknown"
        
        # البحث عن التردد
        freq_match = re.search(r'(\d{5})', text)
        data['frequency'] = freq_match.group(1) if freq_match else "N/A"
        
        data['cw'] = cw_match.group(1).strip()
    except:
        return None
    return data

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    # إضافة User-Agent لتبدو كمتصفح حقيقي
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("جاري الاتصال بتليجرام...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"فشل الاتصال! الكود: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # محاولة البحث عن الرسائل بأكثر من طريقة (كلاسات مختلفة)
    posts = soup.select('.tgme_widget_message_text')
    
    print(f"تم العثور على {len(posts)} منشور في الصفحة.")
    
    database = []
    for post in posts:
        content = post.get_text(separator="\n").strip()
        # طباعة أول 20 حرف للتأكد أن السكربت يرى النصوص فعلاً
        print(f"تحليل منشور: {content[:30]}...") 
        
        structured_data = parse_sat_data(content)
        if structured_data:
            database.append(structured_data)
            
    return database

if __name__ == "__main__":
    results = run_scraper()
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"تم حفظ {len(results)} شفرة في feeds.json")
