import cloudscraper
import json
import os
import requests

TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/api/feeds" 
DB_FILE = "last_keys_list.txt"

def get_data():
    # استخدام سكريبر متطور لتخطي حماية الموقع
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        print("🔍 Trying to bypass protection...")
        response = scraper.get(URL, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Site error: {response.status_code}")
            return []

        feeds_list = response.json()
        print(f"✅ Success! Found {len(feeds_list)} items.")

        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w').close()

        with open(DB_FILE, "r") as f:
            old_keys = f.read().splitlines()

        messages = []
        new_keys = []

        for item in feeds_list:
            key = str(item.get('cw', '')).strip().upper()
            if len(key) == 16 and key not in old_keys:
                sat = item.get('sat', 'N/A')
                freq = item.get('freq', '0000')
                pol = item.get('pol', 'V')
                sr = item.get('sr', '0000')
                name = item.get('name', 'Feed')

                formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))
                msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {formatted_key}"
                
                messages.append(msg)
                new_keys.append(key)

        if new_keys:
            with open(DB_FILE, "a") as f:
                for nk in new_keys:
                    f.write(nk + "\n")
        return messages

    except Exception as e:
        print(f"Error: {e}")
        return []

def send_to_telegram(msgs):
    for m in msgs:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})

if __name__ == "__main__":
    results = get_data()
    if results:
        send_to_telegram(results)
