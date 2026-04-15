import requests
from bs4 import BeautifulSoup
import json
import re

def clean_value(text):
    if not text: return ""
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    clean = re.sub(r'[^\w\s\d\.\-\/°@]', '', text)
    return clean.strip()

def extract_feeds():
    url = "https://t.me/s/live_sat_feeds"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_text')
    final_data = []

    for post in posts:
        content = post.get_text(separator="\n").strip()
        key_pattern = re.compile(r'([A-F0-9]{2}[\s:-]*){8}', re.IGNORECASE)
        key_match = key_pattern.search(content)

        if key_match:
            raw_key = re.sub(r'[\s:-]', '', key_match.group(0)).upper()
            formatted_key = " ".join([raw_key[i:i+2] for i in range(0, 16, 2)])
            sat, freq, cid = "Unknown", "N/A", "N/A"
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            
            key_line_index = -1
            for i, line in enumerate(lines):
                if key_match.group(0) in line:
                    key_line_index = i
                    break

            for i, line in enumerate(lines):
                if '@' in line or any(s in line.lower() for s in ['eutelsat', 'astra', 'intelsat', 'nilesat']):
                    sat = clean_value(line)
                elif re.search(r'\d{5}\s+[HV]\s+\d+', line):
                    freq = clean_value(line)
                if '🆔' in line:
                    cid = clean_value(line.replace('🆔', ''))

            if (cid == "N/A" or cid == "") and key_line_index > 0:
                potential_id = lines[key_line_index - 1]
                if '📶' not in potential_id and '📡' not in potential_id and '@' not in potential_id:
                    cid = clean_value(potential_id)

            entry = {"satellite": sat, "frequency": freq, "id": cid, "key": formatted_key}
            if not any(d['key'] == formatted_key for d in final_data):
                final_data.insert(0, entry)
    return final_data

if __name__ == "__main__":
    results = extract_feeds()
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"Done! Found {len(results)} keys.")
