#!/usr/bin/env python3
"""Build blog/*.html from posts/*.md (YAML-ish frontmatter + minimal markdown).

Frontmatter fields: title, date (YYYY-MM-DD), author, tags (comma separated).
Usage: python3 build.py
"""
import html
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xescape

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT / "blog"
DEFAULT_IMAGE = "https://sekvenser.se/assets/share.png"
IMAGE_SRC_RE = re.compile(r'!\[.*?\]\((\S+?)(?:\s+".*?")?\)')
RSS_ICON = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M4 11a9 9 0 0 1 9 9"></path>'
    '<path d="M4 4a16 16 0 0 1 16 16"></path>'
    '<circle cx="5" cy="19" r="1.5" fill="currentColor"></circle>'
    "</svg>"
)

HEADER = """<header>
  <div class="masthead">
    <img class="logo" src="{root}assets/sekvenser-logo.svg" alt="Sekvenser logo">
    <p class="tagline">[ˈtɛkːnadɛ ˈseːrjɛr]</p>
  </div>
  <nav class="toolbar">
    <a href="{root}index.html#/om">Om</a>
    <a href="{root}index.html#/webbshop">Webbshop</a>
    <a href="{root}blog/" class="{blog_active}">Blogg</a>
    <a href="{root}index.html#/kontakt">Kontakt</a>
    <a href="{root}index.html#/lankar">Länkar</a>
    <a href="https://serieutgivning.sekvenser.se/" target="_blank" rel="noopener noreferrer" class="external">Svensk serieutgivning</a>
  </nav>
</header>
"""

FOOTER = "<footer>Sekvenser &ndash; tidskrift om tecknade serier.</footer>\n"

PAGE = """<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="icon" href="{root}assets/favicon.ico">
<link rel="stylesheet" href="{root}style.css">
<link rel="alternate" type="application/rss+xml" title="Sekvenser" href="{root}blog/rss.xml">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Sekvenser">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:locale" content="sv_SE">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}">
</head>
<body>
{header}
<main>
{body}
</main>
{footer}
<script src="{root}gallery.js" defer></script>
</body>
</html>
"""


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        sys.exit("missing --- frontmatter block")
    raw, body = m.group(1), m.group(2)
    meta = {}
    for line in raw.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return meta, body


def render_link(m):
    text, href = m.group(1), m.group(2)
    if re.match(r"^https?://", href):
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{text}</a>'
    return f'<a href="{href}">{text}</a>'


def inline(text):
    text = html.escape(text)
    text = re.sub(r"!\[(.*?)\]\((.*?)\)", r'<img src="\2" alt="\1">', text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", render_link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"(?<!\w)__(.+?)__(?!\w)", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def render_gallery(title, imgs):
    if not imgs:
        return ""
    cover_alt, cover_src = imgs[0]
    rest_html = "".join(
        f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" loading="lazy" hidden>'
        for alt, src in imgs[1:]
    )
    label = f"Öppna galleri: {html.escape(title)}" if title else "Öppna galleri"
    title_html = f'<span class="gallery-title">{html.escape(title)}</span>' if title else ""
    return (
        f'<div class="gallery">'
        f'<button type="button" class="gallery-trigger" aria-label="{label}">'
        f'<img src="{html.escape(cover_src)}" alt="{html.escape(cover_alt)}">'
        f"{title_html}"
        f"</button>"
        f"{rest_html}"
        f"</div>"
    )


def render_callout(kind, title, body):
    title_html = f'<p class="callout-title">{html.escape(title)}</p>' if title else ""
    return f'<div class="callout callout-{html.escape(kind)}">{title_html}{markdown_to_html(body)}</div>'


def markdown_to_html(md):
    lines = md.strip("\n").split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        fm = re.match(r"^:::(\S+)(?:\s+(.*))?$", line)
        if fm:
            kind, title = fm.group(1), (fm.group(2) or "").strip()
            i += 1
            block_lines = []
            while i < len(lines) and lines[i].strip() != ":::":
                block_lines.append(lines[i])
                i += 1
            i += 1
            if kind == "gallery":
                imgs = []
                for bl in block_lines:
                    img_m = re.match(r'^!\[(.*?)\]\((\S+?)\)$', bl.strip())
                    if img_m:
                        imgs.append(img_m.groups())
                out.append(render_gallery(title, imgs))
            else:
                out.append(render_callout(kind, title, "\n".join(block_lines)))
            continue
        if line.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                item_text = re.sub(r"^[-*]\s+", "", lines[i])
                items.append(f"<li>{inline(item_text)}</li>")
                i += 1
            out.append(f"<ul>{''.join(items)}</ul>")
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                item_text = re.sub(r"^\d+\.\s+", "", lines[i])
                items.append(f"<li>{inline(item_text)}</li>")
                i += 1
            out.append(f"<ol>{''.join(items)}</ol>")
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip():
            para.append(lines[i])
            i += 1
        img = re.match(r'^!\[(.*?)\]\((\S+?)(?:\s+"(.*?)")?\)$', para[0]) if len(para) == 1 else None
        if img:
            alt, src, caption = img.groups()
            fig = f'<img src="{html.escape(src)}" alt="{html.escape(alt)}">'
            if caption:
                fig += f"<figcaption>{inline(caption)}</figcaption>"
            out.append(f"<figure>{fig}</figure>")
            continue
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def excerpt(md, length=160):
    text = re.sub(r":::\S+.*?:::", "", md.strip(), flags=re.DOTALL)
    text = re.sub(r"!\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"[#*`_>]", "", text)
    text = re.sub(r"\s+", " ", text)
    return (text[:length] + "…") if len(text) > length else text


def share_image(meta, body, page_url):
    if meta.get("image"):
        return urljoin(page_url, meta["image"])
    m = IMAGE_SRC_RE.search(body)
    return urljoin(page_url, m.group(1)) if m else DEFAULT_IMAGE


def tag_slug(tag):
    return re.sub(r"[^\w-]", "", tag.strip().lower().replace(" ", "-"))


def render_tags(tags, href_prefix):
    return "".join(f'<a class="tag" href="{href_prefix}{tag_slug(t)}.html">{html.escape(t)}</a>' for t in tags)


def post_summary_card(p, post_href_prefix="", tag_href_prefix="tags/"):
    tags_html = render_tags(p["tags"], tag_href_prefix)
    img_src = f"{post_href_prefix}{p['image']}" if p.get("image") else None
    img_html = f'<img src="{html.escape(img_src)}" alt="">' if img_src else ""
    return (
        f'<div class="card post-summary">'
        f'<h2><a href="{post_href_prefix}{p["slug"]}.html">{html.escape(p.get("title", p["slug"]))}</a></h2>'
        f'<p class="byline">{p.get("date", "")} &middot; {p.get("author", "")}</p>'
        f"{img_html}"
        f'<p>{html.escape(p["excerpt"])}</p>'
        f'<p class="tags">{tags_html}</p>'
        f"</div>"
    )


def build_tag_pages(posts):
    by_tag = {}
    for p in posts:
        for t in p["tags"]:
            by_tag.setdefault(t, []).append(p)
    tags_dir = OUT_DIR / "tags"
    tags_dir.mkdir(exist_ok=True)
    for tag, tag_posts in by_tag.items():
        slug = tag_slug(tag)
        cards = "\n".join(post_summary_card(p, post_href_prefix="../", tag_href_prefix="") for p in tag_posts)
        body = (
            f'<div class="card"><h2>Tagg: {html.escape(tag)}</h2>'
            f'<p><a href="../index.html">&larr; Alla inlägg</a></p></div>'
            f"{cards}"
        )
        page_html = PAGE.format(
            title=f"Tagg: {html.escape(tag)} &ndash; Sekvenser",
            description=f"Inlägg taggade {html.escape(tag)} på Sekvenser.",
            root="../../",
            url=f"https://sekvenser.se/blog/tags/{slug}.html",
            image=DEFAULT_IMAGE,
            header=HEADER.format(root="../../", blog_active="active"),
            body=body,
            footer=FOOTER,
        )
        (tags_dir / f"{slug}.html").write_text(page_html)
    return by_tag


def build_rss(posts):
    items = []
    for p in posts:
        pub_date = datetime.strptime(p["date"], "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
        categories = "".join(f"<category>{xescape(t)}</category>" for t in p["tags"])
        items.append(
            "<item>"
            f"<title>{xescape(p.get('title', p['slug']))}</title>"
            f"<link>{xescape(p['url'])}</link>"
            f"<guid>{xescape(p['url'])}</guid>"
            f"<pubDate>{pub_date}</pubDate>"
            f"<description>{xescape(p['excerpt'])}</description>"
            f"{categories}"
            "</item>"
        )
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        "<title>Sekvenser</title>"
        "<link>https://sekvenser.se/blog/</link>"
        "<description>Nyheter och inlägg från Sekvenser.</description>"
        "<language>sv-se</language>"
        f"{''.join(items)}"
        "</channel></rss>"
    )
    (OUT_DIR / "rss.xml").write_text(rss)


def build_sitemap(posts, by_tag):
    entries = ["<url><loc>https://sekvenser.se/</loc></url>"]
    blog_lastmod = f"<lastmod>{posts[0]['date']}</lastmod>" if posts else ""
    entries.append(f"<url><loc>https://sekvenser.se/blog/</loc>{blog_lastmod}</url>")
    for p in posts:
        entries.append(f"<url><loc>{xescape(p['url'])}</loc><lastmod>{p['date']}</lastmod></url>")
    for tag, tag_posts in by_tag.items():
        loc = f"https://sekvenser.se/blog/tags/{tag_slug(tag)}.html"
        entries.append(f"<url><loc>{xescape(loc)}</loc><lastmod>{tag_posts[0]['date']}</lastmod></url>")
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{''.join(entries)}"
        "</urlset>"
    )
    (ROOT / "sitemap.xml").write_text(sitemap)


def build():
    OUT_DIR.mkdir(exist_ok=True)
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text())
        slug = path.stem
        meta["slug"] = slug
        meta["excerpt"] = excerpt(body)
        posts.append(meta)

        byline = f"{meta.get('date', '')} &middot; {meta.get('author', '')}"
        tags_html = render_tags(meta["tags"], "tags/")
        post_body = (
            f'<article class="card post">'
            f'<h1>{html.escape(meta.get("title", slug))}</h1>'
            f'<p class="byline">{byline}</p>'
            f'{markdown_to_html(body)}'
            f'<p class="tags">{tags_html}</p>'
            f'<p><a href="./">&larr; Alla inlägg</a></p>'
            f"</article>"
        )
        page_url = f"https://sekvenser.se/blog/{slug}.html"
        meta["url"] = page_url
        html_out = PAGE.format(
            title=f"{meta.get('title', slug)} &ndash; Sekvenser",
            description=html.escape(meta["excerpt"]),
            root="../",
            url=page_url,
            image=share_image(meta, body, page_url),
            header=HEADER.format(root="../", blog_active="active"),
            body=post_body,
            footer=FOOTER,
        )
        (OUT_DIR / f"{slug}.html").write_text(html_out)

    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    items = [post_summary_card(p) for p in posts]
    items.append(f'<p><a class="rss-link" href="rss.xml">{RSS_ICON} RSS-flöde</a></p>')
    index_html = PAGE.format(
        title="Blogg &ndash; Sekvenser",
        description="Nyheter och inlägg från Sekvenser.",
        root="../",
        url="https://sekvenser.se/blog/",
        image="https://sekvenser.se/assets/share.png",
        header=HEADER.format(root="../", blog_active="active"),
        body="\n".join(items) or "<p>Inga inlägg än.</p>",
        footer=FOOTER,
    )
    (OUT_DIR / "index.html").write_text(index_html)
    by_tag = build_tag_pages(posts)
    build_rss(posts)
    build_sitemap(posts, by_tag)
    print(f"built {len(posts)} post(s) into {OUT_DIR}/")


if __name__ == "__main__":
    build()
