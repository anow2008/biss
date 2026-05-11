import cloudscraper
from bs4 import BeautifulSoup
import re
import os
import json
import time

# ط§ظ„ط¥ط¹ط¯ط§ط¯ط§طھ ظ…ظ† Secrets
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SAT_USER = os.getenv("SAT_USER")
SAT_PASS = os.getenv("SAT_PASS")

DB_FILE = "last_keys_list.txt"
JSON_FILE = "for me.json"

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
    updated_data = new_data_list + current_data
    updated_data = updated_data[:100]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)

def get_feeds():
    """ط§ظ„ظ…ظˆظ‚ط¹ ط§ظ„ط£ظˆظ„: live-feed.net"""
    URL = "https://live-feed.net/"
    scraper = cloudscraper.create_scraper()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = scraper.get(URL, headers=headers, timeout=20)
        cards = re.split(r'ًں“،', response.text)
        old_keys = open(DB_FILE, "r").read() if os.path.exists(DB_FILE) else ""
        messages, json_entries, new_keys = [], [], []

        for card in cards[1:]:
            soup = BeautifulSoup(card, 'html.parser')
            text = soup.get_text(separator='|')
            sat_m = re.search(r'([^|]+)@', text)
            sat = sat_m.group(1).strip() if sat_m else "Unknown Sat"
            freq_m = re.search(r'(\d{5}\s[VH]\s\d{4,5})', text)
            freq = freq_m.group(1).strip() if freq_m else "00000 V 0000"
            id_m = re.search(r'ًں†”\s*\|?([^|]+)', text)
            channel = id_m.group(1).strip() if id_m else "Feed"
            key_m = re.search(r'([A-Fa-f0-9]{2}(?:\s[A-Fa-f0-9]{2}){7})', text)
            if key_m:
                raw_key = key_m.group(1).replace(" ", "").upper()
                if len(raw_key) == 16 and raw_key not in old_keys:
                    fmt_key = ' '.join(raw_key[i:i+2] for i in range(0, 16, 2))
                    new_keys.append(raw_key)
                    messages.append(f"Sat: {sat}\nFreq: {freq}\nId: {channel}\nًں”‘ CW: {fmt_key}")
                    json_entries.append({"satellite": sat, "frequency": freq, "id": channel, "key": fmt_key})
        return messages, json_entries, new_keys
    except:
        return [], [], []

def get_sat_universe_feeds():
    """ط§ظ„ظ…ظˆظ‚ط¹ ط§ظ„ط«ط§ظ†ظٹ: Sat-Universe (طھط­ط¯ظٹط« ظ…ط±ظ† ط¬ط¯ط§ظ‹)"""
    scraper = cloudscraper.create_scraper()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    messages, json_entries, new_keys = [], [], []
    old_keys = open(DB_FILE, "r").read() if os.path.exists(DB_FILE) else ""
    
    try:
        # طھط³ط¬ظٹظ„ ط§ظ„ط¯ط®ظˆظ„
        scraper.post("https://www.sat-universe.com/index.php?login/login", 
                     data={'login': SAT_USER, 'password': SAT_PASS, 'remember': 1}, headers=headers)
        
        for topic_url in TARGET_TOPICS:
            # ط¬ظ„ط¨ ط§ظ„طµظپط­ط© ط§ظ„ط±ط¦ظٹط³ظٹط© ظ„ظ„ظ…ظˆط¶ظˆط¹ ظ„ظ…ط¹ط±ظپط© ط¢ط®ط± طµظپط­ط©
            main_page = scraper.get(topic_url, headers=headers).text
            main_soup = BeautifulSoup(main_page, 'html.parser')
            nav = main_soup.find('ul', class_='pageNav-main')
            target = f"{topic_url}page-{nav.find_all('li')[-1].text}" if nav else topic_url
            
            # ط¬ظ„ط¨ ط¢ط®ط± طµظپط­ط©
            response = scraper.get(target, headers=headers).text
            posts = BeautifulSoup(response, 'html.parser').find_all('div', class_='bbWrapper')
            
            for post in posts:
                text = post.get_text(separator='|')
                
                # 1. ط§ظ„ط¨ط­ط« ط¹ظ† ط§ظ„ط´ظپط±ط© (ط¨طµظٹط؛ط© ظ…ط±ظ†ط© ط¬ط¯ط§ظ‹ ظ„طھط´ظ…ظ„ #CW ط£ظˆ CW ط£ظˆ ط¨ط¯ظˆظ†ظ‡ط§)
                key_match = re.search(r'(?:CW:?\s*)([A-F0-9]{2}(?:\s[A-F0-9]{2}){7})', text, re.I)
                if not key_match:
                    key_match = re.search(r'([A-F0-9]{16})', text.replace(" ", "")) # ط§ظ„ط¨ط­ط« ط¹ظ† 16 ط­ط±ظپ ظ‡ظٹظƒط³ط§ ظ…طھطµظ„ظٹظ†
                
                if key_match:
                    raw_key = key_match.group(1).replace(" ", "").upper()
                    if len(raw_key) == 16 and raw_key not in old_keys:
                        
                        # 2. ط§ظ„ط¨ط­ط« ط¹ظ† ط§ظ„ظ‚ظ…ط± (ظٹط¯ط¹ظ… ظˆط¬ظˆط¯ ط±ظ…ظˆط² ظ…ط«ظ„ آ°)
                        sat_m = re.search(r'(Eutelsat\s?[^|@\n]*\d+\.?\d*آ°?\s?[EW])', text, re.I)
                        sat = sat_m.group(1).strip() if sat_m else "Eutelsat Feed"

                        # 3. ط§ظ„ط¨ط­ط« ط¹ظ† ط§ظ„طھط±ط¯ط¯ (ظٹط¯ط¹ظ… ط§ظ„ظپظˆط§طµظ„ ط§ظ„ط؛ط±ظٹط¨ط© ظ…ط«ظ„ - ط£ظˆ :)
                        freq_m = re.search(r'(\d{5})[\s:|-]*([VH]|Vertical|Horizontal)[\s:|-]*(\d{4,5})', text, re.I)
                        if freq_m:
                            pol = "V" if freq_m.group(2).lower().startswith('v') else "H"
                            freq = f"{freq_m.group(1)} {pol} {freq_m.group(3)}"
                        else:
                            freq = "00000 V 0000"

                        # 4. ط§ظ„ط¨ط­ط« ط¹ظ† ط§ظ„ظ€ ID
                        id_m = re.search(r'ID:\s*([A-Z0-9\-_/ ]+)', text, re.I)
                        channel = id_m.group(1).strip() if id_m else "Feed"

                        fmt_key = ' '.join(raw_key[i:i+2] for i in range(0, 16, 2))
                        new_keys.append(raw_key)
                        messages.append(f"Sat: {sat}\nFreq: {freq}\nId: {channel}\nًں”‘ CW: {fmt_key}")
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
        with open(DB_FILE, "a") as f:
            for k in all_keys: f.write(k + "\n")
        update_json_file(all_json)
        if TOKEN and CHAT_ID:
            s = cloudscraper.create_scraper()
            for m in all_msgs:
                s.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m})
