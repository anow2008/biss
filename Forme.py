import requests
import re
import json
import time

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"

def get_feeds():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache'
    }
    
    for attempt in range(3): # هيحاول 3 مرات
        try:
            print(f"🔄 Attempt {attempt+1}...")
            response = requests.get(URL, headers=headers, timeout=30)
            content = response.text
            
            # لو لقينا كلمة data = [ يبقى السحب نجح
            json_data_match = re.search(r'data\s+=\s+(\[.*?\]);', content, re.DOTALL)
            
            if json_data_match:
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

                        msg = f"Sat: {sat}\nFreq: {freq} {pol} {sr}\nId: {name}\n🔑 CW: {formatted_key}"
                        messages.append(msg)
                
                return messages
            
            print("⚠️ Data not found in this attempt, retrying...")
            time.sleep(5) # يستنى 5 ثواني قبل المحاولة الجاية
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return []

def send_to_telegram(msgs):
    # رسالة تأكيد إن السكربت شغال
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": "🤖 Script Started Checking..."})
    
    if not msgs:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": "ℹ️ No new keys found on site right now."})
        return

    for m in msgs:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})

if __name__ == "__main__":
    results = get_feeds()
    send_to_telegram(results)
