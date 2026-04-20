import requests
from bs4 import BeautifulSoup
import re

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"

def get_feeds_from_cards():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن الكروت (بناءً على الصورة الموقع بيستخدم نظام الكروت)
        # هنحاول نسحب النص بالكامل ونحلله بـ Regex
        content = response.text
        
        # 1. البحث عن كل الشفرات (16 حرف ورقم)
        key_pattern = r'[A-Fa-f0-9]{2}(?:\s[A-Fa-f0-9]{2}){7}'
        all_keys = re.findall(key_pattern, content)
        
        # 2. البحث عن الترددات (زي اللي في الصورة 12510 V 7500)
        freq_pattern = r'\d{5}\s[VH]\s\d{4,5}'
        all_freqs = re.findall(freq_pattern, content)

        if all_keys:
            # تنظيف أحدث شفرة
            latest_key = all_keys[0].replace(" ", "").upper()
            latest_freq = all_freqs[0] if all_freqs else "Unknown"
            
            # تنسيق الرسالة لـ "For me"
            message = f"""
🌟 **For me | Live Feed Update** 🌟
━━━━━━━━━━━━━━
📡 **بيانات الفيد المباشر الآن**

🔑 **BISS KEY:** `{latest_key}`
📊 **FREQ:** `{latest_freq}`

🌍 **المصدر:** Live-Feed.net
━━━━━━━━━━━━━━
👤 **بواسطة:** Anow2007
✅ **اضغط على الشفرة لنسخها فوراً**
"""
            return message
        else:
            return "ℹ️ الموقع متاح لكن لم يتم العثور على شفرات BISS حالياً."

    except Exception as e:
        return f"❌ خطأ تقني: {str(e)}"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    msg = get_feeds_from_cards()
    send_to_telegram(msg)
