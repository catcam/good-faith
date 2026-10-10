"""Pre-registered analysis for v4 (EXPERIMENT_V4.md, "Analysis").

Primary:   C2 vs C0, two-sided Mann-Whitney U on failed claims (dead_url + unsupported) per response.
Secondary: permutation test of the mean difference, labels shuffled within model x task strata;
           Fisher's exact on responses with >= 1 failed claim.
Per-model table and descriptive counts. Nothing else is confirmatory.
"""
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

from scipy.stats import fisher_exact, mannwhitneyu

HERE = Path(__file__).resolve().parent
S = json.loads((HERE / "scored_main.json").read_text())
out = []


def p(line=""):
    out.append(line)
    print(line)


def failed(s):
    return s["score"]["failed"]


c0 = [failed(s) for s in S if s["condition"] == "c0"]
c2 = [failed(s) for s in S if s["condition"] == "c2"]
p(f"Completed trials: {len(S)} of 640 (c0 {len(c0)}, c2 {len(c2)})")
p()
p("| condition | n | mean failed / response | responses with >=1 | verified / reworded / unsupported / dead / unverifiable | NO_SOURCE_FOUND lines |")
p("|---|---|---|---|---|---|")
for c in ("c0", "c2"):
    r = [s for s in S if s["condition"] == c]
    k = defaultdict(int)
    for s in r:
        for kk, vv in s["score"]["counts"].items():
            k[kk] += vv
    p(f"| {c} | {len(r)} | {mean(failed(s) for s in r):.3f} | {sum(failed(s) > 0 for s in r)}/{len(r)} | "
      f"{k['verified']} / {k['reworded']} / {k['unsupported']} / {k['dead_url']} / {k['unverifiable']} | "
      f"{sum(len(s['score']['no_source']) for s in r)} |")
p()

u = mannwhitneyu(c2, c0, alternative="two-sided")
p(f"- **PRIMARY (H1) C2 vs C0**: Mann-Whitney U = {u.statistic:.1f}, p = {u.pvalue:.4g}")

strata = defaultdict(list)
for s in S:
    strata[(s["model"], s["task"])].append(s)
obs = mean(c2) - mean(c0)
rng = random.Random("good-faith-v4-perm")
N, extreme = 10000, 0
for _ in range(N):
    a, b = [], []
    for rows in strata.values():
        labels = [s["condition"] for s in rows]
        rng.shuffle(labels)
        for s, lab in zip(rows, labels):
            (b if lab == "c2" else a).append(failed(s))
    if abs(mean(b) - mean(a)) >= abs(obs) - 1e-12:
        extreme += 1
p(f"- Stratified permutation (model x task), mean diff C2 - C0 = {obs:.3f}, p = {(extreme + 1) / (N + 1):.4g}")

f0 = sum(x > 0 for x in c0)
f2 = sum(x > 0 for x in c2)
f = fisher_exact([[f2, len(c2) - f2], [f0, len(c0) - f0]])
p(f"- Fisher (>=1 failed): {f2}/{len(c2)} vs {f0}/{len(c0)}, OR = {f.statistic:.3g}, p = {f.pvalue:.4g}")
p()
p("Per model (mean failed / response):")
p()
p("| model | c0 | c2 |")
p("|---|---|---|")
for m in sorted({s["model"] for s in S}):
    cells = [f"{mean(failed(s) for s in S if s['model'] == m and s['condition'] == c):.3f}" for c in ("c0", "c2")]
    p(f"| {m} | " + " | ".join(cells) + " |")
p()
p(f"Total model cost: ${sum((s.get('cost') or 0) for s in S):.2f}")
(HERE / "results_main.md").write_text("\n".join(out) + "\n")
