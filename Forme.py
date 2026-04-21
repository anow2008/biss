import requests
from bs4 import BeautifulSoup
import re
import os

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"

def get_clean_feeds():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # بنلاقي كل "كارت" في الموقع
        # الموقع بيستخدم div كلاس card أو صفوف في جدول
        content = response.text
        cards = re.split(r'📡', content)
        
        messages = []
        new_keys_found = []

        # الذاكرة
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        for card_html in cards[1:]:
            # تحويل القطعة لـ BeautifulSoup عشان نعرف نتحكم فيها
            item = BeautifulSoup(card_html, 'html.parser')
            text_only = item.get_text(separator='|')

            # 1. اسم القمر (قبل علامة @)
            sat_match = re.search(r'([A-Za-z0-9\s\.\/\-]+)\s?@', text_only)
            sat = sat_match.group(1).strip() if sat_match else "Unknown Sat"

            # 2. التردد
            freq_match = re.search(r'(\d{5}\s[VH]\s\d{4,5})', text_only)
            freq = freq_match.group(1).strip() if freq_match else "00000 V 0000"

            # 3. اسم القناة (الـ ID) - بنصطاد النص اللي بين أيقونة الـ ID والسطر اللي بعده
            # بنهمل أي حاجة فيها snapshot أو { }
            channel_id = "Feed"
            id_patterns = [r'🆔\s*([^|]+)', r'ID:\s*([^|]+)', r'Id:\s*([^|]+)']
            for p in id_patterns:
                m = re.search(p, text_only)
                if m:
                    temp_id = m.group(1).strip()
                    if "snapshot" not in temp_id and "{" not in temp_id:
                        channel_id = temp_id
                        break

            # 4. الشفرة (CW)
            key_match = re.search(r'([A-Fa-f0-9]{2}(?:\s[A-Fa-f0-9]{2}){7})', text_only)
            
            if key_match:
                raw_key = key_match.group(1).replace(" ", "").upper()
                
                if len(raw_key) == 16 and raw_key not in old_keys:
                    new_keys_found.append(raw_key)
                    fmt_key = ' '.join(raw_key[k:k+2] for k in range(0, 16, 2))

                    # التنسيق النهائي النضيف
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

def send(msgs):
    for m in msgs:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})

if __name__ == "__main__":
    results = get_clean_feeds()
    if results:
        send(results)
