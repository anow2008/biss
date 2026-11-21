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
        header_id = ch_id
        freq = sat = None
        freq_idx = None
        for j in range(i - 1, max(i - 15, -1), -1):
            if freq is None and FREQ_LINE.match(lines[j]):
                f = FREQ_LINE.match(lines[j])
                freq = f"{f.group(1)} {f.group(2)} {f.group(3)}"
                freq_idx = j
            elif freq is not None and SAT_LINE.search(lines[j]):
                sat = lines[j]
                break
        if not freq:
            continue
        # الكارت الحقيقي فيه سطر البت ريت (Mb/s)؛ عنصر "FEED 07" المخفي مفيهوش -> نتجاهله
        if not any("Mb/s" in lines[x] for x in range(freq_idx, i)):
            continue
        if FREQ_LINE.match(header_id):  # بلوك FEED 07 اللي مفيهوش 🆔: ناخد الاسم اللي فوق القمر
            ch_id = "N/A"
            for j in range(i - 1, max(i - 8, 0), -1):
                if lines[j] == sat and j > 0:
                    ch_id = lines[j - 1]
                    break
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
# بيدور على أي عناصر نصها رقم (1..20)، ويطلع لفوق لو الرقم متغلف جوه button/span،
# وبعدين يجمّع الأزرار اللي ليها نفس الأب (= صف التابات) ويحط عليها علامة data-tabbtn
MARK_TABS_JS = r"""
() => {
  const isNum = t => /^\s*\d{1,2}\s*$/.test(t || '');
  const groups = new Map();
  document.querySelectorAll('body *').forEach(e => {
    if (e.children.length === 0 && isNum(e.textContent)) {
      let btn = e;
      while (btn.parentElement && btn.parentElement.children.length === 1 &&
             isNum(btn.parentElement.textContent)) btn = btn.parentElement;
      const p = btn.parentElement;
      if (!p) return;
      if (!groups.has(p)) groups.set(p, []);
      if (!groups.get(p).includes(btn)) groups.get(p).push(btn);
    }
  });
  let r = 0, total = 0;
  groups.forEach((btns, p) => {
    const nums = btns.map(b => parseInt(b.textContent.trim()));
    if (btns.length >= 2 && nums.includes(1) && nums.includes(2)) {
      btns.forEach((b, k) => b.setAttribute('data-tabbtn', r + '-' + k));
      p.setAttribute('data-tabrow', r);
      r++; total += btns.length;
    }
  });
  return [r, total];
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

MARK_NEXT_JS = r"""
(row) => {
  let el = row;
  while (el && !/Mb\/s/.test(el.innerText || '')) el = el.parentElement;
  if (!el) return 0;
  const cls = e => (typeof e.className === 'string' ? e.className : (e.className && e.className.baseVal) || '');
  const arrows = ['›', '>', '❯', '→', '▶', '»', '❭', '⟩'];
  let c = [...el.querySelectorAll('button,a,div,span,i,svg')].filter(e => {
    const attrs = cls(e) + ' ' + (e.getAttribute('aria-label') || '') + ' ' + (e.title || '');
    return /next|right|forward|chevron-r|arrow-r/i.test(attrs) || arrows.includes((e.textContent || '').trim());
  });
  // نفضّل أصغر عنصر (الزر نفسه مش الحاوية)
  c = c.filter(e => !c.some(o => o !== e && e.contains(o)));
  if (!c.length) return 0;
  c[0].setAttribute('data-nextbtn', row.getAttribute('data-tabrow'));
  return c.length;
}
"""

ROW_HTML_JS = r"""
(row) => {
  let el = row;
  for (let i = 0; i < 2 && el.parentElement; i++) el = el.parentElement;
  return el.outerHTML.slice(0, 8000);
}
"""


def scrape_browser(debug=False):
    from playwright.sync_api import sync_playwright
    feeds = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        requests_log = []
        page.on("response", lambda resp: requests_log.append(
            f"{resp.request.resource_type} {resp.status} {resp.url}")
            if resp.request.resource_type in ("xhr", "fetch") else None)
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2500)

        # التاب الظاهر في كل الكروت
        add_unique(feeds, parse_text(page.inner_text("body")))
        print(f"من غير ضغط: {len(feeds)} نتيجة")

        rows, total = page.evaluate(MARK_TABS_JS)
        print(f"لقيت {rows} صف تابات، وإجمالي {total} زر")

        if debug and rows:
            html = page.locator('[data-tabrow="0"]').evaluate(ROW_HTML_JS)
            with open("debug_card.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("اتحفظ debug_card.html")

        for r in range(rows):
            row = page.locator(f'[data-tabrow="{r}"]')
            k = 0
            while True:
                btn = page.locator(f'[data-tabbtn="{r}-{k}"]')
                if btn.count() == 0:
                    break
                try:
                    btn.scroll_into_view_if_needed(timeout=3000)
                    try:
                        btn.click(timeout=3000)
                    except Exception:
                        btn.click(timeout=3000, force=True)
                    page.wait_for_timeout(500)
                    before = len(feeds)
                    # نقرا الكارت + الصفحة كلها (احتياطي لو الكارت اتحدد غلط)
                    add_unique(feeds, parse_text(row.evaluate(CARD_TEXT_JS)))
                    add_unique(feeds, parse_text(page.inner_text("body")))
                    print(f"  كارت {r} تاب {k + 1}: +{len(feeds) - before}")
                except Exception as e:
                    print(f"  كارت {r} تاب {k + 1}: فشل ({str(e)[:80]})")
                k += 1

            # --- الطريقة التانية: السهم اليمين (carousel) ---
            try:
                found = row.evaluate(MARK_NEXT_JS)
                nxt = page.locator(f'[data-nextbtn="{r}"]')
                if found and nxt.count():
                    for step in range(max(k, 4) + 1):
                        before = len(feeds)
                        try:
                            nxt.first.click(timeout=2000, force=True)
                        except Exception:
                            break
                        page.wait_for_timeout(500)
                        add_unique(feeds, parse_text(row.evaluate(CARD_TEXT_JS)))
                        print(f"  كارت {r} سهم {step + 1}: +{len(feeds) - before}")
                else:
                    print(f"  كارت {r}: مالقيتش سهم")
            except Exception as e:
                print(f"  كارت {r} سهم: فشل ({str(e)[:80]})")
        browser.close()
        if debug:
            with open("debug_requests.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(requests_log))
            print(f"اتحفظ debug_requests.txt ({len(requests_log)} طلب)")
    return feeds


def main():
    static_only = "--static" in sys.argv
    debug = "--debug" in sys.argv
    try:
        if static_only:
            print("[الوضع العادي] التابات 2-3-4 مش هتتجاب في الوضع ده")
            feeds = scrape_static()
        else:
            try:
                feeds = scrape_browser(debug)
            except ImportError:
                print("خطأ: Playwright مش متثبت. ثبّته:")
                print("  pip install playwright")
                print("  playwright install --with-deps chromium")
                print("(أو شغّل بـ --static لو عايز الوضع العادي من غير التابات)")
                sys.exit(1)
    except Exception as e:
        print(f"حدث خطأ: {e}")
        return

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeds, f, ensure_ascii=False, indent=4)
    print(f"تم بنجاح! تم العثور على {len(feeds)} تردد.")


if __name__ == "__main__":
    main()
