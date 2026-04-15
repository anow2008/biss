import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def clean_for_json(text):
    """Refined cleaning for Windows 7 and Enigma2 compatibility."""
    if not text: return ""
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # Keep alphanumeric, dots, slashes, and degree symbols
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    """Strictly extracts blocks with 16-character hex keys."""
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    data = {}
    try:
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # Improved Regex for Emojis
        sat_match = re.search(r'📡\s*(.*)', text)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        # Frequency: captures everything until the next line/emoji
        freq_match = re.search(r'📶\s*([^\n🎬📊🆔]+)', text)
        data['frequency'] = clean_for_json(freq_match.group(1)) if freq_match else "N/A"
        
        id_match = re.search(r'🆔\s*([^\n🔑]+)', text)
        data['id'] = clean_for_json(id_match.group(1)) if id_match else "N/A"

        data['key'] = formatted_key
        return data
    except Exception:
        return None

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Today's session marker: "15 April 2026"
    today_marker = datetime.now().strftime("%d %B %Y") 
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # We use a flag to start collecting after seeing today's date marker
    found_today_session = False
    
    # Telegram web view orders posts from oldest to newest in the HTML
    for post in posts:
        content = post.get_text(separator="\n").strip()
        
        # Check if this post is the "Daily Scan Session Started" for today
        if today_marker in content and "Daily Scan Session Started" in content:
            found_today_session = True
            print(f"🎯 Found Today's Session: {today_marker}. Starting extraction...")
            continue
            
        # Only process blocks if we have passed the today's session marker
        if found_today_session:
            structured_data = parse_sat_data(content)
            if structured_data:
                if not any(d['key'] == structured_data['key'] for d in database):
                    database.append(structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # Overwrite the file with fresh daily data
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    if results:
        print(f"✅ Success! {len(results)} items found after today's session start.")
    else:
        print("⚠️ No items found. Make sure the 'Daily Scan Session' post is published today.")
