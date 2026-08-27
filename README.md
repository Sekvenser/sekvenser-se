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

This generates `blog/<slug>.html` per post plus `blog/index.html` (a listing), from `posts/*.md`. The `blog/` output is gitignored — CI runs `build.py` automatically before every deploy, so just commit the `.md` file and push.

Each post's `og:image`/`twitter:image` (used when sharing the link) is picked in this order: the frontmatter `image:` field, then the first `![...](...)` image in the post body, then `assets/share.png` as a default.

To add a post: create `posts/your-slug.md` with the frontmatter above, run `python3 build.py` to check it, then commit and push.
