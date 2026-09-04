# sekvenser.se

Static site, deployed to GitHub Pages on push to `main` (see `.github/workflows/pages.yml`). No build step for the main site — `index.html`, `style.css`, `app.js` are served as-is.

## Blog

Posts live as markdown files in `posts/`, one file per post:

```
---
title: Post title
date: 2026-08-27
author: Author name
tags: comma, separated, tags
image: path/to/share-image.png
---

Markdown body here. Supports **bold**, *italic*, [links](https://example.com),
![images](path/to/image.png), `code`, headings (`#`), lists (`-` or `1.`),
and fenced code blocks (```).
```

To preview locally:

```
python3 build.py
open blog/index.html
```

This generates `blog/<slug>.html` per post, `blog/index.html` (a listing), `blog/tags/<tag>.html` per tag used across all posts, `blog/rss.xml` (an RSS 2.0 feed of all posts), and `sitemap.xml` at the site root (homepage, blog index, every post, and every tag page), from `posts/*.md`. All of this generated output is gitignored — CI runs `build.py` automatically before every deploy, so just commit the `.md` file and push.

Tags are clickable on a post's own page, linking to that tag's listing. They're plain text on listing cards (post-summary and tag-page cards), since those cards are themselves links to the post — nesting a link inside a link isn't valid HTML.

Each post's `og:image`/`twitter:image` (used when sharing the link) is picked in this order: the frontmatter `image:` field, then the first `![...](...)` image in the post body, then `assets/share.png` as a default.

To add a post: create `posts/your-slug.md` with the frontmatter above, run `python3 build.py` to check it, then commit and push.

### Image galleries

Drop a `:::gallery` block into a post body to get a click-to-open lightbox:

```
:::gallery Optional title
![Caption for image 1](../gallery/foo/1.webp)
![Caption for image 2](../gallery/foo/2.webp)
![Caption for image 3](../gallery/foo/3.webp)
:::
```

Only the first image renders on the page, as the gallery's clickable cover (with the title overlaid, if given). Clicking it opens a full-screen modal with the caption, and accessible prev/next buttons that wrap around at both ends (Escape closes it, focus returns to the cover). See `posts/galleri.md` for a working example, and `gallery/galleri1/` for where its source images live — put a new gallery's images in their own subfolder under `gallery/`. The lightbox behavior lives in `gallery.js`, loaded on every generated blog page; styling is in `style.css` under `.gallery`/`.gallery-modal`.

### Callout blocks

Any other `:::name` block (not `gallery`) becomes a styled callout box that stands out from the surrounding text — for asides, warnings, bios, etc:

```
:::info
Klicka på bilden för att öppna galleriet.
:::

:::warning Innehåller spoilers
Bilderna är utdrag ur ett kommande album.
:::

:::bio Om skaparen
Fri text, kan använda **markdown** som vanligt.
:::
```

The optional word after `:::` on the opening line becomes a title label; the rest of the block is normal markdown. `info`, `warning`, and `bio` have their own accent color and a small classic printer's-mark icon (`※`, `‡`, `❧`) defined in `style.css` under `.callout-*`; any other name falls back to a plain boxed-with-a-bar look. Add a new `.callout-<name>` rule in `style.css` to give a new kind its own color/icon.

## Images

Before referencing a photo in a post or `index.html`, shrink and convert it with `optimize_image.py` (needs Pillow: `pip install pillow`):

```
python3 optimize_image.py assets/photo.jpg
```

This writes `assets/photo.webp` resized to 1200px wide (the site's content column is ~604px, so 1200px covers retina screens without shipping oversized source photos) and re-encoded as webp. Use the `.webp` file's path in the post/frontmatter/`<img>` tag; the original is left untouched.
