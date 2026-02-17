import requests
import re
import base64
import os

# جلب البيانات السرية من GitHub Secrets
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
FORUM_COOKIES = os.getenv("MY_FORUM_COOKIES") # السطر ده مهم جداً
TARGET_REPO = "anow2008/softcam.key"
FILE_PATH = "softcam.key"

def get_keys_from_forum():
    url = "https://www.linuxsat-support.com/thread/152939-only-afn-powervu-keys-no-chat-keys-only/?pageNo=9999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': FORUM_COOKIES # إرسال الكوكيز للموقع ليتعرف على حسابك
    }
    
    try:
        print("🔍 جاري محاولة صيد الشفرة باستخدام حسابك...")
        response = requests.get(url, headers=headers, timeout=20)
        html = response.text

        # البحث عن نمط شفرة PowerVu
        pattern = r"0009FFFF\s+(00|01)\s+([0-9A-Fa-f]{16})"
        matches = re.findall(pattern, html)

        if not matches:
            print("❌ للاسف الشفرة مش ظاهرة. تأكد من تحديث الـ Cookies في الـ Secrets.")
            return []

        # أخذ آخر شفرتين
        latest_matches = matches[-2:] 
        new_lines = []
        for m in latest_matches:
            new_lines.append(f"P 0009FFFF {m[0]} {m[1].upper()} ;AFN Latest")
        
        return new_lines
    except Exception as e:
        print(f"❌ خطأ في الاتصال بالمنتدى: {e}")
        return []

def update_github_file(new_content_lines):
    # كود رفع الملف إلى GitHub
    url = f"https://api.github.com/repos/{TARGET_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # الحصول على الـ SHA للملف الحالي (مهم للتحديث)
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    content_str = "\n".join(new_content_lines)
    encoded_content = base64.b64encode(content_str.encode()).decode()
    
    data = {
        "message": "Update AFN Keys from LinuxSat Forum",
        "content": encoded_content,
        "sha": sha
    }
    
    put_res = requests.put(url, json=data, headers=headers)
    if put_res.status_code in [200, 201]:
        print("✅ تم تحديث ملف softcam.key بنجاح!")
    else:
        print(f"❌ فشل التحديث: {put_res.text}")

# تشغيل العملية
if __name__ == "__main__":
    keys = get_keys_from_forum()
    if keys:
        update_github_file(keys)
    else:
        print("⚠️ لم يتم العثور على مفاتيح جديدة لتحديثها.")
