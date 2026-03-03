import requests
from bs4 import BeautifulSoup
import json
import re

def parse_sat_data(text):
    # بحث شامل عن أي نمط للشفرة (CW) أو (Constant CW)
    # بياخد أي 16 حرف/رقم بينهم مسافات بعد كلمة CW
    cw_pattern = re.compile(r'CW[:\s#]*([A-F0-9\s]{16,32})', re.IGNORECASE)
    cw_match = cw_pattern.search(text)
    
    if not cw_match:
        return None

    data = {"raw_text": text}
    try:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        data['satellite'] = lines[0] if lines else "Unknown"
        
        # استخراج التردد (5 أرقام)
        freq_match = re.search(r'(\d{5})', text)
        data['frequency'] = freq_match.group(1) if freq_match else "N/A"
        
        # تنظيف الشفرة
        data['cw'] = cw_match.group(1).strip().replace('\n', ' ')
    except:
        return None
    return data

def run_scraper():
    # الرابط ده بيجبر تليجرام يعرض النسخة القديمة السهلة في السحب
    url = "https://t.me/s/live_sat_feeds"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    print("جاري سحب البيانات...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"فشل الطلب بكود: {response.status_code}")
            return []
    except Exception as e:
        print(f"حدث خطأ في الاتصال: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # تليجرام ويب بيحط النصوص جوه كلاس اسمه tgme_widget_message_bubble
    posts = soup.find_all('div', class_='tgme_widget_message_bubble')
    
    print(f"عدد الفقاعات المستخرجة: {len(posts)}")
    
    database = []
    for post in posts:
        # بنسحب النص من جوه الفقاعة بالكامل
        content = post.get_text(separator="\n").strip()
        
        structured_data = parse_sat_data(content)
        if structured_data:
            # منع تكرار نفس الشفرة
            if not any(d['cw'] == structured_data['cw'] for d in database):
                database.append(structured_data)
            
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    # لو النتائج لسه صفر، هنحط رسالة تجريبية عشان نتأكد إن الملف بيتحفظ
    if not results:
        print("تحذير: لم يتم العثور على شفرات تطابق الفلتر حالياً.")
    
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"العملية انتهت. تم حفظ {len(results)} شفرة.")
