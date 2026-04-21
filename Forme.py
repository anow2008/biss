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
    # استخدام سكريبر متقدم
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    ) 
    try:
        print("🌐 Connecting to Live-Feed...")
        response = scraper.get(URL, timeout=30)
        content = response.text
        
        # الطريقة الجديدة: البحث عن أي نص يشبه مصفوفة JSON فيها مفتاح "cw"
        # دي بتصطاد الداتا حتى لو الموقع غير اسم المتغير 100 مرة
        json_match = re.search(r'(\[[\s\S]*?\{[\s\S]*?"cw"[\s\S]*?\}[\s\S]*?\])', content)
        
        if not json_match:
            print("❌ Data not found in page source. Checking backup method...")
            # محاولة أخيرة للبحث عن أي مصفوفة تبدأ بـ [
            json_match = re.search(r'=\s*(\[[\s\S]*?\]);', content)

        if not json_match:
            return []

        feeds_list = json.loads(json_match.group(1))
        print(f"📊 Found {len(feeds_list)} cards.")
        
        messages = []
        # قراءة الذاكرة
        old_keys = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read().splitlines()

        new_keys_to_save = []

        for item in feeds_list:
            key = str(item.get('cw', '')).strip().upper()
            
            # التأكد إنها شفرة BISS (16 رقم)
            if len(key) == 16:
                if key not in old_keys:
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
                    new_keys_to_save.append(key)
                    
        # حفظ الشفرات الجديدة لمنع التكرار
        if new_keys_to_save:
            with open(DB_FILE, "a") as f:
                for k in new_keys_to_save:
                    f.write(k + "\n")
                    
        return messages

    except Exception as e:
        print(f"❌ Python Error: {e}")
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
