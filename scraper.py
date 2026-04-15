import requests
from bs4 import BeautifulSoup
import json
import re

def super_clean(text):
    """تنظيف جراحي للنص لإزالة كل الرموز المخفية"""
    if not text: return ""
    # إزالة المسافات الغريبة بكل أنواعها
    text = re.sub(r'\s+', ' ', text)
    # الإبقاء فقط على الحروف والأرقام وعلامات التردد والدرجة
    clean = re.sub(r'[^\w\s\d\.\-\/°@]', '', text)
    return clean.strip()

def extract_feeds():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    final_data = []
    
    for post in posts:
        # تحويل البلوك لنص مقسم لأسطر
        content = post.get_text(separator="\n")
        
        # البحث عن الشفرة أولاً (16 حرف هكس)
        key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
        key_match = key_pattern.search(content)
        
        if key_match:
            raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
            formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])
            
            sat, freq, cid = "Unknown", "N/A", "N/A"
            
            # فحص كل سطر في المنشور
            lines = content.split('\n')
            for line in lines:
                line_clean = line.strip()
                # إذا السطر فيه رمز القمر، خد اللي بعده ونظفه
                if '📡' in line_clean:
                    sat = super_clean(line_clean.split('📡')[-1])
                # إذا السطر فيه رمز الإشارة، خد اللي بعده
                elif '📶' in line_clean:
                    freq = super_clean(line_clean.split('📶')[-1])
                # إذا السطر فيه رمز الهوية، خد اللي بعده
                elif '🆔' in line_clean:
                    cid = super_clean(line_clean.split('🆔')[-1])

            # بناء الحقول الأربعة لبلجن BissPro-Smart
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
    
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        # طباعة مثال للتأكد من البيانات قبل قفل السكربت
        print(f"✅ تم سحب {len(results)} بلوك بنجاح.")
        print(f"آخر قمر تم سحبه: {results[0]['satellite']}")
    else:
        print("⚠️ الملف لسه فاضي.. جرب تفتح اللينك في المتصفح وشوف القناة شغالة ولا لا.")
