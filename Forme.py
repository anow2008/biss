import requests
import re
import os

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"

def get_all_feeds():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        content = response.text
        
        # تقسيم الصفحة بناءً على الترددات (مثال: 12510 V 7500)
        cards = re.split(r'(\d{5}\s[VH]\s\d{4,5})', content)
        
        messages = []
        new_keys_found = []

        # قراءة الذاكرة
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        for i in range(1, len(cards), 2):
            freq_data = cards[i] # التردد
            text_block = cards[i+1][:800] # النص اللي بعد التردد

            # 1. استخراج القمر (Satellite)
            sat = "Unknown Sat"
            sat_match = re.search(r'([A-Za-z0-9\s\.\/]+)@', text_block)
            if sat_match:
                sat = sat_match.group(1).strip()

            # 2. استخراج الـ ID (Channel Name)
            channel_id = "Feed ID"
            # الموقع بيحط اسم القناة بعد كلمة ID في الغالب
            id_match = re.search(r'(?:ID|Id):\s?([^\n<]+)', text_block)
            if id_match:
                channel_id = id_match.group(1).strip()

            # 3. استخراج الشفرة (CW) - بياخد أي 16 رقم وجنبهم مسافات أو لا
            key_match = re.search(r'([A-Fa-f0-9]{2}(?:\s?[A-Fa-f0-9]{2}){7})', text_block)
            
            if key_match:
                raw_key = key_match.group(1).replace(" ", "").upper()
                
                # التأكد إنها شفرة جديدة وطولها 16
                if len(raw_key) == 16 and raw_key not in old_keys:
                    new_keys_found.append(raw_key)
                    
                    # التنسيق الإنجليزي اللي طلبته (14 1A C8...)
                    formatted_key = ' '.join(raw_key[k:k+2] for k in range(0, 16, 2))

                    msg = f"Sat: {sat}\n"
                    msg += f"Freq: {freq_data}\n"
                    msg += f"Id: {channel_id}\n"
                    msg += f"🔑 CW: {formatted_key}"
                    
                    messages.append(msg)

        # حفظ الجديد
        if new_keys_found:
            with open(DB_FILE, "a") as f:
                for k in new_keys_found:
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
    new_messages = get_all_feeds()
    if new_messages:
        send_to_telegram(new_messages)
        print(f"✅ Sent {len(new_messages)} updates.")
