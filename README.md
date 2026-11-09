# lwilsesamson.com

Static personal site, served by GitHub Pages at https://lwilsesamson.com (CNAME).

- Edit page bodies in `_pages/*.html`, then run `python3 _build.py` to regenerate `index.html` and `<slug>/index.html`.
- The CV is `_cv/cv.html`; render it with headless Chromium to `cv/Wilse-Samson-CV.pdf`.
- Papers live in `papers/`. Old URLs (`/papers`, `/apps`, `/courses`, `/contact`) redirect.
- The three chart previews on the Tools page are `tools/img/*.svg`, drawn by `python3 _previews/make_previews.py` from `_previews/data.json`, a dated snapshot of each tool's own data. Refresh the snapshot and the "as of" dates in `_pages/tools.html` together.
