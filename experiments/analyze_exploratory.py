"""Exploratory analyses beyond the pre-registered primary metric (fabrication
rate), per EXPERIMENT.md's stated clause: "Anything else that turns up in the
data gets reported as exploratory, explicitly labeled as such, not folded
into the primary result." Does NOT touch design_matrix.json, verify.py, or
the primary fabrication_rate calculation -- purely additive analysis over
already-scored data.

Two analyses, both motivated by a real finding (2026-08-25): c2's elevated
fabrication rate in Domain A (73.33%, n=7 trials) turned out to be driven
almost entirely by 2 of 7 trials (t0033, t0066), both showing the same
pattern -- invent a handful of specific fake sources, then generate several
dependent claims elaborating on each ("a quote from X", "techniques
described in X") that all get counted as separate fabricated claims. This
inflates the aggregate rate in a way that looks like "many independent bad
judgment calls" when it's closer to "a few root fabrications, each
generating multiple counted sub-claims."

1. Root-vs-dependent fabrication clustering: groups each trial's
   fabricated_details strings by a shared "key" (the URL/repo/quote-source
   token mentioned in the string) to estimate how many DISTINCT invented
   sources actually drove a trial's fabricated-claim count, vs how many of
   those counted claims are just elaboration on an already-invented root.
2. Outlier-trial flagging: for each condition/domain cell, flags any single
   trial contributing more than OUTLIER_THRESHOLD of that cell's total
   fabricated-claim count -- so a small-sample cell (e.g. c2/domain-a, n=7)
   doesn't get its headline percentage silently dominated by one bad trial
   without that being visible.

Run standalone: `python3 analyze_exploratory.py`
Also called automatically at the end of every run_trial_batch.py batch (see
that file's main()), so this re-runs and stays current on every cron fire --
"kad god mogu", not just on manual request.
"""
from __future__ import annotations
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "experiments" / "raw"
SCORED_CSV = ROOT / "experiments" / "results" / "scored.csv"
EXPLORATORY_MD = ROOT / "experiments" / "results" / "exploratory.md"

OUTLIER_THRESHOLD = 0.30  # a single trial contributing >30% of a cell's total
                          # fabricated claims gets flagged explicitly


# Loose token extraction from a fabricated_details string -- these are free-text
# judge output, not structured data, so this is a best-effort heuristic, not an
# exact parser. Prefers a URL/repo/domain-like token; falls back to the first
# few words if none found. Good enough to cluster "same invented source,
# multiple elaborated claims" without needing to touch verify.py's judge
# prompt (which would mean re-scoring already-collected trials).
_TOKEN_RE = re.compile(
    r'(?:github\.com/[\w.\-]+/[\w.\-]+|(?:www\.)?[\w.\-]+\.[a-z]{2,}(?:/[\w.\-/]*)?)',
    re.IGNORECASE,
)


def _cluster_key(detail: str) -> str:
    m = _TOKEN_RE.search(detail)
    if m:
        return m.group(0).lower().rstrip("/.,")
    return " ".join(detail.lower().split()[:4])


def root_vs_dependent_for_trial(trial_id: str) -> dict | None:
    """Returns {'roots': n, 'dependent': n, 'total': n} for one trial, or
    None if the raw file is missing or has no fabricated_details."""
    path = RAW_DIR / f"{trial_id}.json"
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text())
    except Exception:
        return None
    v = d.get("verification", {})
    details = v.get("fabricated_details")
    if not details:
        return None
    clusters: dict[str, int] = defaultdict(int)
    for detail in details:
        clusters[_cluster_key(detail)] += 1
    n_roots = len(clusters)
    total = sum(clusters.values())
    return {"roots": n_roots, "dependent": total - n_roots, "total": total}


def analyze_root_vs_dependent(rows: list[dict]) -> dict:
    """Per condition/domain, sums up root-fabrication counts vs dependent
    (elaborated) counts across all trials with fabricated_details data."""
    out: dict[str, dict] = {}
    for r in rows:
        key = f"{r['domain']}/{r['condition']}"
        rvd = root_vs_dependent_for_trial(r["trial_id"])
        if rvd is None:
            continue
        cell = out.setdefault(key, {"trials_with_fabrication": 0, "roots": 0,
                                    "dependent": 0, "total": 0})
        cell["trials_with_fabrication"] += 1
        cell["roots"] += rvd["roots"]
        cell["dependent"] += rvd["dependent"]
        cell["total"] += rvd["total"]
    return out


def find_outlier_trials(rows: list[dict]) -> dict:
    """Per condition/domain cell, find the single trial contributing the most
    fabricated claims and flag it if it's above OUTLIER_THRESHOLD of the
    cell's total."""
    by_cell: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        key = f"{r['domain']}/{r['condition']}"
        by_cell[key].append(r)

    out = {}
    for key, cell_rows in by_cell.items():
        total_fab = sum(int(r["fabricated"]) for r in cell_rows)
        if total_fab == 0:
            continue
        worst = max(cell_rows, key=lambda r: int(r["fabricated"]))
        worst_fab = int(worst["fabricated"])
        share = worst_fab / total_fab
        if share >= OUTLIER_THRESHOLD:
            out[key] = {
                "trial_id": worst["trial_id"],
                "model": worst["model"],
                "fabricated": worst_fab,
                "cell_total_fabricated": total_fab,
                "share": share,
            }
    return out


def regenerate_exploratory_report(scored_csv: Path = SCORED_CSV,
                                   out_path: Path = EXPLORATORY_MD) -> None:
    if not scored_csv.exists():
        return
    with open(scored_csv) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return

    rvd = analyze_root_vs_dependent(rows)
    outliers = find_outlier_trials(rows)

    lines = [
        "# Exploratory analyses (auto-generated, do not hand-edit)\n",
        "Not part of the pre-registered primary metric (fabrication rate) --",
        "see EXPERIMENT.md's exploratory-analysis clause. Regenerated every",
        "batch run alongside summary.md.\n",
        "## Root-vs-dependent fabrication clustering\n",
        "Estimates how many DISTINCT invented sources drove each cell's fabricated-claim",
        "count, vs how many counted claims are elaboration on an already-invented root",
        "(e.g. inventing a fake repo, then separately counting \"a quote from it\" and",
        "\"techniques described in it\" as 2 more fabricated claims off the same root).",
        "Heuristic clustering on free-text judge output, not an exact parser.\n",
        "| domain/condition | trials w/ fabrication | distinct roots | dependent claims | total counted |",
        "|---|---|---|---|---|",
    ]
    for key in sorted(rvd):
        c = rvd[key]
        lines.append(f"| {key} | {c['trials_with_fabrication']} | {c['roots']} | "
                     f"{c['dependent']} | {c['total']} |")
    lines.append("\n_Note: \"total counted\" here sums `len(fabricated_details)` per trial, which"
                 " can differ by 1-2 from summary.md's `fabricated` sum -- the judge model"
                 " occasionally reports a `fabricated_claims` int that doesn't exactly match its own"
                 " itemized list length (found: t0066, judge said 6, listed 7). A judge-consistency"
                 " quirk, not a bug in this script -- flagged honestly, not silently reconciled._")

    lines.append("\n## Outlier-trial flags\n")
    lines.append(f"Cells where a single trial contributes >={OUTLIER_THRESHOLD:.0%} "
                 "of that cell's total fabricated-claim count -- the aggregate")
    lines.append("fabrication_rate in summary.md for these cells should be read with")
    lines.append("that in mind, especially at small sample sizes.\n")
    if outliers:
        lines.append("| domain/condition | trial | model | trial fabricated | cell total | share |")
        lines.append("|---|---|---|---|---|---|")
        for key in sorted(outliers):
            o = outliers[key]
            lines.append(f"| {key} | {o['trial_id']} | {o['model']} | {o['fabricated']} | "
                         f"{o['cell_total_fabricated']} | {o['share']:.0%} |")
    else:
        lines.append("(none currently)")

    out_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    regenerate_exploratory_report()
    print(f"Wrote {EXPLORATORY_MD}")
