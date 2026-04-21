import requests
import json

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
# الرابط المباشر اللي شايل الداتا الخام
API_URL = "https://live-feed.net/api/feeds"

def get_live_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://live-feed.net/'
    }
    try:
        print("🔍 سحب البيانات من السيرفر مباشرة...")
        response = requests.get(API_URL, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ الموقع رفض الطلب: {response.status_code}")
            return

        feeds = response.json()
        print(f"✅ تم العثور على {len(feeds)} قناة.")

        for item in feeds:
            key = str(item.get('cw', '')).strip().upper()
            
            # التأكد إنها شفرة BISS (16 حرف)
            if len(key) == 16:
                sat = item.get('sat', 'N/A')
                freq = item.get('freq', '0000')
                pol = item.get('pol', 'V')
                sr = item.get('sr', '0000')
                name = item.get('name', 'Feed')

                # تنسيق الشفرة بمسافات (14 1A C8...)
                fmt_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                # التنسيق الإنجليزي اللي إنت عايزه
                msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {fmt_key}"
                
                # إرسال فوري لتلجرام
                t_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                requests.post(t_url, data={"chat_id": CHAT_ID, "text": msg})
                print(f"🚀 Sent to Telegram: {name}")

    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    get_live_data()
