import requests
from bs4 import BeautifulSoup

def get_keys():
    url = "https://satellite-keys.ru/biss-keys"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"Connecting to {url}...")
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # للتأكد من قراءة اللغة الروسية أو العربية صح
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # سحب محتوى الصفحة الأساسي (الجداول أو النصوص)
            content = soup.find('main') or soup.find('body')
            
            # تنظيف النص ليظهر بشكل مرتب
            clean_text = content.get_text(separator='\n', strip=True)
            return clean_text
        else:
            return f"Error: Site returned status {response.status_code}"
    except Exception as e:
        return f"Connection Failed: {str(e)}"

# تنفيذ وحفظ في ملف biss
result = get_keys()
with open("biss", "w", encoding="utf-8") as f:
    f.write(result)

print("Done! Check your biss file.")
