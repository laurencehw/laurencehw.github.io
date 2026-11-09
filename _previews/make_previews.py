#!/usr/bin/env python3
"""Draw the three small chart previews on the Tools page.

Reads _previews/data.json, a snapshot taken from each tool's own data files
(the "source" and "as_of" fields say which file and when), and writes
tools/img/<name>.svg. Each SVG carries its own light and dark colours, so it
follows the reader's colour scheme when shown through <img>.

Refresh: re-extract data.json from the tool repositories, run this script,
then update the "as of" dates in _pages/tools.html.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "_previews" / "data.json").read_text())
OUT = ROOT / "tools" / "img"
OUT.mkdir(parents=True, exist_ok=True)

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
  .bar { fill: #1f4e79; } .bar2 { fill: #9fb6cc; } .pub { fill: none; stroke: #1d1d1b; stroke-width: 1.2; stroke-dasharray: 3 2; }
  @media (prefers-color-scheme: dark) {
    text { fill: #e8e6e0; }
    .mut { fill: #9a9892; }
    .ax { stroke: #33322f; }
    .ln { stroke: #8fb4d9; } .area { fill: #8fb4d9; opacity: 0.12; } .dot { fill: #8fb4d9; }
    .s-impl { fill: #5aa37f; } .s-part { fill: #2f5c45; } .s-rev { fill: #5a5954; }
    .s-deb { fill: #44433f; } .s-prop { fill: #2f2e2b; } .s-stall { fill: #c06a52; }
    .bar { fill: #8fb4d9; } .bar2 { fill: #3d5670; } .pub { stroke: #e8e6e0; }
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
    return svg(h, "".join(parts), "Status of 171 reform ideas, by reform package", desc)


def fiscal():
    d = DATA["fiscal"]
    narrow = W < 500
    rows = [
        ("Before importers respond" if not narrow else "Before response", d["static_revenue"], "bar2"),
        ("After they respond: the score" if not narrow else "After: the score", d["conventional_revenue"], "bar"),
    ]
    left, right, top, rh, gap = (112, 62, 10, 20, 12) if narrow else (200, 70, 10, 20, 12)
    scale = (W - left - right) / (max(d["published"], d["static_revenue"]) * 1.0)
    parts = []
    y = top
    for lab, v, cls in rows:
        parts.append(f'<text x="{left - 10}" y="{y + 14}" font-size="12.5" text-anchor="end">{lab}</text>')
        parts.append(f'<rect class="{cls}" x="{left}" y="{y}" width="{v * scale:.1f}" height="{rh}"/>')
        parts.append(f'<text x="{left + v * scale + 8:.1f}" y="{y + 14}" font-size="12">${v / 1000:.2f}T</text>')
        y += rh + gap
    v = d["published"]
    parts.append(f'<text x="{left - 10}" y="{y + 14}" font-size="12.5" text-anchor="end">{"Published" if narrow else "Tax Foundation, published"}</text>')
    parts.append(f'<rect class="pub" x="{left + 0.6}" y="{y + 0.6}" width="{v * scale - 1.2:.1f}" height="{rh - 1.2}"/>')
    parts.append(f'<text x="{left + v * scale + 8:.1f}" y="{y + 14}" font-size="12">${v / 1000:.2f}T</text>')
    y += rh + gap
    parts.append(f'<line class="ax" x1="{left}" x2="{left}" y1="{top - 4}" y2="{y - gap + 4}"/>')
    h = y + 2
    desc = (
        f'Universal 10% tariff, revenue over {d["window"]}: ${d["static_revenue"] / 1000:.2f} trillion before importers respond, '
        f'${d["conventional_revenue"] / 1000:.2f} trillion after (the calculator\'s conventional score), against '
        f'${d["published"] / 1000:.2f} trillion published by the Tax Foundation.'
    )
    return svg(h, "".join(parts), "What a universal 10% tariff raises over ten years", desc)


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
    return svg(h, "".join(parts), "Dollars lent to foreign central banks through Fed swap lines", desc)


# Full-column version, and a narrow one that phones load through <picture>, so the
# labels stay legible instead of shrinking with the image.
for W, suffix in [(640, ""), (360, "-narrow")]:
    for name, fn in [("sa-policy-space", sa_policy_space), ("fiscal-tariff", fiscal), ("fed-swap-lines", balance_of_power)]:
        (OUT / f"{name}{suffix}.svg").write_text(fn())
        print("wrote", (OUT / f"{name}{suffix}.svg").relative_to(ROOT))
