"""Pre-registered analysis for v2 (EXPERIMENT_V2.md, "Analysis ... stated exactly").

Per domain:
  primary  C2 vs C0: two-sided Mann-Whitney U on the per-response primary metric
           + Fisher's exact on responses with >= 1 failed claim / fabricated issue
  H2       the same for C2 vs C1
  per-model tables, secondary metrics; C0 vs C1 is exploratory.
Domain A primary = dead_url + unsupported per response.
Domain B primary = fabricated / reported issues per response (0 if nothing reported).
Refuses to run Domain B while any issue is still unadjudicated.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from scipy.stats import fisher_exact, mannwhitneyu

HERE = Path(__file__).resolve().parent
S = json.loads((HERE / "scored_main.json").read_text())
assert len(S) == 408, f"expected 408 scored trials, got {len(S)}"
CONDS = ("c0", "c1", "c2")
out = []


def p(line=""):
    out.append(line)
    print(line)


def primary(s):
    sc = s["score"]
    return sc["failed"] if s["domain"] == "a" else sc["fabricated_share"]


def any_fail(s):
    sc = s["score"]
    return (sc["failed"] if s["domain"] == "a" else sc["counts"]["fabricated"]) > 0


def tests(rows, x, y):
    a = [primary(s) for s in rows if s["condition"] == x]
    b = [primary(s) for s in rows if s["condition"] == y]
    u = mannwhitneyu(a, b, alternative="two-sided")
    fa = sum(any_fail(s) for s in rows if s["condition"] == x)
    fb = sum(any_fail(s) for s in rows if s["condition"] == y)
    f = fisher_exact([[fa, len(a) - fa], [fb, len(b) - fb]])
    return u, f, (fa, len(a)), (fb, len(b))


for dom, label in (("a", "Domain A: citations (failed claims = dead URL + unsupported quote, per response)"),
                   ("b", "Domain B: code review (fabricated / reported issues, per response)")):
    rows = [s for s in S if s["domain"] == dom]
    if dom == "b":
        unknown = sum(s["score"]["counts"]["unknown"] for s in rows)
        if unknown:
            sys.exit(f"Domain B has {unknown} unadjudicated issues: run adjudicate.py first")
    p(f"## {label}")
    p()
    p("| condition | n | mean | median | responses with >=1 | " +
      ("claims: verified / reworded / unsupported / dead / unverifiable | NO_SOURCE_FOUND lines |" if dom == "a"
       else "issues: planted / dup / real / nitpick / fabricated | planted recall |"))
    p("|---|---|---|---|---|---|---|")
    for c in CONDS:
        r = [s for s in rows if s["condition"] == c]
        vals = [primary(s) for s in r]
        anyf = sum(any_fail(s) for s in r)
        if dom == "a":
            k = defaultdict(int)
            for s in r:
                for kk, vv in s["score"]["counts"].items():
                    k[kk] += vv
            extra = (f"{k['verified']} / {k['reworded']} / {k['unsupported']} / {k['dead_url']} / {k['unverifiable']} | "
                     f"{sum(len(s['score']['no_source']) for s in r)} |")
        else:
            k = defaultdict(int)
            for s in r:
                for kk, vv in s["score"]["counts"].items():
                    k[kk] += vv
            rec = sum(s["score"]["planted_found"] for s in r) / sum(s["score"]["planted_total"] for s in r)
            extra = f"{k['planted']} / {k['duplicate']} / {k['real']} / {k['nitpick']} / {k['fabricated']} | {rec:.1%} |"
        p(f"| {c} | {len(r)} | {mean(vals):.3f} | {median(vals):.3f} | {anyf}/{len(r)} | {extra}")
    p()
    for x, y, tag in (("c2", "c0", "PRIMARY (H1) C2 vs C0"), ("c2", "c1", "H2 C2 vs C1"), ("c1", "c0", "exploratory C1 vs C0")):
        u, f, fa, fb = tests(rows, x, y)
        p(f"- **{tag}**: Mann-Whitney U = {u.statistic:.1f}, p = {u.pvalue:.4g}; "
          f"Fisher (>=1): {fa[0]}/{fa[1]} vs {fb[0]}/{fb[1]}, OR = {f.statistic:.3g}, p = {f.pvalue:.4g}")
    p()
    p("Per model (mean primary metric):")
    p()
    p("| model | c0 | c1 | c2 |")
    p("|---|---|---|---|")
    for m in sorted({s["model"] for s in rows}):
        cells = []
        for c in CONDS:
            v = [primary(s) for s in rows if s["model"] == m and s["condition"] == c]
            cells.append(f"{mean(v):.3f} (n={len(v)})")
        p(f"| {m} | " + " | ".join(cells) + " |")
    p()

cost = sum((s.get("cost") or 0) for s in S)
p(f"Total model cost of the 408 main trials: ${cost:.2f}")
(HERE / "results_main.md").write_text("\n".join(out) + "\n")
