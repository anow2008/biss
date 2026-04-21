import requests
import re
import json

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"

def get_data_now():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        # 1. سحب الصفحة
        print("🔍 Connecting...")
        r = requests.get(URL, headers=headers, timeout=20)
        content = r.text
        
        # 2. البحث عن أي مصفوفة فيها شفرات (cw) مهما كان اسم المتغير
        # الطريقة دي بتجيب الداتا حتى لو الموقع مغير اسمها
        match = re.search(r'(\[[\s\S]*?\{[\s\S]*?"cw"[\s\S]*?\}[\s\S]*?\])', content)
        
        if not match:
            print("❌ No Data Found in Page Source")
            return

        feeds = json.loads(match.group(1))
        print(f"✅ Found {len(feeds)} items")

        for item in feeds:
            key = str(item.get('cw', '')).strip().upper()
            
            # لو لقينا شفرة طولها 16 حرف
            if len(key) == 16:
                sat = item.get('sat', 'N/A')
                freq = item.get('freq', '0000')
                pol = item.get('pol', 'V')
                sr = item.get('sr', '0000')
                name = item.get('name', 'Feed')

                # تنسيق الشفرة (14 1A C8...)
                fmt_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                # الرسالة الإنجليزي اللي طلبتها
                msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {fmt_key}"
                
                # إرسال فوري لتلجرام (عشان نتأكد إن السحب شغال)
                t_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                requests.post(t_url, data={"chat_id": CHAT_ID, "text": msg})
                print(f"🚀 Sent: {name}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_data_now()
