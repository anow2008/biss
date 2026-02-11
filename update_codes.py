import requests

def get_codes():
    # ده رابط تجريبي لملف نصي فيه شفرات، هنغيره بعدين لموقعك
    url = "https://raw.githubusercontent.com/Moatla/test/main/biss_sample.txt"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return "No codes found"
    except:
        return "Connection Error"

# تحديث ملف biss.txt
new_content = get_codes()
with open("biss.txt", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done!")
