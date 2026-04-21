import requests
from bs4 import BeautifulSoup
import re
import os
import json

# --- الإعدادات (اسحبها من الـ Secrets لأمانك) ---
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"
JSON_FILE = "for me.json"

def update_json_file(new_data_list):
    current_data = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except:
            current_data = []
    # إضافة الجديد في الأول
    updated_data = new_data_list + current_data
    updated_data = updated_data[:100]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)

def get_feeds():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(URL, headers=headers, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # التعديل الجوهري: البحث عن كل بلوك شفرة بشكل مباشر
        cards = soup.find_all('div', class_='text-gray-600')
        
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        messages = []
        new_keys = []
        json_entries = []

        for card in cards:
            text = card.get_text(separator='|')
            
            # البحث عن الشفرة (CW)
            key_m = re.search(r'([A-Fa-f0-9]{2}(?:\s?[A-Fa-f0-9]{2}){7})', text)
            if key_m:
                raw_key = key_m.group(1).replace(" ", "").upper()
                
                # لو الشفرة جديدة
                if len(raw_key) == 16 and raw_key not in old_keys:
                    # سحب القمر
                    sat = "Satellite Feed"
                    sat_m = re.search(r'([^|]+@[^|]+)', text)
                    if sat_m: sat = sat_m.group(1).strip()

                    # سحب التردد
                    freq = "00000 V 0000"
                    freq_m = re.search(r'(\d{5}\s?[VH]\s?\d{4,5})', text)
                    if freq_m: freq = freq_m.group(1).strip()

                    # سحب الـ ID
                    channel = "Feed"
                    id_m = re.search(r'🆔\s*\|?([^|]+)', text)
                    if id_m: channel = id_m.group(1).strip()

                    fmt_key = ' '.join(raw_key[i:i+2] for i in range(0, 16, 2))
                    
                    messages.append(f"🛰 Sat: {sat}\n📡 Freq: {freq}\n🆔 Id: {channel}\n🔑 CW: {fmt_key}")
                    
                    json_entries.append({
                        "satellite": sat,
                        "frequency": freq,
                        "id": channel,
                        "key": fmt_key
                    })
                    new_keys.append(raw_key)

        if new_keys:
            with open(DB_FILE, "a") as f:
                for k in new_keys: f.write(k + "\n")
            update_json_file(json_entries)
            print(f"✅ Found {len(new_keys)} keys")
        return messages
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    results = get_feeds()
    if TOKEN and CHAT_ID:
        for m in results:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})
