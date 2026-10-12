"""Exploratory (not pre-registered), 2026-10-12: when the good-faith framing (C2) makes a
model say NO_SOURCE_FOUND more often, does it abstain where it would otherwise have been
wrong? If abstention were selective, the share of attempted (checkable) citations that
fail would drop under C2, and the extra abstention would sit in the model x task cells
where C0 fails most."""
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
out = []


def p(s=""):
    out.append(s)
    print(s)


def shares(S, label):
    p(f"### {label}")
    p()
    p("| condition | checkable claims | failed share | NO_SOURCE_FOUND lines | checkable claims per response |")
    p("|---|---|---|---|---|")
    for c in sorted({s["condition"] for s in S}):
        r = [s for s in S if s["condition"] == c]
        k = defaultdict(int)
        for s in r:
            for a, b in s["score"]["counts"].items():
                k[a] += b
        chk = k["verified"] + k["reworded"] + k["unsupported"] + k["dead_url"]
        p(f"| {c} | {chk} | {(k['unsupported'] + k['dead_url']) / chk:.1%} | "
          f"{sum(len(s['score']['no_source']) for s in r)} | {chk / len(r):.2f} |")
    p()


v4 = json.loads((ROOT / "v4" / "scored_main.json").read_text())
v2 = json.loads((ROOT / "v3" / "v2_rescored_a.json").read_text())
p("# Is the extra abstention under good-faith framing selective? (exploratory)")
p()
shares(v4, "v4: no web search (640 responses)")
shares(v2, "v2 Domain A: web search, re-scored with the fixed scorer (192 responses)")

# Cell level, v4: model x task
cells = defaultdict(lambda: defaultdict(list))
for s in v4:
    cells[(s["model"], s["task"])][s["condition"]].append(s)
x, y, z = [], [], []
for key, d in cells.items():
    c0, c2 = d["c0"], d["c2"]
    fail0 = mean(s["score"]["failed"] for s in c0)
    dnsf = mean(len(s["score"]["no_source"]) for s in c2) - mean(len(s["score"]["no_source"]) for s in c0)
    dfail = mean(s["score"]["failed"] for s in c2) - fail0
    x.append(fail0); y.append(dnsf); z.append(dfail)
r1 = spearmanr(x, y)
r2 = spearmanr(y, z)
p("### v4, per model x task cell (64 cells, 5 responses per condition each)")
p()
p(f"- C0 failure rate vs extra NO_SOURCE_FOUND under C2: Spearman rho = {r1.statistic:.2f}, p = {r1.pvalue:.3g}")
p(f"- Extra NO_SOURCE_FOUND under C2 vs change in failures: Spearman rho = {r2.statistic:.2f}, p = {r2.pvalue:.3g}")
p("  (selective abstention predicts: positive first rho, negative second rho)")
p()

# Response level, v4 C2: do responses that abstain somewhere fail less elsewhere?
p("### v4, response level")
p()
for c in ("c0", "c2"):
    r = [s for s in v4 if s["condition"] == c]
    a = [s for s in r if s["score"]["no_source"]]
    b = [s for s in r if not s["score"]["no_source"]]
    p(f"- {c}: responses with any NO_SOURCE_FOUND: {len(a)}, mean failed {mean(s['score']['failed'] for s in a):.2f}; "
      f"without: {len(b)}, mean failed {mean(s['score']['failed'] for s in b):.2f}")
p()
(Path(__file__).resolve().parent / "abstention_v4.md").write_text("\n".join(out) + "\n")
