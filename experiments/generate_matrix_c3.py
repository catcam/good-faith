"""Run once to create the 48-row C3 design matrix (EXPERIMENT_C3.md). Re-running
is a no-op if it already exists. Separate from generate_matrix.py's 144-row
matrix -- does not touch or resize that file. Same shuffle-seed convention
(documented in EXPERIMENT_C3.md) so daily batches sample across both domains
from day one."""
import json
import random
from pathlib import Path

from lib import MODELS, ROOT, load_domain_a_tasks, load_domain_b_fixtures

OUT = ROOT / "experiments" / "design_matrix_c3.json"

SHUFFLE_SEED = 43  # different from the main experiment's 42, documented in EXPERIMENT_C3.md


def main():
    if OUT.exists():
        print(f"{OUT} already exists, not overwriting. Delete it first if you really want to regenerate.")
        return

    rows = []
    a_tasks = load_domain_a_tasks()
    b_fixtures = load_domain_b_fixtures()

    trial_n = 0
    for domain, task_ids in (("a", [t["id"] for t in a_tasks]), ("b", list(b_fixtures.keys()))):
        for task_id in task_ids:
            for model in MODELS:
                trial_n += 1
                rows.append({
                    "trial_id": f"c3_t{trial_n:04d}",
                    "domain": domain,
                    "task_id": task_id,
                    "condition": "c3",
                    "model": model,
                    "status": "pending",
                })

    random.Random(SHUFFLE_SEED).shuffle(rows)
    for i, row in enumerate(rows, start=1):
        row["trial_id"] = f"c3_t{i:04d}"

    OUT.write_text(json.dumps(rows, indent=2))
    print(f"Wrote {len(rows)} trials to {OUT} (shuffled, seed={SHUFFLE_SEED})")


if __name__ == "__main__":
    main()
