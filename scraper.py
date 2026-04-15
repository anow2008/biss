import requests
from bs4 import BeautifulSoup
import json
import re

def clean_value(text):
    """تنظيف القيم الناتجة من أي رموز تعبيرية أو مسافات زائدة"""
    if not text: return ""
    # حذف أي رموز تعبيرية أو رموز خاصة والإبقاء على النص والأرقام
    clean = re.sub(r'[^\w\s\d\.\-\/°@]', '', text)
    return clean.strip()

def extract_feeds():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"خطأ في الاتصال: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    final_data = []
    
    for post in posts:
        content = post.get_text(separator="\n").strip()
        
        # 1. البحث عن الشفرة (16 حرف هكس) - هذا هو المحرك الأساسي
        key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
        key_match = key_pattern.search(content)
        
        if key_match:
            raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
            formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])
            
            # قيم افتراضية
            sat, freq, cid = "Unknown", "N/A", "N/A"
            
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            
            for i, line in enumerate(lines):
                # كشف القمر: السطر الذي يحتوي على علامة @ أو كلمة Eutelsat/Astra
                if '@' in line or any(s in line.lower() for s in ['eutelsat', 'astra', 'intelsat', 'nilesat']):
                    sat = clean_value(line)
                
                # كشف التردد: السطر الذي يبدأ بأرقام (مثل 10982) ويحتوي على H أو V
                elif re.search(r'\d{5}\s+[HV]\s+\d+', line):
                    freq = clean_value(line)
                
                # كشف الـ ID: السطر الذي يسبق سطر الشفرة مباشرة أو يحتوي على FEED
                elif 'FEED' in line.upper() or 'M0' in line.upper():
                    cid = clean_value(line)
            
            # إذا فشل كشف الـ ID بالطريقة السابقة، نأخذ السطر الذي يسبق الشفرة مباشرة
            if cid == "N/A":
                for i, line in enumerate(lines):
                    if key_match.group(0) in line and i > 0:
                        cid = clean_value(lines[i-1])

            entry = {
                "satellite": sat,
                "frequency": freq,
                "id": cid,
                "key": formatted_key
            }
            
            if not any(d['key'] == formatted_key for d in final_data):
                final_data.insert(0, entry)

    return final_data

if __name__ == "__main__":
    results = run_scraper_logic = extract_feeds()
    
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ مبروك! تم سحب {len(results)} بلوك ببيانات كاملة.")
    else:
        print("⚠️ الصفحة لم تعثر على شفرات. تأكد أن المتصفح يرى القناة.")
