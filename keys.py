import cloudscraper
import re
import json

def clean_text(text):
    return text.strip() if text else "N/A"

def scrape_fury_biss():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://t.me/s/furybiss"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"Failed. Status: {response.status_code}")
            return

        content = response.text
        active_feeds = []

        # استخراج كتل الرسائل
        msg_blocks = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', content, re.DOTALL)

        for block in msg_blocks:
            # تحويل الوسوم لسطور وتنظيف النص
            block_clean = re.sub(r'<[^>]+>', '\n', block)
            
            # لو الرسالة فيها شفرة، نبدأ نستخرج التفاصيل
            if "#CW:" in block_clean.upper() or "CW:" in block_clean.upper():
                
                # 1. القمر الصناعي: بنبحث عن أي نص يحتوي على @ وموقع مداري (°E أو °W)
                # النمط ده مرن جداً عشان يلقط الاسم كامل
                sat_match = re.search(r'([^\n]+@\s?\d+\.?\d?°\s?[EW])', block_clean, re.IGNORECASE)
                
                # 2. التردد: 5 أرقام + V/H + الترميز
                freq_match = re.search(r'(\d{5})\s+([VH])\s+(\d{4,5})', block_clean)
                
                # 3. الـ ID
                id_match = re.search(r'ID:\s*([^\n]+)', block_clean, re.IGNORECASE)
                
                # 4. الشفرة (Key)
                cw_match = re.search(r'(?:#CW|CW):\s*([A-F0-9\s]{16,48})', block_clean, re.IGNORECASE)

                if freq_match and cw_match:
                    # لو مالقاش القمر بنمط الـ @، بنجرب نبحث عن أي سطر فيه درجة ° وخلاص
                    sat_name = "N/A"
                    if sat_match:
                        sat_name = clean_text(sat_match.group(1))
                    else:
                        backup_sat = re.search(r'([^\n]+?\d+\.?\d?°\s?[EW])', block_clean)
                        if backup_sat:
                            sat_name = clean_text(backup_sat.group(1))

                    feed_item = {
                        "satellite": sat_name,
                        "frequency": f"{freq_match.group(1)} {freq_match.group(2)} {freq_match.group(3)}",
                        "id": clean_text(id_match.group(1)) if id_match else "N/A",
                        "key": clean_text(cw_match.group(1))
                    }
                    
                    if feed_item not in active_feeds:
                        active_feeds.append(feed_item)

        with open('keys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Done! Found {len(active_feeds)} keys.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_fury_biss()
