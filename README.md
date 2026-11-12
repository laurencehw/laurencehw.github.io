# lwilsesamson.com

Static personal site, served by GitHub Pages at https://lwilsesamson.com (CNAME).

- Edit page bodies in `_pages/*.html`, then run `python3 _build.py` to regenerate `index.html` and `<slug>/index.html`.
- The CV is `_cv/cv.html`; render it with headless Chromium to `cv/Wilse-Samson-CV.pdf`.
- Papers live in `papers/`. Old URLs (`/papers`, `/apps`, `/courses`, `/contact`) redirect.
- The three chart previews on the Tools page are `tools/img/*.svg`, drawn from `_previews/data.json`, a dated snapshot of each tool's own data. To refresh: `python3 _previews/refresh_data.py --fiscal <clone> --sa <clone> --bop <clone>` (any subset), then `python3 _previews/make_previews.py`, then `python3 _build.py`. The second script also rewrites the figure blocks in `_pages/tools.html` (between the `<!-- preview:NAME -->` markers), so the alt text, the numbers and the "As of" date in each caption always match the chart. Edit caption wording in the script, not the page.
- The Merger Lab (`/tools/merger-lab/`) is `_pages/tools/merger-lab.html` plus its engine `tools/merger-lab.js`, a port of `run_logit_sim()` from the Antitrust Methods book. After changing the engine run `node _tests/merger_lab_check.js`.
