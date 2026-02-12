import requests
import re
import base64
import os

GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
TARGET_REPO = "anow2008/softcam.key"
FILE_PATH = "softcam.key"

def get_keys_from_forum():
    # الرابط اللي أنت بعته
    url = "https://www.linuxsat-support.com/thread/152939-only-afn-powervu-keys-no-chat-keys-only/?pageNo=9999" # طلبت صفحة كبيرة عشان يوديني لآخر صفحة تلقائياً
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print("🔍 جاري محاولة صيد الشفرة من المنتدى...")
        response = requests.get(url, headers=headers, timeout=20)
        html = response.text

        # بنبحث عن نمط شفرة PowerVu (P 0009FFFF) جوه نص المشاركات
        # الكود ده بيدور على 16 رقم وحرف بتوع الشفرة
        pattern = r"0009FFFF\s+(00|01)\s+([0-9A-Fa-f]{16})"
        matches = re.findall(pattern, html)

        if not matches:
            print("❌ للاسف المنتدى عامل حماية أو الشفرة مش ظاهرة بدون تسجيل دخول.")
            return []

        # هناخد آخر شفرتين ظهروا في الصفحة (لأنهم الأحدث)
        latest_matches = matches[-2:] 
        new_lines = []
        for m in latest_matches:
            new_lines.append(f"P 0009FFFF {m[0]} {m[1].upper()} ;AFN Latest")
        
        return new_lines
    except Exception as e:
        print(f"❌ خطأ في الاتصال بالمنتدى: {e}")
        return []

# ... (باقي كود التحديث للمستودع التاني زي ما هو)
