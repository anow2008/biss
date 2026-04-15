 import requests
from bs4 import BeautifulSoup
import json
import re

def clean_value(text):
    """تنظيف القيم الناتجة من أي رموز تعبيرية أو مسافات زائدة"""
    if not text: return ""
    # استبدال المسافات المخفية بمسافات عادية
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # حذف الرموز التعبيرية والإبقاء على النص والأرقام والدرجة °
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
        # استخراج النص مع الحفاظ على الأسطر
        content = post.get_text(separator="\n").strip()
        
        # 1. البحث عن الشفرة (16 حرف هكس)
        key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
        key_match = key_pattern.search(content)
        
        if key_match:
            raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
            formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])
            
            sat, freq, cid = "Unknown", "N/A", "N/A"
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            
            # تحديد السطر الذي يحتوي على الشفرة لنتعرف على ما قبله
            key_line_index = -1
            for i, line in enumerate(lines):
                if key_match.group(0) in line:
                    key_line_index = i
                    break

            for i, line in enumerate(lines):
                # كشف القمر: السطر اللي فيه @ أو أسماء أقمار
                if '@' in line or any(s in line.lower() for s in ['eutelsat', 'astra', 'intelsat', 'nilesat']):
                    sat = clean_value(line)
                
                # كشف التردد: السطر اللي فيه 5 أرقام و H أو V
                elif re.search(r'\d{5}\s+[HV]\s+\d+', line):
                    freq = clean_value(line)
                
                # كشف الـ ID: 
                # أولاً: لو فيه رمز 🆔
                if '🆔' in line:
                    cid = clean_value(line.replace('🆔', ''))
            
            # ثانياً: لو لسه الـ ID مجهول، خد السطر اللي قبل الشفرة مباشرة (ده الأضمن)
            if (cid == "N/A" or cid == "") and key_line_index > 0:
                # نتأكد إن السطر اللي قبله مش هو التردد أو القمر
                potential_id = lines[key_line_index - 1]
                if '📶' not in potential_id and '📡' not in potential_id and '@' not in potential_id:
                    cid = clean_value(potential_id)

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
    results = extract_feeds()
    
    # مسح الملف القديم تماماً وكتابة الجديد ببيانات كاملة
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ مبروك! تم سحب {len(results)} بلوك ببيانات كاملة (بما فيها اسم القناة).")
    else:
        print("⚠️ لم يتم العثور على بيانات.")
