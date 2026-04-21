import requests
from bs4 import BeautifulSoup
import re
import os

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"
DB_FILE = "last_keys_list.txt"

def get_all_feeds():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن نصوص الصفحة لتحليلها
        content = response.text
        
        # تقسيم الصفحة لقطع بناءً على الترددات لاصطياد بيانات كل كارت لوحده
        cards = re.split(r'(\d{5}\s[VH]\s\d{4,5})', content)
        
        messages = []
        new_keys_found = []

        # قراءة الشفرات القديمة لمنع التكرار
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        # تحليل كل كارت مستخرج
        for i in range(1, len(cards), 2):
            freq_data = cards[i] # التردد
            text_after_freq = cards[i+1][:500] # النص اللي بعد التردد (فيه القمر والشفرة)

            # استخراج اسم القمر (مثال: Eutelsat 7A/7B/7C)
            satellite = "Unknown Satellite"
            sat_match = re.search(r'[A-Za-z0-9\s\.\/]+(?=\s@)', text_after_freq)
            if sat_match:
                satellite = sat_match.group(0).strip()

            # استخراج اسم القناة أو الحدث (غالباً يكون بجانب أيقونة ID في الموقع)
            channel_name = "Feed Channel"
            # البحث عن نصوص مميزة للأسماء
            name_match = re.search(r'ID:\s?([^\n]+)', text_after_freq)
            if name_match:
                channel_name = name_match.group(1).strip()

            # استخراج الشفرة
            key_match = re.search(r'[A-Fa-f0-9]{2}(?:\s[A-Fa-f0-9]{2}){7}', text_after_freq)
            
            if key_match:
                full_key = key_match.group(0).replace(" ", "").upper()
                
                # التحقق إذا كانت الشفرة جديدة
                if full_key not in old_keys:
                    new_keys_found.append(full_key)
                    
                    # صياغة الرسالة بالتنسيق الذي طلبته
                    msg = f"""
📡 **اسم القمر:** {satellite}
📊 **التردد:** {freq_data}
📺 **اسم القناة:** {channel_name}
🔑 **الشفرة:** `{full_key}`
________________________
"""
                    messages.append(msg)

        # حفظ الشفرات الجديدة في الذاكرة
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
        requests.post(url, data={"chat_id": CHAT_ID, "text": m, "parse_mode": "Markdown"})

if __name__ == "__main__":
    new_messages = get_all_feeds()
    if new_messages:
        send_to_telegram(new_messages)
        print(f"✅ تم إرسال {len(new_messages)} تحديث جديد.")
    else:
        print("ℹ️ لا توجد شفرات جديدة حالياً.")
