#!/usr/bin/env python3
"""Build blog/*.html from posts/*.md (YAML-ish frontmatter + minimal markdown).

Frontmatter fields: title, date (YYYY-MM-DD), author, tags (comma separated).
Usage: python3 build.py
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT / "blog"

HEADER = """<header>
  <div class="masthead">
    <img class="logo" src="{root}assets/sekvenser-logo.svg" alt="Sekvenser logo">
    <p class="tagline">[ˈtɛkːnadɛ ˈseːrjɛr]</p>
  </div>
  <nav class="toolbar">
    <a href="{root}index.html#/om">Om</a>
    <a href="{root}index.html#/webbshop">Webbshop</a>
    <a href="{root}index.html#/kontakt">Kontakt</a>
    <a href="{root}index.html#/lankar">Länkar</a>
    <a href="{root}blog/" class="{blog_active}">Blogg</a>
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


def inline(text):
    text = html.escape(text)
    text = re.sub(r"!\[(.*?)\]\((.*?)\)", r'<img src="\2" alt="\1">', text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def markdown_to_html(md):
    lines = md.strip("\n").split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
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
    text = re.sub(r"[#*`\[\]!()_>]", "", md.strip())
    text = re.sub(r"\s+", " ", text)
    return (text[:length] + "…") if len(text) > length else text


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
        tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in meta["tags"])
        post_body = (
            f'<article class="card post">'
            f'<h1>{html.escape(meta.get("title", slug))}</h1>'
            f'<p class="byline">{byline}</p>'
            f'{markdown_to_html(body)}'
            f'<p class="tags">{tags_html}</p>'
            f'<p><a href="./">&larr; Alla inlägg</a></p>'
            f"</article>"
        )
        html_out = PAGE.format(
            title=f"{meta.get('title', slug)} &ndash; Sekvenser",
            description=html.escape(meta["excerpt"]),
            root="../",
            url=f"https://sekvenser.se/blog/{slug}.html",
            image="https://sekvenser.se/assets/share.png",
            header=HEADER.format(root="../", blog_active="active"),
            body=post_body,
            footer=FOOTER,
        )
        (OUT_DIR / f"{slug}.html").write_text(html_out)

    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    items = []
    for p in posts:
        tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in p["tags"])
        items.append(
            f'<article class="card post-summary">'
            f'<h2><a href="{p["slug"]}.html">{html.escape(p.get("title", p["slug"]))}</a></h2>'
            f'<p class="byline">{p.get("date", "")} &middot; {p.get("author", "")}</p>'
            f'<p>{html.escape(p["excerpt"])}</p>'
            f'<p class="tags">{tags_html}</p>'
            f"</article>"
        )
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
    print(f"built {len(posts)} post(s) into {OUT_DIR}/")


if __name__ == "__main__":
    build()
