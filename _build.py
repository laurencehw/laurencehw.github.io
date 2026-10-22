#!/usr/bin/env python3
"""Assemble the static pages from _head.tmpl + _pages/*.html + _foot.tmpl.

Run `python3 _build.py` after editing anything in _pages/. Output goes to
index.html and <slug>/index.html so URLs have no extension.
"""
from pathlib import Path

ROOT = Path(__file__).parent
HEAD = (ROOT / "_head.tmpl").read_text()
FOOT = (ROOT / "_foot.tmpl").read_text()

PAGES = {
    # slug: (title, description, nav key)
    "": ("Laurence Wilse-Samson", "Economist. Associate Director at Oxford Economics; adjunct at NYU Wagner and Columbia SIPA. Research on labor markets and technological change, industrial policy, and economic history.", None),
    "research": ("Research — Laurence Wilse-Samson", "Published papers, papers under review, and work in progress.", "R"),
    "teaching": ("Teaching — Laurence Wilse-Samson", "Courses at NYU Wagner, Columbia SIPA, and the University of Johannesburg.", "T"),
    "tools": ("Tools — Laurence Wilse-Samson", "Interactive tools and open textbooks.", "O"),
    "cv": ("CV — Laurence Wilse-Samson", "Curriculum vitae.", "C"),
}

for slug, (title, desc, key) in PAGES.items():
    body = (ROOT / "_pages" / f"{slug or 'index'}.html").read_text()
    head = HEAD.replace("{TITLE}", title).replace("{DESC}", desc).replace("{PATH}", f"{slug}/" if slug else "")
    for k in "RTOC":
        head = head.replace("{" + k + "}", ' aria-current="page"' if k == key else "")
    out = ROOT / (f"{slug}/index.html" if slug else "index.html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(head + body + FOOT)
    print("wrote", out.relative_to(ROOT))

# Redirects so links to the old site's paths keep working.
REDIRECTS = {"papers": "research", "apps": "tools", "courses": "teaching", "contact": "", "africa": "african-economic-future/"}
for old, new in REDIRECTS.items():
    d = ROOT / old
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(
        f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=/{new}">'
        f'<link rel="canonical" href="https://lwilsesamson.com/{new}"><title>Redirecting</title>'
        f'<a href="/{new}">/{new or ""}</a>\n')
    print("redirect", old, "->", "/" + new)
