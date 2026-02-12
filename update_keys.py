import requests
import base64
import re
import os

# --- الإعدادات ---
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN") 
TARGET_REPO = "anow2008/softcam.key"
FILE_PATH = "softcam.key"
BRANCH = "main"

def get_new_afn_keys():
    url = "https://satellite-keys.ru/powervu-keys"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        # بنسحب أي سطر يبدأ بـ P 0009FFFF
        lines = response.text.split('\n')
        new_lines = [l.strip() for l in lines if "P 0009FFFF" in l and "ecm key" in l]
        print(f"✅ تم سحب {len(new_lines)} شفرة من الموقع.")
        return sorted(list(set(new_lines)))
    except Exception as e:
        print(f"❌ خطأ في سحب الشفرات: {e}")
        return []

def update_remote_repo():
    new_afn = get_new_afn_keys()
    if not new_afn:
        print("❌ لم يتم العثور على أي شفرات في الموقع الروسي.")
        return

    api_url = f"https://api.github.com/repos/{TARGET_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. جلب الملف الحالي
    r = requests.get(api_url, headers=headers)
    if r.status_code != 200:
        print(f"❌ فشل الوصول للمستودع الثاني. كود الخطأ: {r.status_code}")
        return
    
    file_data = r.json()
    content = base64.b64decode(file_data['content']).decode('utf-8')
    sha = file_data['sha']

    # 2. منطق الاستبدال المضمون
    lines = content.split('\n')
    # إزالة أي أسطر قديمة لـ AFN (حتى لو فيها مسافات مختلفة)
    clean_lines = [l for l in lines if "0009FFFF" not in l and l.strip() != ""]
    
    # إضافة الشفرات الجديدة في بداية الملف عشان تظهر بوضوح
    final_content = "\n".join(new_afn) + "\n" + "\n".join(clean_lines)

    # 3. مقارنة: لو مفيش تغيير ميرفعش حاجة
    if content.strip() == final_content.strip():
        print("ℹ️ الشفرات الموجودة في المستودع هي بالفعل أحدث شفرات. لا حاجة للتحديث.")
        return

    # 4. رفع التحديث
    payload = {
        "message": "Update AFN Keys 🚀",
        "content": base64.b64encode(final_content.encode('utf-8')).decode('utf-8'),
        "sha": sha,
        "branch": BRANCH
    }
    
    res = requests.put(api_url, headers=headers, json=payload)
    if res.status_code == 200:
        print("✅ مبروك! تم تحديث ملف softcam.key بنجاح.")
    else:
        print(f"❌ فشل الرفع. رد السيرفر: {res.text}")

if __name__ == "__main__":
    update_remote_repo()
