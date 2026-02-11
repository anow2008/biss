import requests

def get_biss_data():
    # هذا رابط لمصدر شفرات مجاني (كمثال للتجربة)
    # سنقوم لاحقاً بتغييره لروابط المواقع التي تريدها
    url = "https://raw.githubusercontent.com/Moatla/test/main/biss_sample.txt"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print("جاري سحب البيانات من المصدر...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.text
        else:
            return f"خطأ في الوصول للموقع: {response.status_code}"
            
    except Exception as e:
        return f"حدث خطأ أثناء السحب: {str(e)}"

def save_to_file(data):
    # نستخدم اسم الملف 'biss' كما سميته أنت في المستودع
    try:
        with open("biss", "w", encoding="utf-8") as f:
            f.write(data)
        print("تم تحديث الملف بنجاح!")
    except Exception as e:
        print(f"فشل في كتابة الملف: {str(e)}")

if __name__ == "__main__":
    content = get_biss_data()
    save_to_file(content)
