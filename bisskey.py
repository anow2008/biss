import re
import sys
import json
import cloudscraper
from bs4 import BeautifulSoup

URL = "https://live-feed.net/"
OUT_FILE = "bisskeys.json"

FREQ_RE = re.compile(r'(\d{5})\s*([VHLR])\s*(\d{4,5})')
ID_RE = re.compile(r'🆔\s*([^\n\r]+)')
KEY_RE = re.compile(r'(?:🔑|CW:?)[ \t]*((?:[0-9A-Fa-f]{2}[ \t]*){8,16})')
SAT_RE = re.compile(r'📡\s*([^\n\r]+)')


def format_key(raw_key):
    clean = re.sub(r'\s+', '', raw_key).upper()
    return " ".join(clean[i:i + 2] for i in range(0, len(clean), 2))


def parse_text(text):
    """يقسم نص الصفحة لبلوكات (كل بلوك يبدأ بسطر 📡) ويستخرج منها الفيدات اللي فيها KEY."""
    items = []
    blocks = re.split(r'(?=📡)', text)
    for block in blocks:
        if "📡" not in block:
            continue
        sat = SAT_RE.search(block)
        freq = FREQ_RE.search(block)
        key = KEY_RE.search(block)
        if not (sat and freq and key):
            continue  # مفيش شفرة (Clear / مش لاقيها) -> نتجاهله
        ch_id = ID_RE.search(block)
        items.append({
            "satellite": sat.group(1).strip(),
            "frequency": f"{freq.group(1)} {freq.group(2)} {freq.group(3)}",
            "id": ch_id.group(1).strip() if ch_id else "N/A",
            "key": format_key(key.group(1)),
        })
    return items


def add_unique(target, new_items):
    for it in new_items:
        if it not in target:
            target.append(it)


# ---------- الوضع 1: بدون متصفح (سريع) ----------
def scrape_static():
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    r = scraper.get(URL)
    if r.status_code != 200:
        raise RuntimeError(f"فشل الوصول للموقع: {r.status_code}")
    soup = BeautifulSoup(r.text, 'html.parser')
    # get_text بتجيب كمان النص المخفي (التابات 2-3-4 لو موجودة في الـ HTML)
    return parse_text(soup.get_text(separator="\n"))


# ---------- الوضع 2: بمتصفح حقيقي (بيدوس على أزرار 1 2 3 4) ----------
def scrape_browser():
    from playwright.sync_api import sync_playwright
    feeds = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2000)

        # فتح أي قسم قمر مقفول (لو موجود)
        add_unique(feeds, parse_text(page.inner_text("body")))

        # كل الأزرار اللي نصها رقم واحد بس (1 / 2 / 3 ...)
        tabs = page.locator("button, a, span, div, li").filter(
            has_text=re.compile(r'^\s*\d{1,2}\s*$'))
        count = tabs.count()
        for i in range(count):
            try:
                el = tabs.nth(i)
                if not el.is_visible():
                    continue
                el.click(timeout=2000)
                page.wait_for_timeout(300)
                add_unique(feeds, parse_text(page.inner_text("body")))
            except Exception:
                continue
        browser.close()
    return feeds


def main():
    use_browser = "--browser" in sys.argv
    try:
        feeds = scrape_browser() if use_browser else scrape_static()
    except Exception as e:
        print(f"حدث خطأ: {e}")
        return

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeds, f, ensure_ascii=False, indent=4)
    print(f"تم بنجاح! تم العثور على {len(feeds)} تردد.")


if __name__ == "__main__":
    main()
