import cloudscraper
import re
import json
import os

def scrape_fury_biss():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://t.me/s/furybiss"
    
    try:
        response = scraper.get(url)
        content = response.text
        active_feeds = []

        msg_blocks = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', content, re.DOTALL)

        for block in msg_blocks:
            block_clean = re.sub(r'<[^>]+>', '\n', block)
            
            if "CW:" in block_clean.upper():
                # نمط مرن جداً للقمر الصناعي
                sat_match = re.search(r'([^\n]+?(?:@|°)[^\n]+)', block_clean)
                freq_match = re.search(r'(\d{5})\s+([VH])\s+(\d{4,5})', block_clean)
                id_match = re.search(r'ID:\s*([^\n]+)', block_clean, re.IGNORECASE)
                cw_match = re.search(r'(?:#CW|CW):\s*([A-F0-9\s]{16,48})', block_clean, re.IGNORECASE)

                if freq_match and cw_match:
                    active_feeds.append({
                        "satellite": sat_match.group(1).strip() if sat_match else "N/A",
                        "frequency": f"{freq_match.group(1)} {freq_match.group(2)} {freq_match.group(3)}",
                        "id": id_match.group(1).strip() if id_match else "N/A",
                        "key": cw_match.group(1).strip()
                    })

        # التأكد من إنشاء الملف حتى لو القائمة فاضية عشان الـ Action ميقفش
        with open('keys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Total keys found: {len(active_feeds)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_fury_biss()
