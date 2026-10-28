#!/usr/bin/env python3
"""Build blog pages from posts/*.md.

Each post starts with a header block, then Markdown:

    ---
    title: Making cloud masks
    date: 2026-11-03
    description: One sentence for search results and link previews.
    ---

    Post text in Markdown...

posts/cloud-masks.md becomes blog/cloud-masks.html. Add `draft: true` to keep a
post off the site. The Writing section on index.html lists every published post,
newest first, and stays hidden until there is at least one. The "Last updated"
date in the footer is set to today, so it tracks the latest commit.
"""

import datetime
import html
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("build.py needs the markdown package: pip install markdown")

ROOT = Path(__file__).resolve().parent
POSTS = ROOT / "posts"
BLOG = ROOT / "blog"
INDEX = ROOT / "index.html"

FONTS = "https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=Young+Serif&display=swap"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · Pushkar Kopparla</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23fff'/%3E%3Ctext x='16' y='22.5' font-family='Georgia,Times New Roman,serif' font-size='17' font-weight='bold' text-anchor='middle' fill='%23000'%3EPK%3C/text%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{fonts}">
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <main>
    <p class="home"><a href="../">Pushkar Kopparla</a></p>
    <article class="post">
      <header>
        <h1>{title}</h1>
        <time datetime="{iso}">{long_date}</time>
      </header>
      <div class="post-body">
{body}
      </div>
    </article>
    <p class="back"><a href="../#writing">&larr; All writing</a></p>
  </main>
</body>
</html>
"""


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit(f"{path}: missing the --- header block at the top")
    meta = {}
    for line in m.group(1).splitlines():
        if line.strip():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    for key in ("title", "date"):
        if key not in meta:
            sys.exit(f"{path}: header is missing '{key}'")
    try:
        meta["date"] = datetime.date.fromisoformat(meta["date"])
    except ValueError:
        sys.exit(f"{path}: date must look like 2026-11-03")
    meta["slug"] = path.stem
    meta["body"] = text[m.end():]
    return meta


def main():
    posts = [parse(p) for p in sorted(POSTS.glob("*.md"))]
    posts = [p for p in posts if p.get("draft", "").lower() != "true"]
    posts.sort(key=lambda p: p["date"], reverse=True)

    # blog/ is entirely generated: rebuild it from scratch.
    BLOG.mkdir(exist_ok=True)
    for old in BLOG.glob("*.html"):
        old.unlink()

    for p in posts:
        body = markdown.markdown(p["body"], extensions=["fenced_code", "tables", "footnotes"])
        (BLOG / f"{p['slug']}.html").write_text(PAGE.format(
            title=html.escape(p["title"]),
            description=html.escape(p.get("description", p["title"])),
            fonts=FONTS,
            iso=p["date"].isoformat(),
            long_date=f"{p['date'].day} {p['date']:%B %Y}",
            body=body,
        ), encoding="utf-8")

    items = "".join(
        f'\n          <li><a href="blog/{p["slug"]}.html">{html.escape(p["title"])}</a> '
        f'<time datetime="{p["date"].isoformat()}">{p["date"]:%b %Y}</time></li>'
        for p in posts
    )
    index = INDEX.read_text(encoding="utf-8")
    index = re.sub(r"(<!-- posts:start -->).*?(\n *<!-- posts:end -->)",
                   lambda m: m.group(1) + items + m.group(2), index, flags=re.S)
    index = re.sub(r'<section id="writing"( hidden)?>',
                   '<section id="writing">' if posts else '<section id="writing" hidden>', index)
    today = datetime.date.today()
    index = re.sub(r'<time id="updated" datetime="[^"]*">[^<]*</time>',
                   f'<time id="updated" datetime="{today.isoformat()}">{today.day} {today:%B %Y}</time>', index)
    INDEX.write_text(index, encoding="utf-8")

    print(f"build.py: {len(posts)} post(s) published")


if __name__ == "__main__":
    main()
