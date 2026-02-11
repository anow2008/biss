import requests
from bs4 import BeautifulSoup
import os

def get_keys():
    # الرابط الذي طلبته
    url = "https://satellite-keys.ru/biss-keys"
    
    # رأس الطلب لإقناع الموقع أننا متصفح عادي
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"Connecting to {url}...")
        response = requests.get(url, headers=headers, timeout=20)
        
        # ضبط الترميز لقرأة اللغة الروسية والعربية بشكل صحيح
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # استهداف المحتوى الرئيسي للموقع
            # الموقع الروسي يضع الشفرات غالباً داخل وسم main أو جداول
            content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if content:
                # تنظيف النص واستخراج النصوص فقط بشكل مرتب
                clean_text = content.get_text(separator='\n', strip=True)
                print("Success: Data extracted.")
                return clean_text
            else:
                return "Error: Could not find the main content on the page."
        else:
            return f"Error: Site returned status code {response.status_code}"
            
    except Exception as e:
        return f"Connection Failed: {str(e)}"

# تشغيل السحب
result_data = get_keys()

# حفظ النتيجة في ملف biss (تأكد أن الاسم مطابق لما في المستودع)
try:
    with open("biss", "w", encoding="utf-8") as f:
        f.write(result_data)
    print("File 'biss' updated successfully!")
except Exception as e:
    print(f"Failed to write file: {e}")
