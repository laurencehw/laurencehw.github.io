#!/usr/bin/env python3
"""Rebuild _previews/data.json from local clones of the tool repositories.

    python3 _previews/refresh_data.py \
        --fiscal ../fiscal-policy-calculator \
        --sa ../sa-policy-space \
        --bop ../balance-of-power
    python3 _previews/make_previews.py
    python3 _build.py

Any repository left out keeps its block from the current data.json, so one
tool can be refreshed without the others. Each block records the file it was
read from and the date of that data ("as_of"), and make_previews.py prints
those dates into the captions on the Tools page.
"""
import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data.json"

# The two proposals on the Tools page: one close to its published score, and one
# that shows the model's limits. A deficit increase is a cost; a cut is revenue.
FISCAL_CASES = [
    ("aca-ptc-extend-enhanced", "Enhanced ACA premium credits, extended", "CBO/JCT, publication 60437"),
    ("tariff-universal-10pct", "Universal 10% tariff", "Tax Foundation, Fiscal Fact 861"),
]


def fiscal(repo):
    site = repo / "site_data"
    manifest = json.loads((site / "manifest.json").read_text())
    score = json.loads((site / "validation" / "scorecard.json").read_text())
    entries = score["entries"]

    def summary(rows):
        gaps = [r["abs_percent_difference"] for r in rows]
        return {
            "n": len(gaps),
            "median_gap_pct": statistics.median(gaps),
            "within_10pct": sum(g <= 10 for g in gaps),
        }

    cases = []
    for pid, label, source in FISCAL_CASES:
        conv = json.loads((site / "presets" / f"{pid}.json").read_text())["conventional"]
        cred = conv["credibility"]
        cases.append({
            "id": pid,
            "label": label,
            "model": conv["ten_year_deficit_impact"],
            "model_window": conv["budget_window"].replace("\u2013", "-"),
            "published": cred["own_row_official_billions"],
            "published_source": source,
            "published_window": cred["own_row_window"],
            "tier": cred["own_row_tier_label"],
            "pct_from_published": cred["own_row_abs_pct_error"],
        })
    return {
        "source": "fiscal-policy-calculator site_data/presets/<id>.json and validation/scorecard.json",
        "as_of": manifest["scores_date"],
        "cases": cases,
        # Where these sit among all published comparisons on the methods page.
        "scorecard": {
            "fitted": summary([r for r in entries if r["calibrated_to_target"]]),
            "unfitted": summary([r for r in entries if not r["calibrated_to_target"]]),
        },
    }


def sa_policy_space(repo):
    snap = json.loads((repo / "data" / "pmg_snapshot.json").read_text())
    packages = json.loads((repo / "data" / "reform_packages.json").read_text())
    counts = {}
    for idea in snap["policy_ideas"]:
        if idea.get("reform_package") is not None:
            counts.setdefault(str(idea["reform_package"]), Counter())[idea["current_status"]] += 1
    return {
        "source": "sa-policy-space data/pmg_snapshot.json (policy_ideas.current_status by reform_package)",
        "as_of": snap["generated_at"][:10],
        "packages": [
            {"id": pid, "name": packages[pid]["name"], "counts": dict(counts[pid])}
            for pid in sorted(counts, key=int)
        ],
    }


def balance_of_power(repo):
    chart = json.loads((repo / "data" / "hierarchy" / "fed-liquidity-swaps.json").read_text())
    monthly = {}
    for row in chart["rows"]:
        if row.get("swaps_m") is None:
            continue
        ym = row["date"][:7]
        monthly[ym] = max(monthly.get(ym, 0.0), row["swaps_m"] / 1000)  # $ million -> $ billion
    return {
        "source": "balance-of-power data/hierarchy/fed-liquidity-swaps.json (FRED SWPT, weekly; monthly max here)",
        "as_of": chart["provenance"]["data_through"],
        "monthly_max_swaps_bn": [[k, round(v, 1)] for k, v in sorted(monthly.items())],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fiscal", type=Path, help="clone of laurencehw/fiscal-policy-calculator")
    ap.add_argument("--sa", type=Path, help="clone of laurencehw/sa-policy-space")
    ap.add_argument("--bop", type=Path, help="clone of laurencehw/balance-of-power")
    args = ap.parse_args()
    data = json.loads(DATA.read_text())
    for key, fn, repo in [
        ("fiscal", fiscal, args.fiscal),
        ("sa_policy_space", sa_policy_space, args.sa),
        ("balance_of_power", balance_of_power, args.bop),
    ]:
        if repo:
            data[key] = fn(repo.expanduser().resolve())
            print(f"{key}: as of {data[key]['as_of']}")
    DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
