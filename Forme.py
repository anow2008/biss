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
        
        # تقسيم الصفحة بناءً على شكل التردد (الرقم اللي بيبدأ بـ 10 أو 11 أو 12)
        cards = re.split(r'(\d{5}\s[VH]\s\d{4,5})', content)
        
        messages = []
        new_keys_found = []

        # الذاكرة
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        for i in range(1, len(cards), 2):
            freq_val = cards[i] # التردد (12510 V 7500)
            text_after = cards[i+1][:1000] # النص اللي بعد التردد

            # 1. سحب اسم القمر: بيدور على النص اللي آخره علامة @
            # بياخد الكلام اللي قبل الـ @ علطول
            sat_name = "Unknown Sat"
            sat_match = re.search(r'([A-Za-z0-9\s\.\/\-]+)\s?@', text_after)
            if sat_match:
                sat_name = sat_match.group(1).strip()

            # 2. سحب الـ ID: بيدور على النص اللي بعد أيقونة الـ ID أو كلمة ID
            channel_id = "Feed ID"
            id_match = re.search(r'(?:ID|Id|🆔):\s?([^\n<]+)', text_after)
            if id_match:
                channel_id = id_match.group(1).strip()

            # 3. سحب الشفرة (16 حرف)
            key_match = re.search(r'([A-Fa-f0-9]{2}(?:\s?[A-Fa-f0-9]{2}){7})', text_after)
            
            if key_match:
                clean_key = key_match.group(1).replace(" ", "").upper()
                
                if len(clean_key) == 16 and clean_key not in old_keys:
                    new_keys_found.append(clean_key)
                    
                    # تنسيق الشفرة بمسافات
                    formatted_key = ' '.join(clean_key[k:k+2] for k in range(0, 16, 2))

                    # التنسيق الإنجليزي اللي إنت عايزه
                    msg = f"Sat: {sat_name}\n"
                    msg += f"Freq: {freq_val}\n"
                    msg += f"Id: {channel_id}\n"
                    msg += f"🔑 CW: {formatted_key}"
                    
                    messages.append(msg)

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
    results = get_all_feeds()
    if results:
        send_to_telegram(results)
        print(f"✅ Done! Sent {len(results)} feeds.")
