import requests
import re
import json
import os

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"

def get_all_feeds_english():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        content = response.text
        
        # البحث عن مصفوفة البيانات في كود الصفحة
        json_data_match = re.search(r'const\s+data\s+=\s+(\[.*?\]);', content, re.DOTALL)
        if not json_data_match:
            json_data_match = re.search(r'let\s+feeds\s+=\s+(\[.*?\]);', content, re.DOTALL)
        
        if not json_data_match:
            return []

        feeds_list = json.loads(json_data_match.group(1))
        
        messages = []
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        new_keys_to_save = []

        # هيلف على كل الداتا ويطلع أي شفرة 16 رقم
        for item in feeds_list:
            key = item.get('cw', '').strip().upper()
            
            if key and len(key) == 16:
                if key not in old_keys:
                    new_keys_to_save.append(key)
                    
                    sat = item.get('sat', 'Unknown')
                    freq = item.get('freq', '00000')
                    pol = item.get('pol', 'V')
                    sr = item.get('sr', '0000')
                    name = item.get('name', 'Feed')

                    # تنسيق الشفرة بمسافات (14 1A C8...)
                    formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                    # التنسيق الإنجليزي النهائي زي ما طلبت يا محمد
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
        print(f"Error: {e}")
        return []

def send_to_telegram(msgs):
    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": m})

if __name__ == "__main__":
    all_msgs = get_all_feeds_english()
    if all_msgs:
        send_to_telegram(all_msgs)
