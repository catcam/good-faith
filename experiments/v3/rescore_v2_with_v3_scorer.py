"""Sensitivity check (not pre-registered): re-score v2's Domain A main responses with the
v3 scorer, whose three fixes came from v3 pilot 2 (page's .md version, rendered page,
"[...]" editorial insertions). Writes v2_rescored_a.json and prints the v2 tests again."""
import json
import sys
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "v2"))
sys.path.insert(0, str(HERE))
import scorer  # noqa: E402  (v3/scorer.py)
from scipy.stats import fisher_exact, mannwhitneyu  # noqa: E402

V2 = HERE.parent / "v2"
rows = [r for r in json.loads((V2 / "matrix_main.json").read_text()) if r["domain"] == "a"]
out = []
for r in rows:
    d = json.loads((V2 / "raw" / f"{r['trial_id']}.json").read_text())
    out.append({**r, "score": scorer.score_a(d["response"]["content"])})
(HERE / "v2_rescored_a.json").write_text(json.dumps(out, indent=1))
old = {s["trial_id"]: s for s in json.loads((V2 / "scored_main.json").read_text())}
for c in ("c0", "c1", "c2"):
    r = [s for s in out if s["condition"] == c]
    print(c, "failed/response old %.3f new %.3f" % (mean(old[s["trial_id"]]["score"]["failed"] for s in r),
                                                     mean(s["score"]["failed"] for s in r)))
f = {c: [s["score"]["failed"] for s in out if s["condition"] == c] for c in ("c0", "c1", "c2")}
for x, y in (("c2", "c0"), ("c2", "c1")):
    u = mannwhitneyu(f[x], f[y], alternative="two-sided")
    a, b = sum(v > 0 for v in f[x]), sum(v > 0 for v in f[y])
    fe = fisher_exact([[a, len(f[x]) - a], [b, len(f[y]) - b]])
    print(f"{x} vs {y}: MWU p = {u.pvalue:.4g}; Fisher {a}/{len(f[x])} vs {b}/{len(f[y])} p = {fe.pvalue:.4g}")
by = {}
for s in out:
    by.setdefault((s["task"], s["condition"]), []).append(s["score"]["failed"])
for t in sorted({s["task"] for s in out}):
    print(t, " ".join("%s %.2f" % (c, mean(by[(t, c)])) for c in ("c0", "c1", "c2")))
