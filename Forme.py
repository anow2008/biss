import requests
import json
import os

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
# ده الرابط اللي الموقع بيسحب منه البيانات فعلياً
URL = "https://live-feed.net/api/feeds" 
DB_FILE = "last_keys_list.txt"

def get_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json' # إحنا بنطلب JSON مباشر
    }
    try:
        print("🔗 Connecting to API...")
        response = requests.get(URL, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Site rejected request: {response.status_code}")
            return []

        # الموقع بيبعت الداتا جاهزة في الـ JSON
        feeds_list = response.json()
        print(f"✅ Found {len(feeds_list)} cards.")

        # قراءة الذاكرة
        old_keys = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read().splitlines()

        messages = []
        new_keys = []

        for item in feeds_list:
            key = str(item.get('cw', '')).strip().upper()
            
            # لو الشفرة 16 حرف ومش موجودة عندنا قبل كده
            if len(key) == 16 and key not in old_keys:
                sat = item.get('sat', 'N/A')
                freq = item.get('freq', '00000')
                pol = item.get('pol', 'V')
                sr = item.get('sr', '0000')
                name = item.get('name', 'Feed')

                # تنسيق الشفرة بمسافات كما طلبت
                formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                # التنسيق الإنجليزي بالمللي
                msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {formatted_key}"
                
                messages.append(msg)
                new_keys.append(key)

        # حفظ الشفرات الجديدة
        if new_keys:
            with open(DB_FILE, "a") as f:
                for nk in new_keys:
                    f.write(nk + "\n")
                    
        return messages

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_to_telegram(msgs):
    for m in msgs:
        api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(api_url, data={"chat_id": CHAT_ID, "text": m})
        print("🚀 Message Sent!")

if __name__ == "__main__":
    results = get_data()
    if results:
        send_to_telegram(results)
    else:
        print("ℹ️ No new keys or site is empty.")
