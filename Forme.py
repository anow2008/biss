import cloudscraper
from bs4 import BeautifulSoup
import re
import os
import json
import time

# الإعدادات من Secrets (GitHub Settings -> Secrets and variables -> Actions)
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SAT_USER = os.getenv("SAT_USER")
SAT_PASS = os.getenv("SAT_PASS")

DB_FILE = "last_keys_list.txt"
JSON_FILE = "for me.json"

# روابط مواضيع Sat-Universe (سيتم جلب آخر صفحة تلقائياً)
TARGET_TOPICS = [
    "https://www.sat-universe.com/index.php?threads/wrestling-world-championship-10e-7e.275203/",
    "https://www.sat-universe.com/index.php?threads/african-football-inc-caf-africa-cup-of-nations-other-caf-10%C2%B0e-7%C2%B0e-etc-etc.256328/"
]

def update_json_file(new_data_list):
    current_data = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except:
            current_data = []
    # دمج الجديد مع القديم والحفاظ على أحدث 100 إدخال
    updated_data = new_data_list + current_data
    updated_data = updated_data[:100]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)

def get_feeds():
    """الموقع الأول: live-feed.net (نفس منطق كودك الأصلي)"""
    URL = "https://live-feed.net/"
    scraper = cloudscraper.create_scraper()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = scraper.get(URL, headers=headers, timeout=20)
        cards = re.split(r'📡', response.text)
        
        old_keys = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                old_keys = f.read()

        messages, json_entries, new_keys_list = [], [], []

        for card in cards[1:]:
            soup = BeautifulSoup(card, 'html.parser')
            text = soup.get_text(separator='|')

            sat = "Unknown Sat"
            sat_m = re.search(r'([^|]+)@', text)
            if sat_m: sat = sat_m.group(1).strip()

            freq = "00000 V 0000"
            freq_m = re.search(r'(\d{5}\s[VH]\s\d{4,5})', text)
            if freq_m: freq = freq_m.group(1).strip()

            channel = "Feed"
            id_m = re.search(r'🆔\s*\|?([^|]+)', text)
            if id_m: 
                val = id_m.group(1).strip()
                if "snapshot" not in val.lower(): channel = val

            key_m = re.search(r'([A-Fa-f0-9]{2}(?:\s[A-Fa-f0-9]{2}){7})', text)
            if key_m:
                raw_key = key_m.group(1).replace(" ", "").upper()
                if len(raw_key) == 16 and raw_key not in old_keys:
                    new_keys_list.append(raw_key)
                    fmt_key = ' '.join(raw_key[i:i+2] for i in range(0, 16, 2))
                    messages.append(f"Sat: {sat}\nFreq: {freq}\nId: {channel}\n🔑 CW: {fmt_key}")
                    json_entries.append({"satellite": sat, "frequency": freq, "id": channel, "key": fmt_key})

        return messages, json_entries, new_keys_list
    except:
        return [], [], []

def get_sat_universe_feeds():
    """الموقع الثاني: Sat-Universe (تجاوز الحماية + جلب أحدث صفحة)"""
    login_url = "https://www.sat-universe.com/index.php?login/login"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    scraper = cloudscraper.create_scraper()
    
    messages, json_entries, new_keys_list = [], [], []

    old_keys = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            old_keys = f.read()

    try:
        # 1. تسجيل الدخول
        login_data = {'login': SAT_USER, 'password': SAT_PASS, 'remember': 1}
        scraper.post(login_url, data=login_data, headers=headers)
        time.sleep(2) # انتظار بسيط للتأكد من تفعيل الجلسة
        
        for topic_url in TARGET_TOPICS:
            # 2. تحديد آخر صفحة تلقائياً
            main_resp = scraper.get(topic_url, headers=headers, timeout=20)
            main_soup = BeautifulSoup(main_resp.text, 'html.parser')
            nav = main_soup.find('ul', class_='pageNav-main')
            
            if nav:
                pages = nav.find_all('li')
                last_page_num = pages[-1].text
                current_target = f"{topic_url}page-{last_page_num}"
            else:
                current_target = topic_url

            # 3. سحب المشاركات من الصفحة الأخيرة
            response = scraper.get(current_target, headers=headers, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.find_all('div', class_='bbWrapper')
            
            for post in posts:
                text = post.get_text(separator='|')
                # البحث عن الشفرة بمرونة (CW أو #CW)
                key_m = re.search(r'(?:#?CW:?\s*)([A-Fa-f0-9]{2}(?:\s[A-Fa-f0-9]{2}){7})', text, re.I)
                
                if key_m:
                    raw_key = key_m.group(1).replace(" ", "").upper()
                    if len(raw_key) == 16 and raw_key not in old_keys:
                        # سحب القمر (يدعم الدرجات والأسماء المختلفة)
                        sat = "Unknown Sat"
                        sat_m = re.search(r'(Eutelsat\s?[^|@\n]+(?:\d+\.?\d*°?\s?[EW]))', text, re.I)
                        if sat_m: sat = sat_m.group(1).strip()

                        # سحب التردد وتحويله لـ V/H
                        freq = "00000 V 0000"
                        freq_m = re.search(r'(\d{5})[\s:|-]*(Vertical|Horizontal|V|H)[\s:|-]*(\d{4,5})', text, re.I)
                        if freq_m:
                            pol = "V" if freq_m.group(2).lower().startswith('v') else "H"
                            freq = f"{freq_m.group(1)} {pol} {freq_m.group(3)}"

                        # سحب الـ ID (اسم القناة)
                        channel = "Feed"
                        id_m = re.search(r'ID:\s*([A-Z0-9\-_/ ]+)', text, re.I)
                        if id_m: channel = id_m.group(1).strip()

                        fmt_key = ' '.join(raw_key[i:i+2] for i in range(0, 16, 2))
                        new_keys_list.append(raw_key)
                        messages.append(f"Sat: {sat}\nFreq: {freq}\nId: {channel}\n🔑 CW: {fmt_key}")
                        json_entries.append({"satellite": sat, "frequency": freq, "id": channel, "key": fmt_key})

        return messages, json_entries, new_keys_list
    except Exception as e:
        print(f"Sat-Universe Error: {e}")
        return [], [], []

if __name__ == "__main__":
    # جلب البيانات من المصدرين
    m1, j1, k1 = get_feeds()
    m2, j2, k2 = get_sat_universe_feeds()
    
    all_messages = m1 + m2
    all_json = j1 + j2
    all_keys = k1 + k2
    
    if all_keys:
        # حفظ الشفرات لمنع التكرار مستقبلاً
        with open(DB_FILE, "a") as f:
            for k in all_keys: f.write(k + "\n")
        
        # تحديث ملف JSON للبلجن
        update_json_file(all_json)
        
        # إرسال للتلجرام
        if TOKEN and CHAT_ID:
            # استخدام سكرابر عادي للإرسال
            send_scraper = cloudscraper.create_scraper()
            for m in all_messages:
                send_scraper.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})
