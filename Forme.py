import requests
import re
import json

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"

def get_all_feeds_now():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        content = response.text
        
        # البحث عن مصفوفة البيانات JSON
        json_data_match = re.search(r'const\s+data\s+=\s+(\[.*?\]);', content, re.DOTALL)
        if not json_data_match:
            json_data_match = re.search(r'let\s+feeds\s+=\s+(\[.*?\]);', content, re.DOTALL)
        
        if not json_data_match:
            print("Could not find JSON data in page")
            return []

        feeds_list = json.loads(json_data_match.group(1))
        messages = []

        for item in feeds_list:
            key = item.get('cw', '').strip().upper()
            
            # سحب أي قناة فيها شفرة 16 رقم
            if key and len(key) == 16:
                sat = item.get('sat', 'Unknown')
                freq = item.get('freq', '00000')
                pol = item.get('pol', 'V')
                sr = item.get('sr', '0000')
                name = item.get('name', 'Feed')

                formatted_key = ' '.join(key[i:i+2] for i in range(0, len(key), 2))

                # التنسيق الإنجليزي المطلوب
                msg = f"Sat: {sat}\n"
                msg += f"Freq: {freq} {pol} {sr}\n"
                msg += f"Id: {name}\n"
                msg += f"🔑 CW: {formatted_key}"
                
                messages.append(msg)
                    
        return messages

    except Exception as e:
        print(f"Error: {e}")
        return []

def send_to_telegram(msgs):
    if not msgs:
        print("No feeds with keys found to send.")
    for m in msgs:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": m})
        print(f"Sending status: {r.status_code}")

if __name__ == "__main__":
    all_msgs = get_all_feeds_now()
    send_to_telegram(all_msgs)
