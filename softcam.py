import requests
import re
import base64
import os

GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
FORUM_COOKIES = os.getenv("MY_FORUM_COOKIES")
TARGET_REPO = "anow2008/softcam.key" # تأكد إن ده اسم المستودع بتاعك صح
FILE_PATH = "softcam.key"

def get_keys_from_forum():
    url = "https://www.linuxsat-support.com/thread/152939-only-afn-powervu-keys-no-chat-keys-only/?pageNo=9999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': FORUM_COOKIES 
    }
    
    try:
        print("🔍 جاري فحص الصفحة بحثاً عن شفرات AFN...")
        response = requests.get(url, headers=headers, timeout=20)
        html = response.text

        # نمط بحث مطور يلقط الشفرة حتى لو جنبها مسافات أو رموز مختلفة
        # بيبحث عن P 0009FFFF وبعدها الـ Key 00 أو 01
        pattern = r"0009FFFF\s+(00|01)\s+([0-9A-Fa-f]{16})"
        matches = re.findall(pattern, html)

        if not matches:
            print("⚠️ لم يتم العثور على أي شفرة. جرب تحديث الـ Cookies من المتصفح مرة أخرى.")
            # سطر إضافي للتأكد: اطبع جزء من الصفحة في الـ Logs عشان نشوف البوت شايف إيه
            if "Log in" in html or "Register" in html:
                print("❌ البوت مسجل خروج! الـ Cookies اللي حطيتها انتهت أو غلط.")
            return []

        # ترتيب الشفرات وأخذ آخر اتنين (الأحدث)
        new_lines = []
        # بنستخدم set عشان نمنع التكرار
        unique_keys = []
        for m in reversed(matches):
            key_line = f"P 0009FFFF {m[0]} {m[1].upper()}"
            if key_line not in unique_keys:
                unique_keys.append(key_line)
            if len(unique_keys) >= 2: break
        
        for k in unique_keys:
            new_lines.append(f"{k} ;AFN Latest")
            
        print(f"✅ لقينا الشفرات دي: {new_lines}")
        return new_lines
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return []

def update_github(new_content):
    url = f"https://api.github.com/repos/{TARGET_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    final_text = "\n".join(new_content)
    encoded = base64.b64encode(final_text.encode()).decode()
    
    data = {"message": "Auto Update Keys", "content": encoded, "sha": sha}
    requests.put(url, json=data, headers=headers)
    print("🚀 تم تحديث الملف بنجاح!")

keys = get_keys_from_forum()
if keys:
    update_github(keys)
else:
    print("🛑 مفيش بيانات تترفع.")
