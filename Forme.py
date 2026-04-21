import requests
import re
import json
import os

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"

def get_all_feeds():
    # هيدرز قوية لمحاكاة متصفح حقيقي
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        session = requests.Session()
        print("🌐 Connecting to site...")
        response = session.get(URL, headers=headers, timeout=30)
        content = response.text
        
        # البحث عن مصفوفة البيانات JSON بأي اسم متغير
        json_match = re.search(r'=\s*(\[[\s\S]*?\{[\s\S]*?"cw"[\s\S]*?\}[\s\S]*?\])', content)
        
        if not json_match:
            print("❌ Data not found in page. Site might be blocking.")
            return []

        feeds_list = json.loads(json_match.group(1))
        print(f"📊 Found {len(feeds_list)} potential feeds.")
        
        messages = []
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        new_keys_found = []

        for item in feeds_list:
            key = str(item.get('cw', '')).strip().upper()
            
            # التأكد إنها شفرة BISS (16 رقم)
            if len(key) == 16:
                if key not in old_keys:
                    new_keys_found.append(key)
                    
                    sat = item.get('sat', 'Unknown Sat')
                    freq = item.get('freq', '00000')
                    pol = item.get('pol', 'V')
                    sr = item.get('sr', '0000')
                    name = item.get('name', 'Feed ID')

                    # تنسيق الشفرة بمسافات (14 1A C8...)
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
        print(f"❌ Error: {e}")
        return []

def send_to_telegram(msgs):
    if not msgs:
        print("ℹ️ No new keys to send.")
        return

    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": m})
        print(f"✅ Sent to Telegram.")

if __name__ == "__main__":
    results = get_all_feeds()
    send_to_telegram(results)
