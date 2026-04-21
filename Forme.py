import requests
import re
import json
import os

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"

def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        content = response.text
        
        # بنبحث عن أي مصفوفة [ ] فيها كلمة "cw" عشان نضمن السحب
        json_match = re.search(r'(\[[\s\S]*?\{[\s\S]*?"cw"[\s\S]*?\}[\s\S]*?\])', content)
        
        if not json_match:
            print("❌ ملقيتش بيانات في الصفحة")
            return []

        feeds_list = json.loads(json_match.group(1))
        
        # لو الملف مش موجود بنعمله عشان ميديناش Error في GitHub
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w") as f: f.write("")

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
                
                # التنسيق الإنجليزي النضيف
                msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {formatted_key}"
                messages.append(msg)
                new_keys.append(key)

        if new_keys:
            with open(DB_FILE, "a") as f:
                for nk in new_keys: f.write(nk + "\n")
                    
        return messages
    except Exception as e:
        print(f"Error: {e}")
        return []

def send(msgs):
    for m in msgs:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})

if __name__ == "__main__":
    results = get_data()
    if results:
        send(results)
