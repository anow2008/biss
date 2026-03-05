import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def scrape_to_json():
    scraper = cloudscraper.create_scraper() 
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200: return

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(separator="\n")
        
        # تقسيم الموقع لبلوكات
        raw_blocks = re.split(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', content)
        
        active_feeds = []
        for block in raw_blocks:
            if "KEY FOUND" in block and "#CW:" in block:
                sat = re.search(r'(.*?@\s?\d+\.\d°[EW])', block)
                freq = re.search(r'(\d{5}\s[VH]\s\d{4,5})', block)
                chan_id = re.search(r'ID:\s*(.*)', block)
                cw = re.search(r'#CW:\s*([A-F0-9 ]{17,24})', block)

                if sat and freq and cw:
                    active_feeds.append({
                        "sat": sat.group(1).strip(),
                        "freq": freq.group(1).strip(),
                        "id": chan_id.group(1).strip() if chan_id else "N/A",
                        "key": cw.group(1).strip()
                    })
        
        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print("Success! Created bisskeys.json")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
