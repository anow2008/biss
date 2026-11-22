import cloudscraper
from bs4 import BeautifulSoup
import re
import os
import sys
import json
import time

# الإعدادات من Secrets
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SAT_USER = os.getenv("SAT_USER")
SAT_PASS = os.getenv("SAT_PASS")

DB_FILE = "last_keys_list.txt"
JSON_FILE = "for me.json"

SU_BASE = "https://www.sat-universe.com/"
TARGET_TOPICS = [
    "https://www.sat-universe.com/index.php?threads/wrestling-world-championship-10e-7e.275203/",
    "https://www.sat-universe.com/index.php?threads/african-football-inc-caf-africa-cup-of-nations-other-caf-10%C2%B0e-7%C2%B0e-etc-etc.256328/",
    "https://www.sat-universe.com/index.php?threads/wrestling-wwe-tna-aew-impact-wosw-all-brands-all-events-keys-only-plz-no-chat-use-encryption-chat-for-chat.278606/"
]

# ======================================================================
# الجزء المشترك مع bisskey.py: قراءة live-feed.net (متصفح + ضغط التابات)
# ======================================================================
URL = "https://live-feed.net/"

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
  const counts = [];
  groups.forEach((btns, p) => {
    const nums = btns.map(b => parseInt(b.textContent.trim()));
    if (btns.length >= 2 && nums.includes(1) && nums.includes(2)) {
      btns.forEach((b, k) => b.setAttribute('data-tabbtn', r + '-' + k));
      p.setAttribute('data-tabrow', r);
      counts.push(btns.length);
      r++; total += btns.length;
    }
  });
  return counts;
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
        page.on("websocket", lambda ws: requests_log.append(f"websocket {ws.url}"))
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2500)

        if debug:
            raw = page.content()
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(raw)
            hexkeys = set(re.findall(r'\b[0-9A-Fa-f]{16}\b', raw))
            print(f"[debug] HTML الخام فيه {len(hexkeys)} شفرة 16-hex مختلفة")

        # التاب الظاهر في كل الكروت
        add_unique(feeds, parse_text(page.inner_text("body")))
        print(f"من غير ضغط: {len(feeds)} نتيجة")

        counts = page.evaluate(MARK_TABS_JS)
        rows = len(counts)
        print(f"لقيت {rows} صف تابات، أزرار كل صف: {counts}")

        if debug and rows:
            html = page.locator('[data-tabrow="0"]').evaluate(ROW_HTML_JS)
            with open("debug_card.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("اتحفظ debug_card.html")

        for r in range(rows):
            for k in range(counts[r]):
                try:
                    # الموقع بيعمل refresh للـ DOM، فنعيد تعليم الأزرار قبل كل ضغطة
                    new_counts = page.evaluate(MARK_TABS_JS)
                    if r >= len(new_counts) or k >= new_counts[r]:
                        print(f"  كارت {r} تاب {k + 1}: الزر اختفى بعد refresh")
                        continue
                    row = page.locator(f'[data-tabrow="{r}"]')
                    btn = page.locator(f'[data-tabbtn="{r}-{k}"]')
                    btn.scroll_into_view_if_needed(timeout=3000)
                    try:
                        btn.click(timeout=3000)
                    except Exception:
                        btn.click(timeout=3000, force=True)
                    page.wait_for_timeout(500)
                    before = len(feeds)
                    card_text = row.evaluate(CARD_TEXT_JS)
                    add_unique(feeds, parse_text(card_text))
                    add_unique(feeds, parse_text(page.inner_text("body")))
                    print(f"  كارت {r} تاب {k + 1}: +{len(feeds) - before}")
                except Exception as e:
                    print(f"  كارت {r} تاب {k + 1}: فشل ({str(e)[:100]})")

            # --- الطريقة التانية: السهم اليمين (carousel) ---
            try:
                page.evaluate(MARK_TABS_JS)
                row = page.locator(f'[data-tabrow="{r}"]')
                found = row.evaluate(MARK_NEXT_JS)
                nxt = page.locator(f'[data-nextbtn="{r}"]')
                if found and nxt.count():
                    for step in range(counts[r] + 1):
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
                print(f"  كارت {r} سهم: فشل ({str(e)[:100]})")
        browser.close()
        if debug:
            with open("debug_requests.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(requests_log))
            print(f"اتحفظ debug_requests.txt ({len(requests_log)} طلب)")
    return feeds




# ======================================================================
# أدوات عامة
# ======================================================================
def load_old_keys():
    return open(DB_FILE, "r").read() if os.path.exists(DB_FILE) else ""


def update_json_file(new_data_list):
    current_data = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            current_data = []
    updated_data = (new_data_list + current_data)[:100]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)


# ======================================================================
# الموقع الأول: live-feed.net
# ======================================================================
def get_feeds():
    try:
        try:
            feeds = scrape_browser()
        except Exception as e:  # Playwright مش متثبت أو الصفحة ما فتحتش
            print(f"[live-feed] وضع المتصفح فشل ({e}) -> الوضع العادي (تاب 1 بس)")
            feeds = scrape_static()
    except Exception as e:
        print(f"[live-feed] خطأ: {e}")
        return [], [], []

    old_keys = load_old_keys()
    messages, json_entries, new_keys = [], [], []
    for it in feeds:
        raw_key = it["key"].replace(" ", "").upper()
        if len(raw_key) == 16 and raw_key not in old_keys and raw_key not in new_keys:
            new_keys.append(raw_key)
            messages.append(
                f"📡 Sat: {it['satellite']}\n📶 Freq: {it['frequency']}\n"
                f"🆔 Id: {it['id']}\n🔑 CW: {it['key']}")
            json_entries.append(it)
    print(f"[live-feed] {len(feeds)} فيد، الجديد: {len(json_entries)}")
    return messages, json_entries, new_keys


# ======================================================================
# الموقع التاني: Sat-Universe
# ======================================================================
HEX8 = r'(?:[0-9A-Fa-f]{2}[ \t\-:]*){8}'
KEY_PATTERNS = [
    re.compile(r'(?:CW|KEY|BISS)\s*[:=\-]?\s*(' + HEX8 + r')', re.I),            # CW: 11 22 ...
    re.compile(r'\b((?:[0-9A-Fa-f]{2}[ \-:]){7}[0-9A-Fa-f]{2})\b'),               # 11 22 33 ...
    re.compile(r'\b([0-9A-Fa-f]{16})\b'),                                          # 1122334455667788
]
SU_SAT_AT = re.compile(r'([A-Za-z0-9/\- ]{2,40}@\s*[\d.]+\s*°?\s*[EW])', re.I)
SU_SAT_ALT = re.compile(r'(\d{1,3}(?:\.\d)?\s?°\s?[EW]|Eutelsat\s?[^|\n]*)', re.I)
SU_FREQ = re.compile(r'(\d{4,5})[\s:|\-/]*([VHLR])[\s:|\-/]*(\d{4,5})', re.I)
SU_ID = re.compile(r'(?:\bID\b|🆔|\bChannel\b|\bService\b)\s*:?\s*([^\n|]+)', re.I)


def extract_from_post(text):
    """يطلع كل الشفرات في البوست (مش أول واحدة بس)، ومعاها القمر/التردد/ID من السياق اللي قبلها."""
    found = []
    taken = []
    for pat in KEY_PATTERNS:
        for m in pat.finditer(text):
            s, e = m.start(1), m.end(1)
            if any(s < te and e > ts for ts, te in taken):
                continue
            raw = re.sub(r'[^0-9A-Fa-f]', '', m.group(1)).upper()
            if len(raw) != 16:
                continue
            if pat is KEY_PATTERNS[2] and not (re.search(r'[A-F]', raw) and re.search(r'\d', raw)):
                continue  # 16 حرف hex عشوائي من غير بادئة لازم يكون فيه أرقام وحروف
            taken.append((s, e))
            found.append((s, e, raw))
    found.sort()

    entries, prev_end = [], 0
    for s, e, raw in found:
        ctx = text[max(prev_end, s - 600):e]
        prev_end = e

        sat = "Feed"
        sm = SU_SAT_AT.findall(ctx)
        if sm:
            sat = sm[-1].strip()
        else:
            sm = SU_SAT_ALT.findall(ctx)
            if sm:
                sat = sm[-1].strip()

        freq = "Feed Freq"
        fm = list(SU_FREQ.finditer(ctx))
        if fm:
            f = fm[-1]
            freq = f"{f.group(1)} {f.group(2).upper()} {f.group(3)}"

        im = SU_ID.findall(ctx)
        channel = im[-1].strip() if im else "Feed"

        entries.append({
            "satellite": sat,
            "frequency": freq,
            "id": channel,
            "key": " ".join(raw[i:i + 2] for i in range(0, 16, 2)),
        })
    return entries


SU_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')


def parse_cookies(raw):
    """يقبل: "xf_user=...; xf_session=..." أو JSON ({name: value} أو قائمة {name,value})."""
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        if isinstance(data, list):
            return {str(c["name"]): str(c["value"]) for c in data if "name" in c and "value" in c}
    except Exception:
        pass
    out = {}
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


SU_COOKIES = parse_cookies(os.getenv("SU_COOKIES") or "")


def _is_thread_page(html):
    return 'class="bbWrapper"' in html or "bbWrapper" in html


# ---------- الطريقة 1: requests (cloudscraper) ----------
def sat_universe_login(scraper, headers):
    page = scraper.get(SU_BASE + "index.php?login/", headers=headers, timeout=30)
    soup = BeautifulSoup(page.text, 'html.parser')
    tok = soup.find('input', {'name': '_xfToken'})
    token = tok.get('value', '') if tok else ''
    print(f"[sat-universe] صفحة الدخول: status={page.status_code}, token={'موجود' if token else 'مش موجود'}")
    if page.status_code in (403, 503) or "Just a moment" in page.text or "cf-chl" in page.text:
        print("[sat-universe] !! الموقع عارض تحدي Cloudflare لسيرفر GitHub -> استخدم SU_COOKIES أو طريقة المتصفح !!")
    resp = scraper.post(
        SU_BASE + "index.php?login/login",
        data={'login': SAT_USER, 'password': SAT_PASS, 'remember': 1,
              '_xfRedirect': SU_BASE, '_xfToken': token},
        headers=headers, timeout=30)
    ok = 'data-logged-in="true"' in resp.text
    print(f"[sat-universe] الدخول بـ requests: {'نجح' if ok else 'فشل'} (status={resp.status_code})")
    return ok


def last_pages(scraper, headers, topic_url, how_many=2):
    html = scraper.get(topic_url, headers=headers, timeout=30).text
    soup = BeautifulSoup(html, 'html.parser')
    nav = soup.find('ul', class_='pageNav-main')
    nums = []
    if nav:
        nums = [int(a.get_text(strip=True)) for a in nav.find_all('a')
                if a.get_text(strip=True).isdigit()]
    last = max(nums) if nums else 1
    pages = list(range(max(1, last - how_many + 1), last + 1))
    return [topic_url if p == 1 else f"{topic_url}page-{p}" for p in pages]


def collect_posts_requests():
    """يرجّع قائمة نصوص البوستات، أو None لو الدخول فشل."""
    scraper = cloudscraper.create_scraper()
    headers = {'User-Agent': SU_UA}
    logged = False
    if SU_COOKIES:
        for k, v in SU_COOKIES.items():
            scraper.cookies.set(k, v, domain="www.sat-universe.com")
        r = scraper.get(SU_BASE + "index.php", headers=headers, timeout=30)
        logged = 'data-logged-in="true"' in r.text
        print(f"[sat-universe] الدخول بالكوكيز (requests): {'نجح' if logged else 'فشل (الكوكيز منتهية أو غلط)'} (status={r.status_code})")
    if not logged:
        if not (SAT_USER and SAT_PASS):
            return None
        if not sat_universe_login(scraper, headers):
            return None
    texts = []
    for topic_url in TARGET_TOPICS:
        try:
            for target in last_pages(scraper, headers, topic_url):
                resp = scraper.get(target, headers=headers, timeout=30)
                soup = BeautifulSoup(resp.text, 'html.parser')
                posts = soup.find_all('div', class_='bbWrapper')
                print(f"[sat-universe] {target[-45:]} -> {len(posts)} بوست (status={resp.status_code})")
                if not posts:
                    with open("debug_su.html", "w", encoding="utf-8") as f:
                        f.write(resp.text)
                for post in posts:
                    for q in post.find_all('blockquote'):
                        q.decompose()  # نتجاهل الاقتباسات
                    texts.append(post.get_text(separator='\n').strip())
        except Exception as e:
            print(f"[sat-universe] خطأ في {topic_url[-50:]}: {e}")
    return texts


# ---------- الطريقة 2: متصفح حقيقي (Playwright) ----------
EXTRACT_POSTS_JS = """
els => els.map(e => {
  // innerText بيحافظ على الأسطر (br/p) بس لما العنصر يكون جوه الصفحة
  const c = e.cloneNode(true);
  c.style.cssText = 'position:absolute;left:-99999px;top:0;width:800px;';
  document.body.appendChild(c);
  c.querySelectorAll('blockquote').forEach(q => q.remove());
  const t = c.innerText;
  c.remove();
  return t;
})
"""

LAST_PAGE_JS = """
() => {
  const a = [...document.querySelectorAll('.pageNav-main a')]
      .map(x => parseInt(x.textContent.trim())).filter(n => !isNaN(n));
  return a.length ? Math.max(...a) : 1;
}
"""


def _extract_posts(page):
    return page.eval_on_selector_all('.bbWrapper', EXTRACT_POSTS_JS)


def collect_posts_browser():
    from playwright.sync_api import sync_playwright
    texts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=SU_UA, viewport={"width": 1300, "height": 900})
        page = ctx.new_page()
        if SU_COOKIES:
            ctx.add_cookies([{"name": k, "value": v, "domain": "www.sat-universe.com", "path": "/"}
                             for k, v in SU_COOKIES.items()])
        page.goto(SU_BASE + "index.php", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        logged = page.locator('html[data-logged-in="true"]').count() > 0
        if SU_COOKIES:
            print(f"[sat-universe] الدخول بالكوكيز (متصفح): {'نجح' if logged else 'فشل'}")
        if not logged and SAT_USER and SAT_PASS:
            page.goto(SU_BASE + "index.php?login/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            try:
                page.fill('input[name="login"]', SAT_USER)
                page.fill('input[name="password"]', SAT_PASS)
                page.press('input[name="password"]', "Enter")
                page.wait_for_load_state("networkidle", timeout=60000)
            except Exception as e:
                print(f"[sat-universe] فورم الدخول بالمتصفح فشل: {str(e)[:120]}")
            logged = page.locator('html[data-logged-in="true"]').count() > 0
        print(f"[sat-universe] الدخول بالمتصفح: {'نجح' if logged else 'فشل'} (url={page.url[-60:]})")
        if not logged:
            page.screenshot(path="debug_su_login.png")
            with open("debug_su.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            browser.close()
            return texts

        for topic_url in TARGET_TOPICS:
            try:
                page.goto(topic_url, wait_until="domcontentloaded", timeout=60000)
                if "threads/" not in page.url:
                    print(f"[sat-universe] اتحولنا لصفحة تانية: {page.url[-60:]}")
                    continue
                last = page.evaluate(LAST_PAGE_JS)
                for n in range(max(1, last - 1), last + 1):
                    target = topic_url if n == 1 else f"{topic_url}page-{n}"
                    page.goto(target, wait_until="domcontentloaded", timeout=60000)
                    posts = _extract_posts(page)
                    print(f"[sat-universe] (متصفح) {target[-45:]} -> {len(posts)} بوست")
                    texts.extend(t.strip() for t in posts)
            except Exception as e:
                print(f"[sat-universe] خطأ في {topic_url[-50:]}: {str(e)[:120]}")
        browser.close()
    return texts


def get_sat_universe_feeds():
    messages, json_entries, new_keys = [], [], []
    old_keys = load_old_keys()

    if not SU_COOKIES and (not SAT_USER or not SAT_PASS):
        print("[sat-universe] لا SU_COOKIES ولا SAT_USER/SAT_PASS موجودين في الـ Secrets")
        return [], [], []

    texts = None
    try:
        texts = collect_posts_requests()
    except Exception as e:
        print(f"[sat-universe] طريقة requests فشلت: {e}")

    if not texts:  # الدخول فشل أو مفيش بوستات -> جرّب متصفح حقيقي
        print("[sat-universe] بجرب الدخول بالمتصفح...")
        try:
            texts = collect_posts_browser()
        except Exception as e:
            print(f"[sat-universe] طريقة المتصفح فشلت: {e}")
            texts = []

    print(f"[sat-universe] إجمالي البوستات اللي اتقرت: {len(texts or [])}")
    for text in texts or []:
        for it in extract_from_post(text):
            raw = it["key"].replace(" ", "")
            if raw in old_keys or raw in new_keys:
                continue
            new_keys.append(raw)
            json_entries.append(it)
            messages.append(
                f"📡 Sat: {it['satellite']}\n📶 Freq: {it['frequency']}\n"
                f"🆔 Id: {it['id']}\n🔑 CW: {it['key']}")
    print(f"[sat-universe] الجديد: {len(json_entries)}")
    return messages, json_entries, new_keys


if __name__ == "__main__":
    m1, j1, k1 = get_feeds()
    m2, j2, k2 = get_sat_universe_feeds()

    all_msgs = m1 + m2
    all_json = j1 + j2
    all_keys = k1 + k2
    print(f"إجمالي الشفرات الجديدة: {len(all_keys)}")

    if all_keys:
        with open(DB_FILE, "a") as f:
            for k in all_keys:
                f.write(k + "\n")
        update_json_file(all_json)
        if TOKEN and CHAT_ID:
            s = cloudscraper.create_scraper()
            for m in all_msgs:
                r = s.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                           data={"chat_id": CHAT_ID, "text": m})
                if r.status_code != 200:
                    print(f"تلجرام رجّع {r.status_code}: {r.text[:120]}")
                time.sleep(1)  # تأخير لتفادي حظر التلجرام
        else:
            print("BOT_TOKEN/CHAT_ID مش موجودين، مفيش إرسال لتلجرام")
