import requests
from bs4 import BeautifulSoup
import json

def get_telegram_feeds():
    url = "https://t.me/s/live_sat_feeds"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    messages = []
    # البحث عن حاويات الرسائل في نسخة الويب
    posts = soup.find_all('div', class_='tgme_widget_message_bubble')
    
    for post in posts:
        text_area = post.find('div', class_='tgme_widget_message_text')
        if text_area:
            content = text_area.get_text(separator="\n")
            messages.append({"content": content})
            
    return messages

if __name__ == "__main__":
    data = get_telegram_feeds()
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Done! Scraped {len(data)} posts.")
