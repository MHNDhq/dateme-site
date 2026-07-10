#!/usr/bin/env python3
"""Build the DateMe blog: blog/src/*.md -> blog/<slug>/index.html + blog/index.html,
plus sitemap.xml and llms.txt (generated together so they never drift).

Usage: .venv/bin/python scripts/build_blog.py   (from the repo root)
"""
import datetime
import html
import json
import pathlib
import re
from string import Template

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "blog" / "src"
SITE = "https://dateme.mhndlabs.com"

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Hanken+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
FAVICON = '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 64 64\'%3E%3Crect width=\'64\' height=\'64\' rx=\'14\' fill=\'%23ff6b6b\'/%3E%3Ctext x=\'32\' y=\'46\' font-size=\'38\' text-anchor=\'middle\' fill=\'%23fff\'%3E%E2%99%A5%3C/text%3E%3C/svg%3E">'

BASE_CSS = """
:root{--bg:#0c0a0a;--panel:#171211;--text:#f3ebe6;--muted:#a59890;--faint:#665a55;
--line:rgba(243,235,230,.12);--line-2:rgba(243,235,230,.07);--accent:#ff6b6b;--accent-soft:#ffb0a3;
--serif:"Fraunces",Georgia,serif;--sans:"Hanken Grotesk",-apple-system,BlinkMacSystemFont,sans-serif;
--mono:"JetBrains Mono",ui-monospace,Menlo,monospace;}
*{box-sizing:border-box;margin:0;padding:0;}
html{-webkit-text-size-adjust:100%;}
body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:17px;line-height:1.65;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow-x:hidden;}
body::before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:radial-gradient(60vw 52vh at 80% -10%,rgba(255,107,107,.14),transparent 60%),var(--bg);}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.05;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}
.wrap{max-width:760px;margin:0 auto;padding:0 28px;}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:26px 0;border-bottom:1px solid var(--line-2);}
.mark{display:flex;align-items:center;gap:11px;font-family:var(--mono);font-weight:500;letter-spacing:.16em;font-size:13px;}
.mark .heart{color:var(--accent);font-size:15px;}
.mark a{color:inherit;text-decoration:none;}
.meta-nav{font-family:var(--mono);font-size:11.5px;letter-spacing:.14em;color:var(--faint);text-transform:uppercase;}
.meta-nav a{color:var(--muted);text-decoration:none;}
.meta-nav a:hover{color:var(--accent-soft);}
footer{margin-top:90px;border-top:1px solid var(--line);padding:32px 0 60px;display:flex;flex-wrap:wrap;gap:18px 28px;align-items:center;}
footer a{color:var(--muted);text-decoration:none;font-family:var(--mono);font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;transition:color .16s ease;}
footer a:hover{color:var(--accent-soft);}
footer .sig{margin-left:auto;font-family:var(--mono);font-size:12px;letter-spacing:.08em;color:var(--faint);text-transform:uppercase;}
"""

POST_CSS = """
.post-head{padding:72px 0 12px;}
.crumb{font-family:var(--mono);font-size:12px;letter-spacing:.24em;text-transform:uppercase;color:var(--accent);margin-bottom:26px;display:flex;align-items:center;gap:14px;}
.crumb::before{content:"";width:30px;height:1px;background:var(--accent);display:inline-block;}
.crumb a{color:inherit;text-decoration:none;}
h1{font-family:var(--serif);font-weight:500;font-optical-sizing:auto;font-size:clamp(2rem,5.4vw,3.1rem);line-height:1.08;letter-spacing:-.018em;max-width:22ch;}
.post-meta{font-family:var(--mono);font-size:12px;letter-spacing:.08em;color:var(--faint);margin-top:20px;text-transform:uppercase;}
article{padding:40px 0 0;}
article p{margin:0 0 22px;color:#d8cdc6;}
article a{color:var(--accent-soft);text-decoration:none;border-bottom:1px solid rgba(255,176,163,.35);transition:border-color .15s ease;}
article a:hover{border-color:var(--accent-soft);}
article h2{font-family:var(--serif);font-weight:500;font-size:1.65rem;line-height:1.2;letter-spacing:-.012em;margin:44px 0 16px;}
article h3{font-family:var(--serif);font-weight:500;font-size:1.25rem;line-height:1.25;margin:32px 0 10px;}
article ul,article ol{margin:0 0 22px 22px;color:#d8cdc6;}
article li{margin-bottom:8px;}
article li::marker{color:var(--accent);}
article strong{color:var(--text);font-weight:600;}
article em{font-family:var(--serif);font-style:italic;}
article blockquote{border-left:2px solid var(--accent);padding:4px 0 4px 20px;margin:0 0 22px;color:var(--muted);font-family:var(--serif);font-size:1.06em;}
article hr{border:0;height:1px;background:var(--line);margin:40px 0;}
.post-cta{margin-top:52px;border:1px solid var(--line);border-radius:18px;padding:26px 28px;background:linear-gradient(160deg,rgba(255,107,107,.05),transparent 45%),var(--panel);}
.post-cta .k{font-family:var(--mono);font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);margin-bottom:10px;}
.post-cta p{color:var(--muted);font-size:15px;margin:0 0 16px;max-width:56ch;}
.post-cta a.btn{display:inline-flex;align-items:center;gap:9px;font-weight:600;font-size:15px;text-decoration:none;border-radius:999px;padding:12px 22px;background:var(--accent);color:#2a0d0d;border:0;}
"""

INDEX_CSS = """
.blog-hero{padding:78px 0 20px;}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.24em;text-transform:uppercase;color:var(--accent);margin-bottom:26px;display:flex;align-items:center;gap:14px;}
.eyebrow::before{content:"";width:30px;height:1px;background:var(--accent);display:inline-block;}
h1{font-family:var(--serif);font-weight:500;font-size:clamp(2.2rem,6vw,3.4rem);line-height:1.04;letter-spacing:-.02em;max-width:16ch;}
h1 em{font-style:italic;color:var(--accent-soft);font-weight:400;}
.blog-hero p{color:var(--muted);max-width:48ch;margin-top:18px;font-size:1.05rem;}
.post-list{margin-top:54px;border-top:1px solid var(--line);}
.post-row{display:block;padding:30px 0 32px;border-bottom:1px solid var(--line-2);text-decoration:none;color:inherit;}
.post-row .n{font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--accent);margin-bottom:10px;display:flex;gap:16px;}
.post-row .n .d{color:var(--faint);}
.post-row h2{font-family:var(--serif);font-weight:500;font-size:1.55rem;line-height:1.18;letter-spacing:-.012em;margin:0 0 8px;transition:color .15s ease;}
.post-row:hover h2{color:var(--accent-soft);}
.post-row p{color:var(--muted);font-size:15px;max-width:64ch;}
"""

TOPBAR = """<div class="topbar">
    <div class="mark"><span class="heart">&#9829;</span><a href="/">DateMe</a></div>
    <div class="meta-nav"><a href="/blog/">Blog</a> &middot; <a href="/">App</a></div>
  </div>"""

FOOTER = """<footer>
    <a href="/">Home</a>
    <a href="/blog/">Blog</a>
    <a href="/privacy.html">Privacy</a>
    <a href="/support.html">Support</a>
    <span class="sig">On-device. No uploads. No AI faces.</span>
  </footer>"""

CTA = """<div class="post-cta">
      <div class="k">From the makers</div>
      <p>DateMe ranks your real dating photos on your iPhone &mdash; no uploads, no account, no AI faces &mdash; and shows the one fix that helps each photo most.</p>
      <a class="btn" href="https://testflight.apple.com/join/FyBj8Xsm">Try the free beta &rarr;</a>
    </div>"""

POST_TMPL = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<meta name="description" content="$description">
<link rel="canonical" href="$url">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta property="og:type" content="article">
<meta property="og:url" content="$url">
<meta property="og:site_name" content="DateMe">
<meta property="og:title" content="$title">
<meta property="og:description" content="$description">
<meta property="og:image" content="$site/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="$title">
<meta name="twitter:description" content="$description">
<meta name="twitter:image" content="$site/og.png">
<meta property="article:published_time" content="$date">
<meta name="theme-color" content="#0c0a0a">
$favicon
$fonts
<script type="application/ld+json">
$jsonld
</script>
<style>$css</style>
</head>
<body>
<div class="wrap">
  $topbar
  <div class="post-head">
    <div class="crumb"><a href="/blog/">DateMe blog</a></div>
    <h1>$h1</h1>
    <p class="post-meta">$pretty_date &middot; $read_min min read &middot; by Muhannad Ahmed</p>
  </div>
  <article>
$body
$cta
  </article>
  $footer
</div>
</body>
</html>
""")

INDEX_TMPL = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DateMe Blog &mdash; Honest Guides to Dating Photos &amp; Profiles</title>
<meta name="description" content="Research-backed, hype-free guides to dating-app photos and profiles from the makers of DateMe: what to lead with, what to fix, and what the science actually says.">
<link rel="canonical" href="$site/blog/">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta property="og:type" content="website">
<meta property="og:url" content="$site/blog/">
<meta property="og:site_name" content="DateMe">
<meta property="og:title" content="DateMe Blog &mdash; honest guides to dating photos">
<meta property="og:description" content="Research-backed, hype-free guides to dating-app photos and profiles, from the makers of DateMe.">
<meta property="og:image" content="$site/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="$site/og.png">
<meta name="theme-color" content="#0c0a0a">
$favicon
$fonts
<script type="application/ld+json">
$jsonld
</script>
<style>$css</style>
</head>
<body>
<div class="wrap">
  $topbar
  <section class="blog-hero">
    <div class="eyebrow">Field notes</div>
    <h1>Honest guides to <em>dating photos.</em></h1>
    <p>What the research actually says about profiles, photos, and matching &mdash; no looksmaxxing, no hacks, no filler. From the makers of DateMe.</p>
  </section>
  <div class="post-list">
$rows
  </div>
  $footer
</div>
</body>
</html>
""")


def parse_post(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: missing frontmatter")
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    for req in ("title", "description", "slug", "date"):
        if not meta.get(req):
            raise ValueError(f"{path.name}: missing frontmatter field '{req}'")
    body_md = m.group(2).strip()
    meta["words"] = len(re.findall(r"\w+", body_md))
    meta["read_min"] = max(2, round(meta["words"] / 220))
    meta["body_html"] = markdown.markdown(body_md, extensions=["extra", "smarty"])
    return meta


def post_jsonld(p):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": p["title"],
        "description": p["description"],
        "url": f"{SITE}/blog/{p['slug']}/",
        "datePublished": p["date"],
        "dateModified": p["date"],
        "image": f"{SITE}/og.png",
        "author": {"@type": "Person", "name": "Muhannad Ahmed", "url": "https://mhndlabs.com"},
        "publisher": {"@type": "Organization", "name": "MHND LABS", "url": "https://mhndlabs.com"},
        "mainEntityOfPage": f"{SITE}/blog/{p['slug']}/",
        "isPartOf": {"@type": "Blog", "@id": f"{SITE}/blog/#blog"},
    }, indent=2)


def index_jsonld(posts):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Blog",
        "@id": f"{SITE}/blog/#blog",
        "name": "DateMe Blog",
        "url": f"{SITE}/blog/",
        "description": "Research-backed, hype-free guides to dating-app photos and profiles.",
        "publisher": {"@type": "Organization", "name": "MHND LABS", "url": "https://mhndlabs.com"},
        "blogPost": [{"@type": "BlogPosting", "headline": p["title"],
                      "url": f"{SITE}/blog/{p['slug']}/", "datePublished": p["date"]}
                     for p in posts],
    }, indent=2)


def pretty(iso):
    return datetime.date.fromisoformat(iso).strftime("%B %-d, %Y")


def build():
    posts = sorted((parse_post(p) for p in SRC.glob("*.md")),
                   key=lambda p: (p["date"], p["slug"]), reverse=True)

    for p in posts:
        out = ROOT / "blog" / p["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(POST_TMPL.safe_substitute(
            title=html.escape(p["title"], quote=True),
            h1=html.escape(p["title"]),
            description=html.escape(p["description"], quote=True),
            url=f"{SITE}/blog/{p['slug']}/",
            site=SITE, date=p["date"], pretty_date=pretty(p["date"]),
            read_min=p["read_min"], jsonld=post_jsonld(p),
            css=BASE_CSS + POST_CSS, favicon=FAVICON, fonts=FONTS,
            topbar=TOPBAR, footer=FOOTER, cta=CTA, body=p["body_html"],
        ), encoding="utf-8")

    rows = "\n".join(
        f'    <a class="post-row" href="/blog/{p["slug"]}/">'
        f'<div class="n"><span>/ {i + 1:02d}</span><span class="d">{pretty(p["date"])}</span>'
        f'<span class="d">{p["read_min"]} min</span></div>'
        f'<h2>{html.escape(p["title"])}</h2>'
        f'<p>{html.escape(p["description"])}</p></a>'
        for i, p in enumerate(posts))
    (ROOT / "blog" / "index.html").write_text(INDEX_TMPL.safe_substitute(
        site=SITE, jsonld=index_jsonld(posts), css=BASE_CSS + INDEX_CSS,
        favicon=FAVICON, fonts=FONTS, topbar=TOPBAR, footer=FOOTER, rows=rows,
    ), encoding="utf-8")

    today = datetime.date.today().isoformat()
    urls = [(f"{SITE}/", today), (f"{SITE}/privacy.html", today),
            (f"{SITE}/support.html", today), (f"{SITE}/blog/", today)]
    urls += [(f"{SITE}/blog/{p['slug']}/", p["date"]) for p in posts]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls]
    sitemap.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    guides = "\n".join(f"- [{p['title']}]({SITE}/blog/{p['slug']}/): {p['description']}"
                       for p in posts)
    (ROOT / "llms.txt").write_text(f"""# DateMe

> DateMe: Rank Your Photos is an iPhone app that ranks a user's real dating photos entirely on-device, picks the strongest lead photo, shows the one fix that helps each photo most, and drafts dating-app bios in the user's own voice. Photos never leave the phone: no uploads, no account, no AI-generated faces. Built by MHND LABS (indie developer Muhannad Ahmed). Free public beta on TestFlight; App Store release September 2026. Requires iOS 26 or later; full AI coaching uses Apple Intelligence (iPhone 15 Pro or newer).

## Pages

- [Home](https://dateme.mhndlabs.com/): what DateMe does, how it works, FAQ
- [Privacy policy](https://dateme.mhndlabs.com/privacy.html): no data collected; on-device analysis explained
- [Support](https://dateme.mhndlabs.com/support.html): contact and help
- [TestFlight beta](https://testflight.apple.com/join/FyBj8Xsm): free public beta

## Guides

{guides}
""", encoding="utf-8")

    print(f"built {len(posts)} posts, blog index, sitemap.xml ({len(urls)} urls), llms.txt")


if __name__ == "__main__":
    build()
