import re
import sys
import json
import cloudscraper
from bs4 import BeautifulSoup

URL = "https://live-feed.net/"
OUT_FILE = "bisskeys.json"

EMOJI_RE = re.compile(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]')
FREQ_LINE = re.compile(r'^(\d{5})\s*([VHLR])\s*(\d{4,5})$')
KEY_LINE = re.compile(r'^(?:CW:?\s*)?((?:[0-9A-Fa-f]{2}\s+){7,15}[0-9A-Fa-f]{2})$')
SAT_LINE = re.compile(r'@\s*[\d.]+\s*°?\s*[EW]', re.IGNORECASE)


def format_key(raw_key):
    clean = re.sub(r'\s+', '', raw_key).upper()
    return " ".join(clean[i:i + 2] for i in range(0, len(clean), 2))


def parse_text(text):
    """
    يشتغل على ترتيب الأسطر (من غير الاعتماد على الإيموجي):
    كل سطر شفرة (8 بايت hex) -> نرجع لورا نلاقي: ID (السطر اللي قبله)، التردد، القمر.
    """
    lines = [EMOJI_RE.sub('', l).strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    items = []
    for i, line in enumerate(lines):
        m = KEY_LINE.match(line)
        if not m:
            continue
        ch_id = lines[i - 1] if i > 0 else "N/A"
        freq = sat = None
        for j in range(i - 1, max(i - 15, -1), -1):
            if freq is None and FREQ_LINE.match(lines[j]):
                f = FREQ_LINE.match(lines[j])
                freq = f"{f.group(1)} {f.group(2)} {f.group(3)}"
            elif freq is not None and SAT_LINE.search(lines[j]):
                sat = lines[j]
                break
        if not freq:
            continue
        items.append({
            "satellite": sat or "Unknown",
            "frequency": freq,
            "id": ch_id,
            "key": format_key(m.group(1)),
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
    text = soup.get_text(separator="\n")
    with open("debug_page.txt", "w", encoding="utf-8") as f:
        f.write(text)
    return parse_text(text)


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
        if not feeds and not use_browser:
            print("الوضع العادي رجّع 0 نتيجة، بجرب وضع المتصفح...")
            feeds = scrape_browser()
    except Exception as e:
        print(f"حدث خطأ: {e}")
        return

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeds, f, ensure_ascii=False, indent=4)
    print(f"تم بنجاح! تم العثور على {len(feeds)} تردد.")


if __name__ == "__main__":
    main()
