import cloudscraper
import re
import json

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"

def get_all_feeds():
    # بنعمل سكريبر ببيانات متصفح حقيقي (Chrome على Windows)
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    ) 
    try:
        response = scraper.get(URL, timeout=30)
        content = response.text
        
        # بنبحث عن المصفوفة اللي بتبدأ بـ [ وتنتهي بـ ]
        # دي الطريقة الأضمن لسحب كل الشفرات مرة واحدة
        json_match = re.search(r'=\s*(\[.*\]);', content)
        
        if not json_match:
            print("⚠️ لم يتم العثور على مصفوفة البيانات، قد تكون الحماية قوية جداً حالياً.")
            return []

        feeds_list = json.loads(json_match.group(1))
        messages = []

        for item in feeds_list:
            key = item.get('cw', '').strip().upper()
            
            # سحب أي قناة فيها شفرة بيس (16 رقم)
            if key and len(key) == 16:
                sat = item.get('sat', 'Unknown')
                freq = item.get('freq', '00000')
                pol = item.get('pol', 'V')
                sr = item.get('sr', '0000')
                name = item.get('name', 'Feed')

                # تنسيق الشفرة بمسافات (14 1A C8...)
                formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                # التنسيق الإنجليزي اللي طلبته بالمللي
                msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {formatted_key}"
                messages.append(msg)
                    
        return messages

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_to_telegram(msgs):
    import requests
    if not msgs:
        print("No keys found.")
        return

    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": m})

if __name__ == "__main__":
    all_msgs = get_all_feeds()
    send_to_telegram(all_msgs)
