import cloudscraper
from bs4 import BeautifulSoup
import re
import json

def scrape_to_json():
    scraper = cloudscraper.create_scraper() 
    url = "https://live-feed.net"
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(separator="\n")
        
        # نمط البحث المرن جداً لسحب كل البيانات المطلوبة
        pattern = re.compile(
            r'(?P<sat>.*?@\s?\d+\.\d°[EW]).*?'        # القمر
            r'(?P<freq>\d{5}\s[VH]\s\d{4,5}).*?'      # التردد
            r'ID:\s*(?P<id>.*?)\n.*?'                 # المعرف
            r'#CW:\s*(?P<cw>[A-F0-9 ]{17,24})',       # الشفرة
            re.DOTALL | re.IGNORECASE
        )
        
        matches = pattern.finditer(content)
        
        active_feeds = []
        for match in matches:
            # التأكد أن الشفرة موجودة (KEY FOUND) في هذا السياق
            start_pos = match.start()
            block_context = content[max(0, start_pos-500):match.end()]
            
            if "KEY FOUND" in block_context.upper():
                # تجميع البيانات في سطر واحد كما طلبت
                formatted_line = (
                    f"{match.group('sat').strip()} / "
                    f"{match.group('freq').strip()} / "
                    f"ID: {match.group('id').strip()} / "
                    f"#CW: {match.group('cw').strip()}"
                )
                active_feeds.append(formatted_line)
        
        # إزالة التكرار
        unique_feeds = list(dict.fromkeys(active_feeds))
        
        # حفظ الملف بصيغة JSON
        with open('bisskeys.json', 'w', encoding='utf-8') as f:
            json.dump(unique_feeds, f, ensure_ascii=False, indent=2)
            
        print(f"Success! {len(unique_feeds)} keys formatted correctly.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_to_json()
