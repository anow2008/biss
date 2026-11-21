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


# ---------- الوضع 2: بمتصفح حقيقي (بيدوس على أزرار 1 2 3 4 جوه كل كارت) ----------
MARK_TABROWS_JS = r"""
() => {
  let n = 0;
  const seen = new Set();
  document.querySelectorAll('*').forEach(e => {
    if (e.children.length === 0 && /^\s*\d{1,2}\s*$/.test(e.textContent)) {
      const p = e.parentElement;
      if (!p || seen.has(p)) return;
      const nums = [...p.children].filter(c => /^\s*\d{1,2}\s*$/.test(c.textContent));
      if (nums.length >= 2 && nums.length === p.children.length) {
        seen.add(p);
        p.setAttribute('data-tabrow', n++);
      }
    }
  });
  return n;
}
"""

# من صف الأزرار نطلع لفوق لحد أول عنصر فيه Mb/s = الكارت كله
CARD_TEXT_JS = r"""
(row) => {
  let el = row;
  while (el && !/Mb\/s/.test(el.innerText || '')) el = el.parentElement;
  return el ? el.innerText : row.innerText;
}
"""


def scrape_browser():
    from playwright.sync_api import sync_playwright
    feeds = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2500)

        # التاب الظاهر في كل الكروت
        add_unique(feeds, parse_text(page.inner_text("body")))

        rows = page.evaluate(MARK_TABROWS_JS)
        print(f"لقيت {rows} كارت فيه تابات")
        for r in range(rows):
            row = page.locator(f'[data-tabrow="{r}"]')
            try:
                n_tabs = row.locator(":scope > *").count()
                row.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                continue
            for k in range(n_tabs):
                try:
                    row.locator(":scope > *").nth(k).click(timeout=3000)
                    page.wait_for_timeout(400)
                    card_text = row.evaluate(CARD_TEXT_JS)
                    add_unique(feeds, parse_text(card_text))
                except Exception:
                    continue
        browser.close()
    return feeds


def main():
    static_only = "--static" in sys.argv
    try:
        if static_only:
            feeds = scrape_static()
        else:
            try:
                feeds = scrape_browser()
            except ImportError:
                print("Playwright مش متثبت، هشتغل بالوضع العادي (التابات 2-3-4 مش هتتجاب).")
                feeds = scrape_static()
    except Exception as e:
        print(f"حدث خطأ: {e}")
        return

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeds, f, ensure_ascii=False, indent=4)
    print(f"تم بنجاح! تم العثور على {len(feeds)} تردد.")


if __name__ == "__main__":
    main()
