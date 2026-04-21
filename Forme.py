import requests
import re
import json

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"

def get_feeds():
    # هيدرز لمحاكاة متصفح حقيقي 100%
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        session = requests.Session()
        response = session.get(URL, headers=headers, timeout=30)
        content = response.text
        
        # البحث عن مصفوفة البيانات
        json_data_match = re.search(r'data\s+=\s+(\[.*?\]);', content, re.DOTALL)
        if not json_data_match:
            print("⚠️ لم يجد مصفوفة البيانات في كود الصفحة")
            return []

        feeds_list = json.loads(json_data_match.group(1))
        messages = []

        for item in feeds_list:
            key = item.get('cw', '').strip().upper()
            
            if key and len(key) == 16:
                sat = item.get('sat', 'Unknown')
                freq = item.get('freq', '00000')
                pol = item.get('pol', 'V')
                sr = item.get('sr', '0000')
                name = item.get('name', 'Feed')

                formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                # التنسيق الإنجليزي اللي طلبته
                msg = f"Sat: {sat}\n"
                msg += f"Freq: {freq} {pol} {sr}\n"
                msg += f"Id: {name}\n"
                msg += f"🔑 CW: {formatted_key}"
                
                messages.append(msg)
                    
        return messages

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_to_telegram(msgs):
    print(f"🔎 Found {len(msgs)} feeds with keys.")
    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": m})
        if r.status_code == 200:
            print(f"✅ Sent: {m.splitlines()[2]}") # بيطبع اسم القناة في اللوج
        else:
            print(f"❌ Failed to send. Status: {r.status_code}")

if __name__ == "__main__":
    results = get_feeds()
    send_to_telegram(results)
