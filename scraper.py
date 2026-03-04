import requests
from bs4 import BeautifulSoup
import json
import re

def parse_sat_data(text):
    # التعديل هنا: الـ Regex ده بقى دقيق جداً بيعد 8 مجموعات (كل مجموعة حرفين)
    # عشان يضمن إنه يلقط الـ 16 حرف بتوع الشفرة بس
    cw_pattern = re.compile(r'CW[:\s#]*(([A-F0-9]{2}[\s:-]*){8})', re.IGNORECASE)
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
        
        # تنظيف الشفرة: بنشيل المسافات وبناخد أول 16 حرف فقط
        # كدة لو فيه رقم "7" أو غيره بعد الشفرة هيتم تجاهله تماماً
        clean_cw = re.sub(r'[\s:-]', '', cw_match.group(1)).upper()
        data['cw'] = clean_cw[:16] 
    except:
        return None
    return data

def run_scraper():
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
    posts = soup.find_all('div', class_='tgme_widget_message_bubble')
    
    print(f"عدد الفقاعات المستخرجة: {len(posts)}")
    
    database = []
    for post in posts:
        content = post.get_text(separator="\n").strip()
        structured_data = parse_sat_data(content)
        if structured_data:
            if not any(d['cw'] == structured_data['cw'] for d in database):
                database.append(structured_data)
                
    return database

if __name__ == "__main__":
    results = run_scraper()
    
    if not results:
        print("تحذير: لم يتم العثور على شفرات تطابق الفلتر حالياً.")
    
    # الكتابة بوضع 'w' بتمسح القديم وتكتب الجديد زي ما طلبت
    with open('feeds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"العملية انتهت. تم حفظ {len(results)} شفرة.")
