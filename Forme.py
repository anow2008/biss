import cloudscraper
import re
import json
import os
import requests

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"

def get_all_feeds():
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    ) 
    try:
        print("🌐 Connecting to Live-Feed...")
        response = scraper.get(URL, timeout=30)
        content = response.text
        
        # البحث عن مصفوفة البيانات بأي اسم متغير (feedsData أو data أو feeds)
        json_match = re.search(r'=\s*(\[[\s\S]*?\]);', content)
        
        if not json_match:
            print("❌ Could not find data array in page source.")
            return []

        feeds_list = json.loads(json_match.group(1))
        print(f"📊 Found {len(feeds_list)} cards on site.")
        
        messages = []
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        new_keys_found = []

        for item in feeds_list:
            key = item.get('cw', '').strip().upper()
            
            # التأكد إنها شفرة BISS (16 حرف)
            if key and len(key) == 16:
                if key not in old_keys:
                    new_keys_found.append(key)
                    
                    sat = item.get('sat', 'Unknown Sat')
                    freq = item.get('freq', '00000')
                    pol = item.get('pol', 'V')
                    sr = item.get('sr', '0000')
                    name = item.get('name', 'Feed ID')

                    formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                    # التنسيق الإنجليزي اللي طلبته
                    msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {formatted_key}"
                    messages.append(msg)
                    
        if new_keys_found:
            with open(DB_FILE, "a") as f:
                for k in new_keys_found:
                    f.write(k + "\n")
                    
        return messages

    except Exception as e:
        print(f"❌ Python Error: {e}")
        return []

def send_to_telegram(msgs):
    if not msgs:
        print("ℹ️ Everything is up-to-date. No new keys.")
        return

    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": m})
        print(f"✅ Sent to Telegram.")

if __name__ == "__main__":
    results = get_all_feeds()
    send_to_telegram(results)
