import requests
from bs4 import BeautifulSoup
import json
import re

def clean_for_json(text):
    """Remove emojis and keep clean text for satellite names and frequencies."""
    if not text: return ""
    # Supports satellite degree symbols like 7.0°E
    clean = re.sub(r'[^\w\s\d\.\-\/°@]+', '', text)
    return clean.strip()

def parse_sat_data(text):
    """Extract data only if a valid 16-character hex key exists."""
    # 1. Search for the key first (The most important check)
    key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
    key_match = key_pattern.search(text)
    
    # If no 16-character hex key is found, ignore the entire block
    if not key_match:
        return None

    data = {}
    try:
        # Format the key (e.g., 46 EC BD EF 61 25 4E D4)
        raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
        if len(raw_key) != 16: return None
        formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])

        # 2. Extract other fields only if the key was found
        sat_match = re.search(r'📡\s*(.*)', text)
        data['satellite'] = clean_for_json(sat_match.group(1)) if sat_match else "Unknown"

        freq_match = re.search(r'📶\s*([\d\s\w]+)', text)
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
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    
    database = []
    # Process from newest to oldest
    for post in reversed(posts):
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        
        # Only add to database if structured_data is not None (i.e., has a key)
        if structured_data:
            # Check for duplicates within the same session
            if not any(d['key'] == structured_data['key'] for d in database):
                database.append(structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # This will overwrite (wipe) the old feeds.json every time the script runs
    if results:
        with open('feeds.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"✅ Success! {len(results)} active keys saved. Old data was cleared.")
    else:
        # Even if no data found, we could write an empty list or just notify
        print("⚠️ No valid blocks with keys found. Nothing was saved.")
