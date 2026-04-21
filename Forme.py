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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        content = response.text
        
        # دي أقوى طريقة بحث: بتدور على أي مصفوفة JSON شايلة بيانات "cw" 
        # مهما كان اسم المتغير (data, feeds, feedsData)
        json_pattern = r'(\[[\s\S]*?\{[\s\S]*?"cw"[\s\S]*?\}[\s\S]*?\])'
        json_match = re.search(json_pattern, content)
        
        if not json_match:
            print("❌ لم يتم العثور على مصفوفة البيانات في الصفحة")
            return []

        feeds_list = json.loads(json_match.group(1))
        messages = []
        
        # الذاكرة عشان ميبعتش نفس الحاجة مرتين
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        new_keys_to_save = []

        for item in feeds_list:
            # التأكد إن فيه شفرة وطولها 16
            key = str(item.get('cw', '')).strip().upper()
            if len(key) == 16:
                if key not in old_keys:
                    new_keys_to_save.append(key)
                    
                    sat = item.get('sat', 'Unknown Sat')
                    freq = item.get('freq', '00000')
                    pol = item.get('pol', 'V')
                    sr = item.get('sr', '0000')
                    name = item.get('name', 'Feed ID')

                    # تنسيق الشفرة بمسافات (14 1A C8...)
                    formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                    # التنسيق الإنجليزي اللي طلبته بالظبط
                    msg = f"Sat: {sat}\n"
                    msg += f"Freq: {freq} {pol} {sr}\n"
                    msg += f"Id: {name}\n"
                    msg += f"🔑 CW: {formatted_key}"
                    
                    messages.append(msg)

        if new_keys_to_save:
            with open(DB_FILE, "a") as f:
                for k in new_keys_to_save:
                    f.write(k + "\n")
                    
        return messages

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_to_telegram(msgs):
    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": m})

if __name__ == "__main__":
    results = get_all_feeds()
    if results:
        send_to_telegram(results)
        print(f"✅ Success: Sent {len(results)} feeds.")
    else:
        print("ℹ️ No new keys found right now.")
