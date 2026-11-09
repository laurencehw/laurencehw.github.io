#!/usr/bin/env python3
"""Draw the three small chart previews on the Tools page.

Reads _previews/data.json, a snapshot taken from each tool's own data files
(the "source" and "as_of" fields say which file and when), and writes
tools/img/<name>.svg. Each SVG carries its own light and dark colours, so it
follows the reader's colour scheme when shown through <img>.

It also rewrites the three <figure> blocks in _pages/tools.html (between the
<!-- preview:NAME --> markers): image sizes, alt text and the dated caption all
come from the same snapshot, so a refresh cannot leave a stale date or number
on the page.

Refresh: python3 _previews/refresh_data.py --fiscal ... --sa ... --bop ...
(rebuilds data.json from local clones of the tools), then this script, then
python3 _build.py.
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "_previews" / "data.json").read_text())
OUT = ROOT / "tools" / "img"
OUT.mkdir(parents=True, exist_ok=True)
PAGE = ROOT / "_pages" / "tools.html"


def day(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


NUM = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

W = 640  # reset per variant below
FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'

# Light colours first; the dark-mode block overrides them. Site palette from style.css.
STYLE = """
<style>
  text { font-family: %s; fill: #1d1d1b; }
  .mut { fill: #6b6b66; }
  .ax { stroke: #e4e2dc; stroke-width: 1; }
  .ln { stroke: #1f4e79; stroke-width: 1.6; fill: none; }
  .area { fill: #1f4e79; opacity: 0.08; }
  .dot { fill: #1f4e79; }
  .s-impl { fill: #2d6a4f; } .s-part { fill: #8fbba2; } .s-rev { fill: #b9b6ae; }
  .s-deb { fill: #d6d3cb; } .s-prop { fill: #ebe9e3; } .s-stall { fill: #b5533c; }
  .bar { fill: #1f4e79; } .inb { fill: #ffffff; } .bar2 { fill: #9fb6cc; } .pub { fill: none; stroke: #1d1d1b; stroke-width: 1.2; stroke-dasharray: 3 2; }
  @media (prefers-color-scheme: dark) {
    text { fill: #e8e6e0; }
    .mut { fill: #9a9892; }
    .ax { stroke: #33322f; }
    .ln { stroke: #8fb4d9; } .area { fill: #8fb4d9; opacity: 0.12; } .dot { fill: #8fb4d9; }
    .s-impl { fill: #5aa37f; } .s-part { fill: #2f5c45; } .s-rev { fill: #5a5954; }
    .s-deb { fill: #44433f; } .s-prop { fill: #2f2e2b; } .s-stall { fill: #c06a52; }
    .bar { fill: #8fb4d9; } .inb { fill: #1d1d1b; } .bar2 { fill: #3d5670; } .pub { stroke: #e8e6e0; }
  }
</style>
""" % FONT


def svg(h, body, title, desc):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" '
        f'aria-labelledby="t d"><title id="t">{title}</title><desc id="d">{desc}</desc>{STYLE}{body}</svg>\n'
    )


def sa_policy_space():
    d = DATA["sa_policy_space"]
    order = [
        ("implemented", "s-impl", "Implemented"),
        ("partially_implemented", "s-part", "Partly"),
        ("under_review", "s-rev", "Under review"),
        ("debated", "s-deb", "Debated"),
        ("proposed", "s-prop", "Proposed"),
        ("stalled", "s-stall", "Stalled"),
    ]
    short = {
        "Infrastructure Unblock": "Infrastructure",
        "SMME & Employment Acceleration": "Small firms, jobs",
        "Human Capital Pipeline": "Skills, schooling",
        "Trade & Industrial Competitiveness": "Trade, industry",
        "State Capacity & Governance": "State capacity",
    }
    narrow = W < 500
    tail = "" if narrow else " moving"
    left, right, rh, gap = (118, 58, 18, 8) if narrow else (150, 92, 18, 9)
    top = 52 if narrow else 34
    scale = (W - left - right) / max(sum(p["counts"].values()) for p in d["packages"])
    parts = []
    # Legend
    x, ly = (6 if narrow else left), 8
    for k, (_, cls, lab) in enumerate(order):
        if narrow and k == 3:
            x, ly = 6, 26
        parts.append(f'<rect class="{cls}" x="{x}" y="{ly}" width="10" height="10"/>')
        parts.append(f'<text class="mut" x="{x + 14}" y="{ly + 9}" font-size="11">{lab}</text>')
        x += 14 + 6.4 * len(lab) + 14
    y = top
    for p in d["packages"]:
        c = p["counts"]
        n = sum(c.values())
        done = c.get("implemented", 0) + c.get("partially_implemented", 0)
        parts.append(f'<text x="{left - 10}" y="{y + 13}" font-size="12.5" text-anchor="end">{short[p["name"]]}</text>')
        x = left
        for key, cls, _ in order:
            w = c.get(key, 0) * scale
            if w:
                parts.append(f'<rect class="{cls}" x="{x:.1f}" y="{y}" width="{w:.1f}" height="{rh}"/>')
            x += w
        parts.append(f'<text class="mut" x="{x + 8:.1f}" y="{y + 13}" font-size="11.5">{done} of {n}{tail}</text>')
        y += rh + gap
    h = y + 4
    desc = "; ".join(
        f'{short[p["name"]]}: {p["counts"].get("implemented", 0)} implemented, '
        f'{p["counts"].get("partially_implemented", 0)} partly, {p["counts"].get("stalled", 0)} stalled, '
        f'of {sum(p["counts"].values())} ideas'
        for p in d["packages"]
    )
    total = sum(sum(p["counts"].values()) for p in d["packages"])
    return h, svg(h, "".join(parts), f"Status of {total} reform ideas, by reform package", desc)


def money(v):
    v = abs(v)
    return f"${v / 1000:.2f}T" if v >= 1000 else f"${v:.0f}bn"


def fiscal():
    """Each proposal's ten-year score as a share of its published estimate."""
    d = DATA["fiscal"]
    narrow = W < 500
    short = {"aca-ptc-extend-enhanced": "ACA credits", "tariff-universal-10pct": "10% tariff"}
    mid = {"aca-ptc-extend-enhanced": "ACA premium credits", "tariff-universal-10pct": "Universal 10% tariff"}
    left, right = (82, 104) if narrow else (150, 190)
    top, rh, gap, top_pad = 22, 20, 14, 8
    vmax = 120
    X = lambda pct: left + pct / vmax * (W - left - right)
    parts = [f'<text class="mut" x="{left}" y="12" font-size="11">Model score, % of published</text>']
    bottom = top + top_pad + len(d["cases"]) * (rh + gap) - gap
    for v in (0, 50, 100):
        cls = "pub" if v == 100 else "ax"
        parts.append(f'<line class="{cls}" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top}" y2="{bottom + 4}"/>')
        parts.append(f'<text class="mut" x="{X(v):.1f}" y="{bottom + 17}" font-size="11" text-anchor="middle">{"published" if v == 100 else v}</text>')
    y = top + top_pad
    for c in d["cases"]:
        pct = c["model"] / c["published"] * 100
        kind = "cost" if c["published"] > 0 else "raised"
        lab = (short if narrow else mid)[c["id"]]
        parts.append(f'<text x="{left - 10}" y="{y + 14}" font-size="12.5" text-anchor="end">{lab}</text>')
        parts.append(f'<rect class="bar" x="{left}" y="{y}" width="{X(pct) - left:.1f}" height="{rh}"/>')
        parts.append(f'<text class="inb" x="{X(pct) - 6:.1f}" y="{y + 14}" font-size="12" text-anchor="end">{pct:.0f}</text>')
        val = (f"{money(c['model'])} v {money(c['published'])}" if narrow
               else f"{money(c['model'])} {kind}, against {money(c['published'])}")
        parts.append(f'<text class="mut" x="{W - 4}" y="{y + 14}" font-size="11.5" text-anchor="end">{val}</text>')
        y += rh + gap
    h = bottom + 22
    desc = "; ".join(
        f'{mid[c["id"]]}: {money(c["model"])} against {money(c["published"])} published by {c["published_source"]}, '
        f'{c["model"] / c["published"] * 100:.0f}% of it'
        for c in d["cases"]
    )
    return h, svg(h, "".join(parts), "Two ten-year scores against the published estimates", desc)


def balance_of_power():
    d = DATA["balance_of_power"]
    pts = d["monthly_max_swaps_bn"]
    left, right, top, bottom, h = 40, 16, 14, 26, (170 if W < 500 else 190)
    y0, y1 = 0, 600
    x0 = 2007 + 11 / 12
    last = pts[-1][0]
    x1 = int(last[:4]) + (int(last[5:]) - 1) / 12

    def X(ym):
        t = int(ym[:4]) + (int(ym[5:]) - 1) / 12
        return left + (t - x0) / (x1 - x0) * (W - left - right)

    def Y(v):
        return top + (1 - (v - y0) / (y1 - y0)) * (h - top - bottom)

    parts = []
    for v in (0, 200, 400, 600):
        parts.append(f'<line class="ax" x1="{left}" x2="{W - right}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>')
        parts.append(f'<text class="mut" x="{left - 6}" y="{Y(v) + 4:.1f}" font-size="11" text-anchor="end">{v}</text>')
    for yr in (2008, 2012, 2016, 2020, 2024):
        parts.append(f'<text class="mut" x="{X(f"{yr}-01"):.1f}" y="{h - 8}" font-size="11" text-anchor="middle">{yr}</text>')
    line = " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, v in pts)
    area = f"{X(pts[0][0]):.1f},{Y(0):.1f} " + line + f" {X(pts[-1][0]):.1f},{Y(0):.1f}"
    parts.append(f'<polygon class="area" points="{area}"/>')
    parts.append(f'<polyline class="ln" points="{line}"/>')
    peaks = [max((p for p in pts if p[0] < "2010"), key=lambda p: p[1]), max((p for p in pts if p[0] > "2019"), key=lambda p: p[1])]
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    for k, v in peaks:
        lab = f"${v:.0f}bn, {months[int(k[5:]) - 1]} {k[:4]}"
        parts.append(f'<circle class="dot" cx="{X(k):.1f}" cy="{Y(v):.1f}" r="2.6"/>')
        parts.append(f'<text x="{X(k) + 7:.1f}" y="{Y(v) + 4:.1f}" font-size="11.5">{lab}</text>')
    desc = (
        f"Fed central bank liquidity swaps outstanding, monthly peak of weekly levels, December 2007 to {last}: "
        f"peaks of ${peaks[0][1]:.0f} billion in {peaks[0][0]} and ${peaks[1][1]:.0f} billion in {peaks[1][0]}, near zero otherwise."
    )
    return h, svg(h, "".join(parts), "Dollars lent to foreign central banks through Fed swap lines", desc)


def page_text():
    """Alt text and caption for each preview, from the same snapshot as the charts."""
    sa, fi, bp = DATA["sa_policy_space"], DATA["fiscal"], DATA["balance_of_power"]
    short = {"Infrastructure Unblock": "Infrastructure", "SMME & Employment Acceleration": "Small firms and jobs",
             "Human Capital Pipeline": "Skills and schooling", "Trade & Industrial Competitiveness": "Trade and industry",
             "State Capacity & Governance": "State capacity"}
    total = sum(sum(p["counts"].values()) for p in sa["packages"])
    sa_alt = f"Status of {total} reform ideas by package. " + " ".join(
        f'{short[p["name"]]}: {p["counts"].get("implemented", 0) + p["counts"].get("partially_implemented", 0)} '
        f'of {sum(p["counts"].values())}' + (" implemented or partly implemented." if k == 0 else ".")
        for k, p in enumerate(sa["packages"])
    )
    sa_cap = (f"As of {day(sa['as_of'])}: status of {total} reform ideas in {NUM.get(len(sa['packages']), len(sa['packages']))} packages. "
              "“Moving” counts ideas implemented or partly implemented.")

    aca, tar = fi["cases"]
    sc = fi["scorecard"]
    fi_alt = (f"Ten-year scores as a share of the published estimate. Extending the enhanced ACA premium credits: "
              f"{money(aca['model'])} cost against {money(aca['published'])} from {aca['published_source']}, "
              f"{aca['model'] / aca['published'] * 100:.0f}%. Universal 10% tariff: {money(tar['model'])} raised against "
              f"{money(tar['published'])} from the {tar['published_source']}, {tar['model'] / tar['published'] * 100:.0f}%.")
    fi_cap = (f"As of {day(fi['as_of'])}: ten-year scores as a share of the published estimate (dashed line), whose "
              f"window starts a year earlier. The credits land {round(aca['pct_from_published'])}% high; the module was "
              f"fitted to an earlier $350bn estimate, so this is close to home ground. The tariff lands "
              f"{round(tar['pct_from_published'])}% low with nothing fitted, which is typical where the model is not tuned: "
              f"across the {sc['unfitted']['n']} published estimates it was not fitted to, the median gap is "
              f"{round(sc['unfitted']['median_gap_pct'])}%, against {round(sc['fitted']['median_gap_pct'])}% for the "
              f"{sc['fitted']['n']} it was.")

    pts = bp["monthly_max_swaps_bn"]
    months = "January February March April May June July August September October November December".split()
    m = lambda ym: f"{months[int(ym[5:]) - 1]} {ym[:4]}"
    pk = [max((p for p in pts if p[0] < "2010"), key=lambda p: p[1]), max((p for p in pts if p[0] > "2019"), key=lambda p: p[1])]
    bp_alt = (f"Dollars lent to foreign central banks through Fed swap lines, {m(pts[0][0])} to {m(pts[-1][0])}: peaks "
              f"of ${pk[0][1]:.0f} billion in {m(pk[0][0])} and ${pk[1][1]:.0f} billion in {m(pk[1][0])}, near zero otherwise.")
    bp_cap = (f"As of {day(bp['as_of'])}: Fed central bank liquidity swaps, highest weekly level each month since "
              f"{m(pts[0][0])}. $ billion. Federal Reserve H.4.1 via FRED.")
    return {"sa-policy-space": (sa_alt, sa_cap), "fiscal-scores": (fi_alt, fi_cap), "fed-swap-lines": (bp_alt, bp_cap)}


# Full-column version, and a narrow one that phones load through <picture>, so the
# labels stay legible instead of shrinking with the image.
heights = {}
for W, suffix in [(640, ""), (360, "-narrow")]:
    for name, fn in [("sa-policy-space", sa_policy_space), ("fiscal-scores", fiscal), ("fed-swap-lines", balance_of_power)]:
        h, text = fn()
        heights[name + suffix] = h
        (OUT / f"{name}{suffix}.svg").write_text(text)
        print("wrote", (OUT / f"{name}{suffix}.svg").relative_to(ROOT))

# The figure blocks on the Tools page. The chart links to the same page as the
# question above it; it stays in the tab order so its alt text is announced.
page = PAGE.read_text()
for name, (alt, cap) in page_text().items():
    pattern = re.compile(rf'(<!-- preview:{name} -->\s*<figure class="preview">\s*<a href="([^"]+)">).*?(</figure>)', re.S)
    found = pattern.search(page)
    if not found:
        raise SystemExit(f"no <!-- preview:{name} --> block in {PAGE.relative_to(ROOT)}")
    block = (
        f'{found.group(1)}<picture><source media="(max-width: 520px)" srcset="/tools/img/{name}-narrow.svg" '
        f'width="360" height="{heights[name + "-narrow"]}"><img src="/tools/img/{name}.svg" width="640" '
        f'height="{heights[name]}" alt="{esc(alt)}"></picture></a>\n    <figcaption>{esc(cap)}</figcaption>\n  </figure>'
    )
    page = page[: found.start()] + block + page[found.end():]
PAGE.write_text(page)
print("updated", PAGE.relative_to(ROOT))
