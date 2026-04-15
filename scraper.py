import requests
from bs4 import BeautifulSoup
import json
import re

def clean_text(text):
    """تنظيف النص من القرف والرموز اللي بتبوظ الـ JSON"""
    if not text: return ""
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # السماح فقط بالحروف والأرقام وعلامات التردد
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def extract_feeds():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        print("جاري الاتصال بالقناة... يارب يشتغل")
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"فشل الاتصال: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    # بندور على كل الرسائل في الصفحة
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    final_data = []
    
    for post in posts:
        content = post.get_text(separator="\n").strip()
        
        # 1. بندور على الشفرة (16 حرف Hex) في أي داهية داخل البلوك
        key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
        key_match = key_pattern.search(content)
        
        if key_match:
            # تنظيف وتنسيق الشفرة
            raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
            formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])
            
            # 2. سحب القمر والتردد والـ ID بطريقة بدائية ومباشرة
            sat = "Unknown"
            freq = "N/A"
            cid = "N/A"
            
            lines = content.split('\n')
            for line in lines:
                if '📡' in line: sat = clean_text(line.replace('📡', ''))
                if '📶' in line: freq = clean_text(line.replace('📶', ''))
                if '🆔' in line: cid = clean_text(line.replace('🆔', ''))
            
            # 3. بناء الداتا لبلجن BissPro-Smart
            entry = {
                "satellite": sat,
                "frequency": freq,
                "id": cid,
                "key": formatted_key
            }
            
            # منع التكرار
            if not any(d['key'] == formatted_key for d in final_data):
                final_data.insert(0, entry) # الأحدث فوق

    return final_data

if __name__ == "__main__":
    results = extract_feeds()
    
    # مسح الملف وكتابة الجديد
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"الحمد لله! سحب {len(results)} بلوك شفرات.")
    else:
        print("لسه الملف فاضي؟ يبقى تليجرام حاجب الـ IP بتاعك أو الصفحة مش راضية تحمل.")
