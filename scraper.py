import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def clean_for_json(text):
    if not text: return ""
    text = text.replace('\xa0', ' ') 
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    # Search for the 16-character hex key first
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    if not key_match:
        return None

    data = {}
    try:
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        sat_match = re.search(r'📡\s*(.*)', text)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        freq_match = re.search(r'📶\s*([\d\s\w\.\/]+)', text)
        data['frequency'] = clean_for_json(freq_match.group(1)) if freq_match else "N/A"
        
        id_match = re.search(r'🆔\s*(.*)', text)
        data['id'] = clean_for_json(id_match.group(1)) if id_match else "N/A"

        data['key'] = formatted_key
        return data
    except Exception:
        return None

def run_scraper():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Get current date in Telegram format (e.g., "April 15")
    current_date_str = datetime.now().strftime("%B %d").replace(" 0", " ")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    # Finding both text posts and date headers
    elements = soup.find_all(['div', 'span'], class_=['tgme_widget_message_text', 'tgme_widget_message_date'])
    
    database = []
    
    # Process from newest to oldest
    for element in reversed(elements):
        text_content = element.get_text().strip()
        
        # Check if the element is a date header (e.g., "April 14")
        # If it's a date and NOT today's date, stop the loop
        if re.match(r'^[A-Z][a-z]+\s\d{1,2}$', text_content):
            if text_content != current_date_str:
                print(f"🛑 Reached previous date: {text_content}. Stopping.")
                break
            continue # If it's today's date, just continue to next element

        # If it's a message block, parse it
        if 'tgme_widget_message_text' in element.get('class', []):
            structured_data = parse_sat_data(element.get_text(separator="\n"))
            if structured_data:
                if not any(d['key'] == structured_data['key'] for d in database):
                    database.append(structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # Overwrite feeds.json with only today's data
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Done! Saved {len(results)} keys from today's feeds.")
