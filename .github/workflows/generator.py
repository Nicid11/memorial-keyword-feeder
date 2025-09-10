

   

    
   import os, sys, re, random, json, smtplib, ssl, pathlib, html
from email.mime.text import MIMEText
from datetime import datetime

ROOT = pathlib.Path(__file__).parent
SITE = ROOT
POSTS = SITE / "posts"; POSTS.mkdir(parents=True, exist_ok=True)
DATA  = SITE / "data";  DATA.mkdir(parents=True, exist_ok=True)
SITEMAP = SITE / "sitemap.xml"
FEED    = SITE / "feed.xml"
INDEX   = SITE / "index.html"
LOG     = DATA / "outbox.jsonl"
KFILE   = SITE / "keywords.txt"

# ----- config from env -----
TARGET_URL   = os.getenv("TARGET_URL","").strip()
BRAND_NAME   = os.getenv("BRAND_NAME","Simply Averie").strip()
CONTACT_EMAIL= os.getenv("CONTACT_EMAIL","").strip()
REPO         = os.getenv("GITHUB_REPOSITORY","owner/repo")
owner, repo  = (REPO.split("/",1)+[""])[:2]
BASE_URL     = f"https://{owner}.github.io/{repo}"

SMTP_HOST = os.getenv("SMTP_HOST","").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT","465") or 465)
SMTP_USER = os.getenv("SMTP_USER","").strip()
SMTP_PASS = os.getenv("SMTP_PASS","").strip()
DESTS = [x for x in [os.getenv("POST_TO_1"), os.getenv("POST_TO_2"), os.getenv("POST_TO_3")] if x]

assert TARGET_URL, "Missing TARGET_URL"

# ----- keyword source -----
DEFAULT_KW = [
  "online obituary", "memorial page online", "tribute page",
  "Philadelphia obituary", "memorial website", "QR code funeral program",
  "write an obituary", "obituary examples", "how to share obituary",
  "grief support resources Philadelphia", "funeral homes Philadelphia"
]
if not KFILE.exists():
    KFILE.write_text("\n".join(DEFAULT_KW), encoding="utf-8")

KEYWORDS = [k.strip() for k in KFILE.read_text(encoding="utf-8").splitlines() if k.strip()]

# ----- copy blocks -----
CITIES = ["Philadelphia","West Philly","North Philly","South Philly","Kensington","Upper Darby","Camden","Cherry Hill","Germantown","Manayunk","Roxborough"]
OPENERS = [
  "Create an online obituary today", "Dignified memorial page online",
  "Shareable tribute page for family", "Modern alternative to print obituaries",
  "Memorial website your family can keep", "Set up a tribute page in minutes"
]
BENEFITS = [
  "Elegant design, permanent link", "Built for phones and sharing",
  "Clear pricing, fast turnaround", "Keep memories visible, not buried",
  "One page they can visit forever", "Same-day setup available"
]
GUIDE_SECTIONS = [
  ("What to include", [
    "Full name, dates, city, key relationships",
    "Two or three defining stories",
    "Service details and preferred charities"]),
  ("How to write it", [
    "Start with a simple, specific headline",
    "Use one short paragraph for life highlights",
    "Close with service info and thanks"]),
  ("Sharing it right", [
    "Use one link the whole family shares",
    "Add a small QR code to programs",
    "Post to church and community pages"])
]

def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+","-",s).strip("-")
    return s[:80] or "post"

def pick_variant(keyword: str):
    city = random.choice(CITIES)
    opener = random.choice(OPENERS)
    benefit = random.choice(BENEFITS)
    title = f"{opener} — {keyword.title()} in {city}"
    h1 = f"{opener} in {city}"
    desc = f"{benefit}. Help for families searching '{keyword}'."
    return city, title, h1, benefit, desc

def article_html(url, title, h1, city, benefit, desc, keyword):
    ts = datetime.utcnow().strftime("%Y-%m-%d")
    utm = f"?utm_source=feeder&utm_medium=seo&utm_campaign=guides&utm_kw={slugify(keyword)}"
    cta = TARGET_URL + utm
    # body
    parts = [f"""<!doctype html><meta charset="utf-8">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{url}">
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:760px;margin:32px auto;padding:0 16px;line-height:1.55}}
a.button{{display:inline-block;padding:10px 16px;background:#111;color:#fff;text-decoration:none}}
.card{{border:1px solid #e5e5e5;padding:16px;margin:16px 0}}
small{{color:#666}}
</style>
<h1>{html.escape(h1)}</h1>
<p><small>Guide for families in {html.escape(city)} • Published {ts}</small></p>
<div class="card"><p><strong>{benefit}.</strong> Learn more: <a class="button" href="{cta}">Start a memorial</a></p></div>
<h2>What this covers</h2>
<ul>"""]
    for h, items in GUIDE_SECTIONS:
        parts.append(f"<li>{html.escape(h)}</li>")
    parts.append("</ul>")
    for h, items in GUIDE_SECTIONS:
        parts.append(f"<h2>{html.escape(h)}</h2><ul>")
        for it in items:
            parts.append(f"<li>{html.escape(it)}</li>")
        parts.append("</ul>")
    parts.append(f'<p><a class="button" href="{cta}">Create an online obituary</a></p>')
    return "\n".join(parts)

def write_html(path: pathlib.Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def send_email_html(subject: str, html_body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and DESTS):
        return {"sent": 0, "skipped": "no-smtp"}
    ctx = ssl.create_default_context()
    sent = 0
    for dest in DESTS:
        msg = MIMEText(html_body, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = dest
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [dest], msg.as_string())
        sent += 1
    return {"sent": sent}

def build_home_and_feeds(published):
    # index
    items = []
    for p in published[-60:][::-1]:
        items.append(f'<li><a href="{html.escape(p["url"])}">{html.escape(p["title"])}</a> — <small>{p["date"]}</small></li>')
    INDEX.write_text(f"""<!doctype html><meta charset="utf-8">
<title>Memorial Guides | {html.escape(BRAND_NAME)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<h1>Memorial Guides</h1>
<p>Helpful articles generated automatically.</p>
<ul>{''.join(items)}</ul>
<p><small>Destination: {html.escape(TARGET_URL)}</small></p>
""", encoding="utf-8")
    # sitemap
    urls = [f"{BASE_URL}/"] + [p["url"] for p in published]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"<url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>")
    sm.append("</urlset>")
    SITEMAP.write_text("\n".join(sm), encoding="utf-8")
    # feed
    rss = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<rss version="2.0"><channel><title>Memorial Guides</title><link>{BASE_URL}</link><description>Auto guides</description>']
    for p in published[-20:][::-1]:
        rss.append(f"<item><title>{html.escape(p['title'])}</title><link>{p['url']}</link><pubDate>{p['date']}</pubDate></item>")
    rss.append("</channel></rss>")
    FEED.write_text("\n".join(rss), encoding="utf-8")

def main():
    # how many per run
    per_run = 5
    published = []
    dbp = DATA / "published.json"
    if dbp.exists():
        try: published = json.loads(dbp.read_text(encoding="utf-8"))
        except: published = []

    new_items = []
    for _ in range(per_run):
        kw = random.choice(KEYWORDS)
        city, title, h1, benefit, desc = pick_variant(kw)
        slug = slugify(f"{kw}-{city}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
        url  = f"{BASE_URL}/posts/{slug}/"
        html_out = article_html(url, title, h1, city, benefit, desc, kw)
        write_html(POSTS/slug/"index.html", html_out)
        new_items.append({"slug": slug, "title": title, "url": url, "date": datetime.utcnow().strftime("%Y-%m-%d")})
        # optional email
        mail = send_email_html(title, html_out)
        LOG.write_text((LOG.read_text(encoding="utf-8") if LOG.exists() else "") +
                       json.dumps({"ts": datetime.utcnow().isoformat(), "kw": kw, "title": title, "url": url, "mail": mail}) + "\n",
                       encoding="utf-8")

    published.extend(new_items)
    dbp.write_text(json.dumps(published, indent=2), encoding="utf-8")
    build_home_and_feeds(published)
    print(f"Generated {len(new_items)} articles.")

if __name__ == "__main__":
    main()
