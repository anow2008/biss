import requests
from bs4 import BeautifulSoup
import json
import os
import re

def parse_sat_data(text):
    # البحث عن شفرة CW أولاً كشرط أساسي
    cw_match = re.search(r'CW:\s*([A-F0-9 ]{17,23})', text, re.IGNORECASE)
    if not cw_match:
        return None  # إذا لم يجد شفرة، سيتجاهل المنشور تماماً

    data = {"raw_text": text}
    try:
        lines = text.split('\n')
        data['satellite'] = lines[0].strip()

        # استخراج التردد والاستقطاب ومعدل الترميز
        freq_match = re.search(r'(\d{5})\s+([VH])\s+(\d{4,5})', text)
        if freq_match:
            data['frequency'] = freq_match.group(1)
            data['polarity'] = freq_match.group(2)
            data['symbol_rate'] = freq_match.group(3)

        # استخراج الجودة والـ ID
        video_match = re.search(r'(\d{4}x\d{3,4})', text)
        data['resolution'] = video_match.group(1) if video_match else "N/A"
        
        id_match = re.search(r'ID:\s*(.*)', text)
        data['channel_id'] = id_match.group(1).split('\n')[0].strip() if id_match else "N/A"

        # إضافة الشفرة التي وجدها
        data['cw'] = cw_match.group(1).strip()
        
    except Exception as e:
        print(f"Error parsing text: {e}")
        return None
        
    return data

if __name__ == "__main__":
    file_name = 'feeds.json'
    url = "https://t.me/s/live_sat_feeds"
    
    # 1. تحميل البيانات القديمة
    database = []
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try: database = json.load(f)
            except: database = []

    # 2. سحب البيانات الجديدة
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    existing_raw = [item.get('raw_text') for item in database]
    added_count = 0

    for post in posts:
        content = post.get_text(separator="\n").strip()
        
        # تنفيذ الفلترة والتحليل
        structured_data = parse_sat_data(content)
        
        # الحفظ فقط إذا كانت البيانات صالحة وغير مكررة
        if structured_data and content not in existing_raw:
            database.append(structured_data)
            added_count += 1
            
    # 3. حفظ البيانات المنظمة
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
        
    print(f"تم الفحص! تم إضافة {added_count} شفرة جديدة.")
