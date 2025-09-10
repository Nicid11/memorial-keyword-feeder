import os, sys, re, random, json, csv, pathlib, html, hashlib, urllib.request, urllib.parse
from datetime import datetime

ROOT = pathlib.Path(__file__).parent
SITE = ROOT  # pages root
POSTS = SITE / "posts"; POSTS.mkdir(parents=True, exist_ok=True)
DATA = SITE / "data"; DATA.mkdir(exist_ok=True)
DB = DATA / "db.json"
SITEMAP = SITE / "sitemap.xml"
FEED = SITE / "feed.xml"
KEY_TXT = None

TARGET_URL = os.getenv("TARGET_URL","").strip()
BRAND_NAME = os.getenv("BRAND_NAME","Simply Averie").strip()
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL","").strip()
INDEXNOW_KEY = os.getenv("INDEXNOW_KEY","").strip()
REPO = os.getenv("GITHUB_REPOSITORY","owner/repo")
owner, repo = (REPO.split("/",1)+[""])[:2]
BASE_URL = f"https://{owner}.github.io/{repo}"

if not TARGET_URL:
    print("Missing TARGET_URL", file=sys.stderr); sys.exit(2)

# ------------ topics ------------
RELATIONS = ["mother","father","grandmother","grandfather","son","daughter","aunt","uncle","friend","mentor","veteran"]
CITIES = ["Philadelphia","West Philly","North Philly","South Philly","Camden","Upper Darby","Germantown","Manayunk","Roxborough","Cherry Hill"]
ANGLES = [
  "how to write an obituary step-by-step",
  "what to include in an online memorial page",
  "examples you can copy and personalize",
  "costs and options in {city}",
  "sharing with QR codes at services",
  "collecting photos and stories fast",
  "announcing services online the right way",
  "privacy and what to keep offline",
]
OPENERS = [
 "Create an online obituary today",
 "Dignified memorial page online",
 "Shareable tribute page for family",
 "Modern alternative to print obituaries",
 "Memorial website your family can keep",
 "Set up a tribute page in minutes",
]
BENEFITS = [
 "Elegant design, permanent link",
 "Built for phones and sharing",
 "Clear pricing, fast turnaround",
 "Keep memories visible, not buried",
 "One page they can visit forever",
 "Same-day setup available",
]
PROOFS = [
 "Families can visit anytime.",
 "Add photos and life story later.",
 "QR-ready for programs.",
 "Share with friends and church groups.",
]

def slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+","-",s).strip("-")
    return s[:80] or "post"

def pick():
    city = random.choice(CITIES)
    rel  = random.choice(RELATIONS)
    angle = random.choice(ANGLES).replace("{city}", city)
    opener = random.choice(OPENERS)
    benefit = random.choice(BENEFITS)
    proof = random.choice(PROOFS)
    title = f"{opener} — {angle.title()}"
    h1 = f"{opener} in {city}"
    return city, rel, angle, title, h1, benefit, proof

def uniq_slug(title):
    base = slugify(title)
    slug = base
    i = 2
    while (POSTS / slug / "index.html").exists():
        slug = f"{base}-{i}"; i += 1
    return slug

def ensure_db():
    if DB.exists():
        try: return json.loads(DB.read_text(encoding="utf-8"))
        except Exception: pass
    return {"published": []}

def save_db(db): DB.write_text(json.dumps(db, indent=2), encoding="utf-8")

def write_html(path, html_str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_str, encoding="utf-8")

def article_html(url, title, h1, city, rel, benefit, proof):
    ts = datetime.utcnow().strftime("%Y-%m-%d")
    utm = f"?utm_source=feeder&utm_medium=seo&utm_campaign=guides&utm_page={slugify(h1)}"
    cta_url = TARGET_URL + utm
    desc = f"{h1}. {benefit}. {proof}"
    faq = [
      {"@type":"Question","name":"How fast can we publish a memorial page?",
       "acceptedAnswer":{"@type":"Answer","text":"Same-day setup available for most families."}},
      {"@type":"Question","name":"Can we add photos later?",
       "acceptedAnswer":{"@type":"Answer","text":"Yes. You can add or edit photos and story at any time."}}
    ]
    schema = {
      "@context":"https://schema.org","@type":"Article",
      "headline": title,"datePublished": ts,"author": BRAND_NAME,
      "mainEntityOfPage": url
    }
    faq_schema = {"@context":"https://schema.org","@type":"FAQPage","mainEntity": faq}
    body = f"""
<!doctype html><meta charset="utf-8">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{url}">
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:760px;margin:32px auto;padding:0 16px;line-height:1.5}}
a.button{{display:inline-block;padding:10px 16px;background:#111;color:#fff;text-decoration:none}}
.card{{border:1px solid #e5e5e5;padding:16px;margin:16px 0}}
small,figure{{color:#666}}
</style>
<h1>{html.escape(h1)}</h1>
<p><small>Guide for families in {html.escape(city)} • Published {ts}</small></p>

<div class="card">
<p><strong>{benefit}.</strong> {proof} <a class="button" href="{cta_url}">Start a memorial</a></p>
</div>

<h2>1) What to include</h2>
<ul>
  <li>Full name, dates, city, key relationships</li>
  <li>Two or three defining stories</li>
  <li>Service details and preferred charities</li>
</ul>

<h2>2) Example for a {html.escape(rel)}</h2>
<p><em>“We celebrate the life of …”</em> Keep it short, specific, and warm. Add one line on impact and one on what they loved.</p>

<h2>3) Sharing it right</h2>
<p>Use a single link the whole family can share. Print a small QR code on programs and prayer cards.</p>

<h2>4) Online memorial vs. newspaper</h2>
<p>Online pages are searchable, editable, and affordable. Newspapers are short-lived and expensive.</p>

<p><a class="button" href="{cta_url}">Create an online obituary</a></p>

<script type="application/ld+json">{json.dumps(schema)}</script>
<script type="application/ld+json">{json.dumps(faq_schema)}</script>
"""
    return body

def home_html(items):
    items_html = "\n".join([f'<li><a href="{html.escape(u)}">{html.escape(t)}</a> — <small>{d}</small></li>' for (u,t,d) in items])
    return f"""<!doctype html><meta charset="utf-8">
<title>Memorial Guides | {html.escape(BRAND_NAME)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<h1>Memorial Guides</h1>
<p>Helpful articles for families. Created automatically.</p>
<ul>{items_html}</ul>
<p><small>Links include tracking. Destination: {html.escape(TARGET_URL)}</small></p>
"""

def gen_posts(n=4):
    db = ensure_db()
    published = db["published"]
    new_urls = []
    for _ in range(n):
        city, rel, angle, title, h1, benefit, proof = pick()
        slug = uniq_slug(title)
        url = f"{BASE_URL}/posts/{slug}/"
        html_out = article_html(url, title, h1, city, rel, benefit, proof)
        write_html(POSTS/slug/"index.html", html_out)
        published.append({"slug":slug,"title":title,"url":url,"date":datetime.utcnow().strftime("%Y-%m-%d")})
        new_urls.append(url)
    # update homepage
    latest = sorted(published, key=lambda r: r["slug"], reverse=True)[-100:][::-1]
    home_items = [(r["url"], r["title"], r["date"]) for r in latest[-30:]][::-1]
    write_html(SITE/"index.html", home_html(home_items))
    save_db({"published": published})
    return new_urls, published

def write_sitemap(published):
    urls = [f"{BASE_URL}/"] + [r["url"] for r in published]
    body = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    now = datetime.utcnow().strftime("%Y-%m-%d")
    for u in urls:
        body += [f"<url><loc>{u}</loc><lastmod>{now}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>"]
    body.append("</urlset>")
    SITEMAP.write_text("\n".join(body), encoding="utf-8")

def write_feed(published):
    items = published[-20:]
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<rss version="2.0"><channel><title>Memorial Guides</title><link>{BASE_URL}</link><description>Auto guides</description>']
    for r in items[::-1]:
        parts.append(f"<item><title>{html.escape(r['title'])}</title><link>{r['url']}</link><pubDate>{r['date']}</pubDate></item>")
    parts.append("</channel></rss>")
    FEED.write_text("\n".join(parts), encoding="utf-8")

def indexnow_ping(urls):
    if not INDEXNOW_KEY: return
    # drop a key file at root: {key}.txt with the key as contents
    keyfile = SITE / f"{INDEXNOW_KEY}.txt"
    keyfile.write_text(INDEXNOW_KEY, encoding="utf-8")
    payload = {
        "host": f"{owner}.github.io",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": urls
    }
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request("https://api.indexnow.org/indexnow", data=data, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("IndexNow:", resp.status)
    except Exception as e:
        print("IndexNow error:", e)

def main():
    new_urls, published = gen_posts(n=4)  # 4 posts per run
    write_sitemap(published)
    write_feed(published)
    # keep a plain list of new URLs
    (SITE/"new_urls.txt").write_text("\n".join(new_urls), encoding="utf-8")
    # ping Bing/IndexNow if key provided
    indexnow_ping(new_urls)
    print("Generated:", len(new_urls), "pages")

if __name__ == "__main__":
    main()
