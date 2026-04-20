import requests
from bs4 import BeautifulSoup
import re

# --- الإعدادات ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"
URL = "https://live-feed.net/"

def get_live_feeds():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://live-feed.net/'
    }

    try:
        response = requests.get(URL, headers=headers, timeout=20)
        if response.status_code != 200:
            return f"⚠️ الموقع محمي أو غير متاح حالياً (Status: {response.status_code})"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن الجداول أو العناصر اللي فيها البيانات
        # الموقع ده غالباً بيحط البيانات في صفوف (Rows)
        feeds = soup.find_all('tr') # البحث عن صفوف الجدول
        
        if not feeds:
            return "⚠️ لم أتمكن من قراءة جدول البيانات، قد يكون الموقع غير تصميمه."

        # هناخد أول صف بيانات (لأنه الأحدث)
        # هنحاول نصطاد الشفرة والتردد باستخدام Regex
        page_text = response.text
        
        # نمط البحث عن شفرات البيس (16 حرف ورقم)
        key_pattern = r'[A-Fa-f0-9]{2}(?:\s?[A-Fa-f0-9]{2}){7}'
        keys = re.findall(key_pattern, page_text)

        if keys:
            # تنظيف الشفرة الأخيرة
            latest_key = keys[0].replace(" ", "").upper()
            
            # محاولة استخراج اسم الحدث أو الفيد (بيكون غالباً نص قبل الشفرة)
            message = f"""
🌟 **For me | Live Feed Update** 🌟
━━━━━━━━━━━━━━
⚽ **جديد الفيدات المباشرة**

🔑 **BISS KEY:** `{latest_key}`

🌍 **المصدر:** Live-Feed.net
━━━━━━━━━━━━━━
👤 **بواسطة:** Anow2007
✅ **اضغط على الشفرة لنسخها فوراً**
"""
            return message
        else:
            return "ℹ️ تم الدخول للموقع ولكن لم يتم العثور على شفرات نشطة حالياً."

    except Exception as e:
        return f"❌ خطأ فني أثناء السحب: {str(e)}"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    msg = get_live_feeds()
    send_to_telegram(msg)
