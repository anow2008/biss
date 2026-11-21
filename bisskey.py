import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    if not text:
        return "N/A"
    clean = re.sub(r'[📡📶🎬📊🆔🔑🔓]|BISS\s*•\s*KEY\s*FOUND|KEY\s*FOUND', '', text, flags=re.IGNORECASE)
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
        html = response.text
        print("Status Code:", response.status_code)
        print("HTML Length:", len(html))
        print("Contains KEY FOUND in raw HTML:", "KEY FOUND" in html.upper())

        if response.status_code != 200:
            print(f"فشل الوصول للموقع: {response.status_code}")
            return

        soup = BeautifulSoup(html, 'html.parser')
        active_feeds = []

        # نجمع أصغر عناصر تحتوي على KEY FOUND
        candidates = [
            el for el in soup.find_all(['div', 'article', 'section', 'li', 'p'])
            if "KEY FOUND" in el.get_text().upper()
        ]
        print("Candidate elements count:", len(candidates))

        # نرتب من الأصغر للأكبر
        candidates.sort(key=lambda el: len(el.get_text()))

        seen_items = set()

        for card in candidates:
            block_text = card.get_text(separator="\n")

            # نبحث عن كل الترددات داخل البلوك ونأخذ آخر تطابق (الأقرب لتفاصيل الكارت) أو التردد الصحيح
            freqs = re.findall(r'\b(\d{4,5})\s*([VHLR])\s*(\d{3,5})\b', block_text, re.IGNORECASE)
            keys_found = re.findall(r'(?:🔑|CW:?)\s*([A-F0-9\s]{12,50})', block_text, re.IGNORECASE)
            ids_found = re.findall(r'(?:🆔|ID:?)\s*([^\n\r]+)', block_text)

            if not freqs or not keys_found:
                continue

            # لو البلوك فيه أكثر من تردد، غالباً تردد البلوك نفسه يكون الأخير أو الموجود بجانب بياناته
            f_num, f_pol, f_sr = freqs[-1]
            frequency = f"{f_num} {f_pol.upper()} {f_sr}"

            sat_match = re.search(r'([^\n\r]+?\d+\.?\d?°\s?[EW])', block_text)
            if not sat_match and card.parent:
                sat_match = re.search(r'([^\n\r]+?\d+\.?\d?°\s?[EW])', card.parent.get_text(separator="\n"))

            sat_name = clean_text(sat_match.group(1)) if sat_match else "Unknown"

            count = max(len(keys_found), len(ids_found))
            for idx in range(count):
                raw_cw = keys_found[idx] if idx < len(keys_found) else keys_found[-1]
                formatted_key = format_key(raw_cw)
                if len(formatted_key.replace(" ", "")) < 12:
                    continue

                raw_id = ids_found[idx] if idx < len(ids_found) else (ids_found[-1] if ids_found else "N/A")
                channel_id = clean_text(raw_id)

                unique_key = (sat_name, frequency, channel_id, formatted_key)
                if unique_key in seen_items:
                    continue
                seen_items.add(unique_key)

                active_feeds.append({
                    "satellite": sat_name,
                    "frequency": frequency,
                    "slot": idx + 1,
                    "id": channel_id,
                    "key": formatted_key
                })

        # لو لسه فاضي، نطبع جزء من الـ HTML حول KEY FOUND لمعرفة شكل البلوك الحقيقي
        if not active_feeds:
            pos = html.upper().find("KEY FOUND")
            if pos != -1:
                print("--- Raw HTML snippet around KEY FOUND ---")
                print(html[max(0, pos - 400):pos + 800])

        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)

        print(f"تم بنجاح! تم العثور على {len(active_feeds)} نتيجة.")

    except Exception as e:
        print(f"حدث خطأ: {e}")

if __name__ == "__main__":
    scrape_to_json()
