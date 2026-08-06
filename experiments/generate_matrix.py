"""Run once to create the 144-row design matrix. Re-running is a no-op if it already exists.

Trial order is shuffled with a fixed seed (42, documented in EXPERIMENT.md) so daily batches
sample across both domains from day one instead of exhausting domain A before ever touching
domain B."""
import json
import random
from pathlib import Path

from lib import MODELS, ROOT, load_domain_a_tasks, load_domain_b_fixtures

OUT = ROOT / "experiments" / "design_matrix.json"

CONDITIONS = ["c0", "c1", "c2"]
SHUFFLE_SEED = 42


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
            for condition in CONDITIONS:
                for model in MODELS:
                    trial_n += 1
                    rows.append({
                        "trial_id": f"t{trial_n:04d}",
                        "domain": domain,
                        "task_id": task_id,
                        "condition": condition,
                        "model": model,
                        "status": "pending",
                    })

    random.Random(SHUFFLE_SEED).shuffle(rows)
    for i, row in enumerate(rows, start=1):
        row["trial_id"] = f"t{i:04d}"

    OUT.write_text(json.dumps(rows, indent=2))
    print(f"Wrote {len(rows)} trials to {OUT} (shuffled, seed={SHUFFLE_SEED})")


if __name__ == "__main__":
    main()
