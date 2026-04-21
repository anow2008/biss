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
        
        # تقسيم الصفحة لقطع بناءً على أيقونة القمر أو اسم القمر
        # بنقسم الصفحة "كروت" عشان كل كارت يبقى لوحده
        cards = re.split(r'📡', content)
        
        messages = []
        new_keys_found = []

        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()
        else:
            old_keys = ""

        for card in cards[1:]: # بنبدأ من بعد أول تقسيم
            # 1. سحب اسم القمر (بيكون في أول السطر قبل علامة @)
            sat_match = re.search(r'([A-Za-z0-9\s\.\/\-]+)\s?@', card)
            sat = sat_match.group(1).strip() if sat_match else "Unknown Sat"

            # 2. سحب التردد (النمط المشهور 5 أرقام ثم V/H ثم 4-5 أرقام)
            freq_match = re.search(r'(\d{5}\s[VH]\s\d{4,5})', card)
            freq = freq_match.group(1).strip() if freq_match else "00000 V 0000"

            # 3. سحب الـ ID (بيكون بعد أيقونة 🆔 أو كلمة ID)
            id_match = re.search(r'(?:🆔|ID|Id):\s?([^\n<]+)', card)
            channel_id = id_match.group(1).strip() if id_match else "Feed ID"

            # 4. سحب الشفرة (16 حرف)
            key_match = re.search(r'([A-Fa-f0-9]{2}(?:\s?[A-Fa-f0-9]{2}){7})', card)
            
            if key_match:
                clean_key = key_match.group(1).replace(" ", "").upper()
                
                # لو الشفرة جديدة
                if len(clean_key) == 16 and clean_key not in old_keys:
                    new_keys_found.append(clean_key)
                    
                    # تنسيق الشفرة بمسافات
                    fmt_key = ' '.join(clean_key[k:k+2] for k in range(0, 16, 2))

                    # التنسيق اللي إنت عايزه بالمللي
                    msg = f"Sat: {sat}\n"
                    msg += f"Freq: {freq}\n"
                    msg += f"Id: {channel_id}\n"
                    msg += f"🔑 CW: {fmt_key}"
                    
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
        print(f"✅ Sent {len(results)} feeds.")
