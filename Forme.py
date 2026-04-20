import requests
from bs4 import BeautifulSoup
import re

# --- إعداداتك الخاصة ---
TOKEN = "8597807354:AAFmY6aCvTfm2YRpkv7tlb0X_z6zMh2h_Rw"
CHAT_ID = "@keyforbiss"  # يوزر قناتك العامة
URL = "https://www.sat-universe.com/index.php?threads/wrestling-wwe-tna-aew-impact-wosw-all-brands-all-events-keys-only-plz-no-chat-use-encryption-chat-for-chat.278606/page-103"

def get_keys():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن المشاركات في المنتدى
        posts = soup.find_all('div', class_='bbWrapper')
        if not posts:
            return "⚠️ الموقع غير متاح حالياً أو تم تغيير الهيكل"

        # سحب آخر مشاركة (المشاركة الأحدث)
        last_post = posts[-1].get_text(separator="\n").strip()

        # استخراج شفرة BISS (البحث عن نمط 16 حرف ورقم)
        key_pattern = r'[A-Fa-f0-9]{2}(?:\s?[A-Fa-f0-9]{2}){7}'
        keys = re.findall(key_pattern, last_post)

        if keys:
            # تنظيف الشفرة (حروف كبيرة وبدون مسافات لسهولة النسخ بلمسة واحدة)
            clean_key = keys[0].replace(" ", "").upper()
            
            # --- تنسيق الرسالة باسم القناة الجديد ---
            message = f"""
🌟 **For me | Satellite Updates** 🌟
━━━━━━━━━━━━━━
📡 **تحديث شفرات المصارعة الجديد**

🔑 **BISS KEY:** `{clean_key}`

📝 **تفاصيل المشاركة:**
`{last_post[:130]}...`
━━━━━━━━━━━━━━
👤 **بواسطة:** Anow2007
🤖 **بوت:** @KeyForMe_Updates_bot
✅ **اضغط على الشفرة لنسخها فوراً**
"""
            return message
        else:
            return "ℹ️ تم فحص آخر مشاركة ولم يتم العثور على شفرة BISS جديدة."

    except Exception as e:
        return f"❌ حدث خطأ أثناء السحب: {e}"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, data=payload)
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

# --- تشغيل السكربت ---
if __name__ == "__main__":
    print(f"🔄 جاري فحص صفحة Sat-Universe...")
    final_message = get_keys()
    
    # إرسال الرسالة لتلجرام
    response = send_to_telegram(final_message)

    if response.get("ok"):
        print("✅ تم الإرسال بنجاح إلى قناة [For me]!")
    else:
        print(f"❌ فشل الإرسال: {response.get('description')}")
