"""One-time migration: reset status="error" rows back to "pending" so the next
batch run picks them up again, WITHOUT losing the original error message.

Context (2026-08-25): found the judge model (llama-3.3-70b-versatile) had been
retired from Groq's lineup, causing every judge call to 404. Both
run_trial_batch.py and run_trial_batch_c3.py only ever process status=="pending"
rows -- once a row hit an exception it was marked "error" and never touched
again, so 48/144 main-experiment rows and 6/48 C3 rows were silently stranded,
permanently, with no retry. Fixed the root cause in lib.py's call_groq_judge()
(swapped to openai/gpt-oss-120b). This script is the one-time cleanup for rows
that got stuck BEFORE that fix landed.

Does NOT delete the original error message -- moves it into an "error_history"
list (appending, so if a row fails again post-reset for a DIFFERENT reason,
the full history survives) and adds an "attempts" counter so the ongoing
auto-retry logic in run_trial_batch*.py (added alongside this script) can cap
future retries instead of looping forever on a row that's broken for some
other, not-yet-fixed reason.

Usage: python3 retry_stuck_errors.py [--dry-run]
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRICES = [
    ROOT / "experiments" / "design_matrix.json",
    ROOT / "experiments" / "design_matrix_c3.json",
]


def retry_stuck_errors(matrix_path: Path, dry_run: bool = False) -> int:
    if not matrix_path.exists():
        return 0
    rows = json.loads(matrix_path.read_text())
    n_reset = 0
    for row in rows:
        if row.get("status") != "error":
            continue
        history = row.get("error_history", [])
        old_error = row.pop("error", None)
        if old_error:
            history.append(old_error)
        row["error_history"] = history
        row["attempts"] = row.get("attempts", 0)  # preserve if already present (shouldn't be, pre-migration)
        row["status"] = "pending"
        n_reset += 1

    if n_reset and not dry_run:
        matrix_path.write_text(json.dumps(rows, indent=2))
    return n_reset


def main():
    dry_run = "--dry-run" in sys.argv
    total = 0
    for path in MATRICES:
        n = retry_stuck_errors(path, dry_run=dry_run)
        total += n
        label = "would reset" if dry_run else "reset"
        print(f"{path.name}: {label} {n} stuck error row(s) to pending")
    print(f"Total: {total}" + (" (dry run, nothing written)" if dry_run else ""))


if __name__ == "__main__":
    main()
