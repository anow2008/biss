import cloudscraper
import re
import json

def scrape_fury_biss():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    url = "https://t.me/s/furybiss"
    
    try:
        response = scraper.get(url)
        content = response.text
        active_feeds = []

        msg_blocks = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', content, re.DOTALL)

        for block in msg_blocks:
            text = re.sub(r'<br\s*/?>', '\n', block)
            text = re.sub(r'<[^>]+>', '', text)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            found_frequencies = [] # قائمة لتخزين الترددات لو فيه أكتر من واحد
            current_sat = "N/A"
            current_id = "N/A"

            for line in lines:
                # 1. سحب القمر
                sat_match = re.search(r'([0-9.]+\s*(?:E|W|°|East|West))', line, re.IGNORECASE)
                if sat_match: current_sat = sat_match.group(1)

                # 2. سحب الترددات (ممكن نلاقي كذا سطر تردد ورا بعض)
                freq_match = re.search(r'(\d{5})\s+(?:Horizontal|Vertical|H|V)\s+(\d{4,5})', line, re.IGNORECASE)
                if not freq_match: # تجربة النمط التاني لو الأول منفعش
                    freq_match = re.search(r'(\d{5})\s*([VHvh])\s*(\d{4,5})', line)
                
                if freq_match:
                    # لو النمط فيه كلمة Horizontal/Vertical كاملة
                    if len(freq_match.groups()) == 2:
                        h_v = "H" if "hor" in line.lower() else "V"
                        f_data = f"{freq_match.group(1)} {h_v} {freq_match.group(2)}"
                    else:
                        f_data = f"{freq_match.group(1)} {freq_match.group(2).upper()} {freq_match.group(3)}"
                    
                    found_frequencies.append(f_data)

                # 3. سحب الـ ID (بيدعم 🆔 FEED 1)
                id_match = re.search(r'(?:🆔|ID|SID)[:\s-]*([^\n(]+)', line, re.IGNORECASE)
                if id_match: current_id = id_match.group(1).strip()

                # 4. سحب الشفرة (بيدعم #CW:)
                cw_pattern = re.search(r'(?:#?CW[:\s]*|^)([A-F0-9]{2}(?:\s[A-F0-9]{2}){7,})', line.upper())
                
                if cw_pattern and found_frequencies:
                    # لكل تردد لقيناه فوق، هنضيف إدخال جديد بنفس الشفرة
                    for freq in found_frequencies:
                        active_feeds.append({
                            "satellite": current_sat,
                            "frequency": freq,
                            "id": current_id,
                            "key": cw_pattern.group(1).strip()
                        })
                    # بعد ما نربط الشفرة بالترددات، نصفر القائمة عشان البوست الجاي
                    found_frequencies = []
                    current_id = "N/A"

        with open('keys.json', 'w', encoding='utf-8') as f:
            json.dump(active_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Extracted {len(active_feeds)} entries from all patterns.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    scrape_fury_biss()
