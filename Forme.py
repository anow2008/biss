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
    # إنشاء سكريبر يتخطى حماية Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    ) 
    try:
        print("🔍 Connecting to site...")
        response = scraper.get(URL, timeout=30)
        content = response.text
        
        # البحث عن مصفوفة البيانات JSON
        json_data_match = re.search(r'data\s+=\s+(\[.*?\]);', content, re.DOTALL)
        
        if not json_data_match:
            print("⚠️ Data not found - Site might be blocking or changed layout.")
            return []

        feeds_list = json.loads(json_data_match.group(1))
        messages = []
        
        # قراءة الشفرات المرسلة سابقاً
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        new_keys_found = []

        for item in feeds_list:
            key = item.get('cw', '').strip().upper()
            
            # سحب الشفرات الـ 16 حرف
            if key and len(key) == 16:
                if key not in old_keys: # التأكد إنها شفرة جديدة
                    new_keys_found.append(key)
                    
                    sat = item.get('sat', 'Unknown')
                    freq = item.get('freq', '00000')
                    pol = item.get('pol', 'V')
                    sr = item.get('sr', '0000')
                    name = item.get('name', 'Feed')

                    # تنسيق الشفرة بمسافات (14 1A C8...)
                    formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                    # التنسيق الإنجليزي اللي طلبته
                    msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {formatted_key}"
                    messages.append(msg)
                    
        # حفظ الشفرات الجديدة في الملف
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
        print("ℹ️ No NEW feeds found.")
        return

    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": m})
        if r.status_code == 200:
            print(f"✅ Message sent successfully!")
        else:
            print(f"❌ Telegram Error: {r.status_code}")

if __name__ == "__main__":
    results = get_all_feeds()
    send_to_telegram(results)
