import cloudscraper
from bs4 import BeautifulSoup
import re
import os
import json
import time

# الإعدادات من Secrets
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SAT_USER = os.getenv("SAT_USER")
SAT_PASS = os.getenv("SAT_PASS")

DB_FILE = "last_keys_list.txt"
JSON_FILE = "for me.json"

# القائمة المحدثة بالرابط الجديد
TARGET_TOPICS = [
    "https://www.sat-universe.com/index.php?threads/wrestling-world-championship-10e-7e.275203/",
    "https://www.sat-universe.com/index.php?threads/african-football-inc-caf-africa-cup-of-nations-other-caf-10%C2%B0e-7%C2%B0e-etc-etc.256328/",
    "https://www.sat-universe.com/index.php?threads/wrestling-wwe-tna-aew-impact-wosw-all-brands-all-events-keys-only-plz-no-chat-use-encryption-chat-for-chat.278606/"
]

def update_json_file(new_data_list):
    current_data = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except:
            current_data = []
    updated_data = new_data_list + current_data
    updated_data = updated_data[:100]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)

def get_feeds():
    """الموقع الأول: live-feed.net"""
    URL = "https://live-feed.net/"
    scraper = cloudscraper.create_scraper()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = scraper.get(URL, headers=headers, timeout=20)
        cards = re.split(r'📡', response.text)
        old_keys = open(DB_FILE, "r").read() if os.path.exists(DB_FILE) else ""
        messages, json_entries, new_keys = [], [], []

        for card in cards[1:]:
            soup = BeautifulSoup(card, 'html.parser')
            text = soup.get_text(separator='|')
            sat_m = re.search(r'([^|]+)@', text)
            sat = sat_m.group(1).strip() if sat_m else "Unknown Sat"
            freq_m = re.search(r'(\d{5}\s[VH]\s\d{4,5})', text)
            freq = freq_m.group(1).strip() if freq_m else "00000 V 0000"
            id_m = re.search(r'🆔\s*\|?([^|]+)', text)
            channel = id_m.group(1).strip() if id_m else "Feed"
            key_m = re.search(r'([A-Fa-f0-9]{2}(?:\s[A-Fa-f0-9]{2}){7})', text)
            if key_m:
                raw_key = key_m.group(1).replace(" ", "").upper()
                if len(raw_key) == 16 and raw_key not in old_keys:
                    fmt_key = ' '.join(raw_key[i:i+2] for i in range(0, 16, 2))
                    new_keys.append(raw_key)
                    messages.append(f"Sat: {sat}\nFreq: {freq}\nId: {channel}\n🔑 CW: {fmt_key}")
                    json_entries.append({"satellite": sat, "frequency": freq, "id": channel, "key": fmt_key})
        return messages, json_entries, new_keys
    except:
        return [], [], []

def get_sat_universe_feeds():
    """الموقع الثاني: Sat-Universe (تحديث مرن جداً)"""
    scraper = cloudscraper.create_scraper()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    messages, json_entries, new_keys = [], [], []
    old_keys = open(DB_FILE, "r").read() if os.path.exists(DB_FILE) else ""
    
    try:
        # تسجيل الدخول
        scraper.post("https://www.sat-universe.com/index.php?login/login", 
                     data={'login': SAT_USER, 'password': SAT_PASS, 'remember': 1}, headers=headers)
        
        for topic_url in TARGET_TOPICS:
            # جلب الصفحة الرئيسية للموضوع لمعرفة آخر صفحة
            main_page = scraper.get(topic_url, headers=headers).text
            main_soup = BeautifulSoup(main_page, 'html.parser')
            nav = main_soup.find('ul', class_='pageNav-main')
            
            # إذا وجد صفحات متعددة يذهب لآخر صفحة، وإلا يبقى في الرئيسية
            target = f"{topic_url}page-{nav.find_all('li')[-1].text}" if nav else topic_url
            
            # جلب محتوى الصفحة المستهدفة
            response = scraper.get(target, headers=headers).text
            posts = BeautifulSoup(response, 'html.parser').find_all('div', class_='bbWrapper')
            
            for post in posts:
                text = post.get_text(separator='|')
                
                # 1. البحث عن الشفرة (بصيغة مرنة جداً)
                key_match = re.search(r'(?:CW:?\s*)([A-F0-9]{2}(?:\s[A-F0-9]{2}){7})', text, re.I)
                if not key_match:
                    # محاولة إيجاد 16 حرف هيكسا متصلين في حال عدم وجود كلمة CW
                    key_match = re.search(r'([A-F0-9]{16})', text.replace(" ", "").upper())
                
                if key_match:
                    raw_key = key_match.group(1).replace(" ", "").upper()
                    if len(raw_key) == 16 and raw_key not in old_keys:
                        
                        # 2. البحث عن القمر
                        sat_m = re.search(r'(Eutelsat\s?[^|@\n]*\d+\.?\d*°?\s?[EW])', text, re.I)
                        sat = sat_m.group(1).strip() if sat_m else "Sat-Universe Feed"

                        # 3. البحث عن التردد
                        freq_m = re.search(r'(\d{5})[\s:|-]*([VH]|Vertical|Horizontal)[\s:|-]*(\d{4,5})', text, re.I)
                        if freq_m:
                            pol = "V" if freq_m.group(2).lower().startswith('v') else "H"
                            freq = f"{freq_m.group(1)} {pol} {freq_m.group(3)}"
                        else:
                            freq = "00000 V 0000"

                        # 4. البحث عن الـ ID
                        id_m = re.search(r'ID:\s*([A-Z0-9\-_/ ]+)', text, re.I)
                        channel = id_m.group(1).strip() if id_m else "Feed"

                        fmt_key = ' '.join(raw_key[i:i+2] for i in range(0, 16, 2))
                        new_keys.append(raw_key)
                        messages.append(f"Sat: {sat}\nFreq: {freq}\nId: {channel}\n🔑 CW: {fmt_key}")
                        json_entries.append({"satellite": sat, "frequency": freq, "id": channel, "key": fmt_key})
                        
        return messages, json_entries, new_keys
    except Exception as e:
        print(f"Error in Sat-Universe: {e}")
        return [], [], []

if __name__ == "__main__":
    m1, j1, k1 = get_feeds()
    m2, j2, k2 = get_sat_universe_feeds()
    
    all_msgs = m1 + m2
    all_json = j1 + j2
    all_keys = k1 + k2
    
    if all_keys:
        # حفظ المفاتيح الجديدة في القاعدة لمنع التكرار
        with open(DB_FILE, "a") as f:
            for k in all_keys: f.write(k + "\n")
        
        # تحديث ملف JSON
        update_json_file(all_json)
        
        # إرسال التنبيهات للتلجرام
        if TOKEN and CHAT_ID:
            s = cloudscraper.create_scraper()
            for m in all_msgs:
                s.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})
                time.sleep(1) # تأخير بسيط لتجنب سبام التلجرام
