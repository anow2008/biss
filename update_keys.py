import requests
import base64
import re
import os

# --- الإعدادات ---
# التوكن بيقرأه من الـ Secrets بتاعة مستودع biss
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN") 

# المستودع الهدف (اللي فيه ملف الشفرات)
TARGET_REPO = "anow2008/softcam.key"
FILE_PATH = "softcam.key"
BRANCH = "main"

def get_new_afn_keys():
    # الرابط اللي بنسحب منه الشفرات
    url = "https://satellite-keys.ru/powervu-keys"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        lines = response.text.split('\n')
        # فلترة الأسطر المطلوبة لـ AFN
        new_lines = [l.strip() for l in lines if "P 0009FFFF" in l and "ecm key" in l]
        return sorted(list(set(new_lines)))
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

def update_remote_repo():
    new_afn = get_new_afn_keys()
    if len(new_afn) < 2:
        print("❌ لم يتم العثور على شفرات جديدة في الموقع.")
        return

    # رابط API للمستودع التاني
    api_url = f"https://api.github.com/repos/{TARGET_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. جلب الملف الحالي من مستودع softcam.key
    r = requests.get(api_url, headers=headers)
    if r.status_code != 200:
        print(f"❌ فشل الوصول للملف البعيد: {r.status_code}")
        return
    
    file_data = r.json()
    content = base64.b64decode(file_data['content']).decode('utf-8')
    sha = file_data['sha']

    # 2. منطق الاستبدال
    lines = content.split('\n')
    # إزالة الأسطر القديمة وإضافة الجديدة
    clean_lines = [l for l in lines if "P 0009FFFF" not in l]
    clean_lines.extend(new_afn)
    
    updated_content = "\n".join(clean_lines)

    # 3. إرسال التحديث للمستودع التاني
    payload = {
        "message": "Update AFN PowerVu Keys from biss repo",
        "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
        "sha": sha,
        "branch": BRANCH
    }
    
    res = requests.put(api_url, headers=headers, json=payload)
    if res.status_code == 200:
        print(f"✅ تم تحديث {TARGET_REPO} بنجاح من مستودع biss!")
    else:
        print(f"❌ فشل التحديث: {res.text}")

if __name__ == "__main__":
    update_remote_repo()
