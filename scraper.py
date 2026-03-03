import requests
from bs4 import BeautifulSoup
import json
import os

def get_telegram_feeds():
    url = "https://t.me/s/live_sat_feeds"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    new_messages = []
    posts = soup.find_all('div', class_='tgme_widget_message_bubble')
    
    for post in posts:
        text_area = post.find('div', class_='tgme_widget_message_text')
        if text_area:
            content = text_area.get_text(separator="\n").strip()
            new_messages.append(content)
            
    return new_messages

if __name__ == "__main__":
    file_name = 'feeds.json'
    
    # 1. قراءة البيانات القديمة لو الملف موجود
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                database = json.load(f)
            except:
                database = []
    else:
        database = []

    # 2. سحب البيانات الجديدة من القناة
    latest_posts = get_telegram_feeds()

    # 3. إضافة المنشورات الجديدة فقط (منع التكرار)
    added_count = 0
    for post in latest_posts:
        if post not in database:
            database.append(post)
            added_count += 1
            
    # 4. حفظ الكل في الملف من جديد
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
        
    print(f"تمت العملية! أضفنا {added_count} تردد جديد. المجموع الكلي: {len(database)}")
