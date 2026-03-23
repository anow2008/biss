import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text: return "N/A"
    return text.strip()

def scrape_to_json():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"Failed. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(separator="\n")
        content = re.sub(r'\n\s*\n', '\n', content)

        sat_pattern = re.compile(r'([^\n]*?@\s?\d+\.?\d?°\s?[EW])', re.IGNORECASE)
        sat_matches = list(sat_pattern.finditer(content))
        
        active_feeds = []

        for i in range(len(sat_matches)):
            start = sat_matches[i].start()
            end = sat_matches[i+1].start() if i+1 < len(sat_matches) else len(content)
            block = content[start:end]

            if "#CW:" in block.upper() or "CW:" in block.upper():
                freq_match = re.search(r'(\d{5})\s+([VH])\s+(\d{4,5})', block)
                id_match = re.search(r'ID:\s*([^\n]+)', block, re.IGNORECASE)
                
                # نمط الشفرة بياخد النص زي ما هو
                cw_match = re.search(r'(?:#CW|CW):\s*([A-F0-9\s]{16,40})', block, re.IGNORECASE)

                if freq_match and cw_match:
                    feed_item = {
                        "satellite": clean_text(sat_matches[i].group(1)),
                        "frequency": f"{freq_match.group(1)} {freq_match.group(2)} {freq_match.group(3)}",
                        "id": clean_text(id_match.group(1)) if id_match else "N/A",
                        "key": clean_text(cw_match.group(1)) # هنا التعديل: هيحفظ المسافات زي ما هي
                    }
                    
                    if feed_item not in active_feeds:
                        active_feeds.append(feed_item)

        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Done! Found {len(active_feeds)} feeds.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
