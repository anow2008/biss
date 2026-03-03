import requests
from bs4 import BeautifulSoup
import json
import os
import re

def parse_sat_data(text):
    # نمط بحث مرن: يبحث عن #CW: متبوعة بأرقام وحروف ومسافات
    # التعديل هنا ليتناسب مع: #CW: D0 30 3E 3E 58 FF AF 06
    cw_match = re.search(r'#CW:\s*([A-F0-9\s]{16,24})', text, re.IGNORECASE)
    
    if not cw_match:
        return None

    data = {"raw_text": text}
    try:
        lines = text.split('\n')
        data['satellite'] = lines[0].strip()

        # استخراج التردد والاستقطاب
        freq_match = re.search(r'(\d{5})\s+([VH])', text)
        if freq_match:
            data['frequency'] = freq_match.group(1)
            data['polarity'] = freq_match.group(2)

        # استخراج الشفرة وتنظيفها من المسافات الزائدة
        data['cw'] = cw_match.group(1).strip()
        
    except Exception:
        return None
        
    return data

if __name__ == "__main__":
    file_name = 'feeds.json'
    url = "https://t.me/s/live_sat_feeds"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # استهداف حاويات الرسائل في تليجرام ويب
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # إذا كنت تريد الحفاظ على القديم، فك تفعيل السطور القادمة
    # if os.path.exists(file_name):
    #     with open(file_name, 'r', encoding='utf-8') as f:
    #         database = json.load(f)

    for post in posts:
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        if structured_data:
            # منع التكرار
            if not any(d.get('cw') == structured_data['cw'] for d in database):
                database.append(structured_data)
            
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
        
    print(f"تم! تم العثور على {len(database)} شفرة.")
