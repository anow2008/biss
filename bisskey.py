import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text:
        return "N/A"
    clean = re.sub(r'[📡📶🎬📊🆔🔑🔓]|BISS • KEY FOUND', '', text)
    return re.sub(r'\s+', ' ', clean).strip()

def format_key(raw_key):
    clean_key = re.sub(r'[^A-Fa-f0-9]', '', raw_key).upper()
    return " ".join(clean_key[i:i+2] for i in range(0, len(clean_key), 2))

def scrape_to_json():
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    url = "https://live-feed.net"

    try:
        response = scraper.get(url, timeout=20)
        print("Status Code:", response.status_code)
        if response.status_code != 200:
            print(f"فشل الوصول للموقع: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        active_feeds = []

        candidate_elements = [
            el for el in soup.find_all(['div', 'article', 'section', 'li', 'p'])
            if "KEY FOUND" in el.get_text()
        ]
        candidate_elements.sort(key=lambda el: len(el.get_text()))

        seen_cards = set()

        for card in candidate_elements:
            block_text = card.get_text(separator="\n")

            freq_match = re.search(r'(\d{4,5})\s*([VHLR])\s*(\d{3,5})', block_text, re.IGNORECASE)
            keys_found = re.findall(r'(?:🔑|CW:?)\s*([A-F0-9\s]{12,50})', block_text, re.IGNORECASE)
            ids_found = re.findall(r'(?:🆔|ID:?)\s*([^\n\r]+)', block_text)

            # لو فيه تردد 10762 أو 11513 نطبع تشخيص سريع ليه اتاخد أو اتساب
            if freq_match and freq_match.group(1) in ("10762", "11513"):
                print(f"--- Debug Freq {freq_match.group(1)} ---")
                print("keys_found:", keys_found)
                print("ids_found:", ids_found)
                print("snippet:", repr(block_text[:300]))

            if not freq_match or not keys_found:
                continue

            frequency = f"{freq_match.group(1)} {freq_match.group(2).upper()} {freq_match.group(3)}"
            first_clean_key = format_key(keys_found[0])
            card_signature = (frequency, first_clean_key)

            if card_signature in seen_cards:
                continue
            seen_cards.add(card_signature)

            sat_match = re.search(r'([^\n\r]+?\d+\.?\d?°\s?[EW])', block_text)
            if not sat_match and card.parent:
                parent_text = card.parent.get_text(separator="\n")
                sat_match = re.search(r'([^\n\r]+?\d+\.?\d?°\s?[EW])', parent_text)

            sat_name = clean_text(sat_match.group(1)) if sat_match else "Unknown"

            count = max(len(keys_found), len(ids_found))
            for idx in range(count):
                raw_cw = keys_found[idx] if idx < len(keys_found) else keys_found[-1]
                formatted_key = format_key(raw_cw)
                if len(formatted_key.replace(" ", "")) < 12:
                    continue

                raw_id = ids_found[idx] if idx < len(ids_found) else (ids_found[-1] if ids_found else "N/A")
                channel_id = clean_text(raw_id)

                feed_item = {
                    "satellite": sat_name,
                    "frequency": frequency,
                    "slot": idx + 1,
                    "id": channel_id,
                    "key": formatted_key
                }

                if feed_item not in active_feeds:
                    active_feeds.append(feed_item)

        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)

        print(f"تم بنجاح! تم العثور على {len(active_feeds)} نتيجة.")

    except Exception as e:
        print(f"حدث خطأ: {e}")

if __name__ == "__main__":
    scrape_to_json()
