import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def clean_for_json(text):
    """
    Cleans text for Enigma2 display, preserving satellite degrees and basic symbols.
    Removes hidden characters and emojis that might cause issues.
    """
    if not text: return ""
    # Handling non-breaking spaces and tabs often found in Telegram posts
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # Keeping alphanumeric, dots, slashes, degree symbols (°), and @
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    """
    Analyzes the message block. 
    Strictly requires a 16-character hex key to proceed.
    """
    # Flexible Regex: catches 16 hex chars regardless of prefix (CW, BISS, 🔑, etc.)
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    data = {}
    try:
        # Extract and format key to: XX XX XX XX XX XX XX XX
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # 1. Satellite: Extract after dish emoji 📡
        sat_match = re.search(r'📡\s*([^\n]+)', text)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        # 2. Frequency: Extract after signal emoji 📶
        # Grabs everything until the next major block icon
        freq_match = re.search(r'📶\s*([^\n🎬📊🆔]+)', text)
        data['frequency'] = clean_for_json(freq_match.group(1)) if freq_match else "N/A"
        
        # 3. ID (Channel Name): Extract after ID emoji 🆔
        id_match = re.search(r'🆔\s*([^\n🔑]+)', text)
        data['id'] = clean_for_json(id_match.group(1)) if id_match else "N/A"

        # 4. Key: The mandatory final field for the plugin
        data['key'] = formatted_key
        
        return data
    except Exception:
        return None

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Generate today's marker (e.g., "15 April 2026")
    today_marker = datetime.now().strftime("%d %B %Y").lstrip('0')
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # Flag to ensure we only capture posts AFTER today's session started
    found_today_session = False
    
    for post in posts:
        content = post.get_text(separator="\n").strip()
        
        # Check for the Daily Session Marker for today
        if today_marker in content and "Daily Scan Session" in content:
            found_today_session = True
            continue
            
        if found_today_session:
            structured_data = parse_sat_data(content)
            if structured_data:
                # Avoid duplicates and keep newest on top
                if not any(d['key'] == structured_data['key'] for d in database):
                    database.insert(0, structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # Overwrites feeds.json every time to ensure only fresh data
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ Success! {len(results)} today's keys saved to feeds.json.")
    else:
        print("⚠️ No valid keys found after today's session marker.")
