"""Daily cron entrypoint for the C3 follow-up experiment (EXPERIMENT_C3.md).
Structurally identical to run_trial_batch.py but points at entirely separate
files (design_matrix_c3.json, scored_c3.csv, summary_c3.md, raw/c3_*.json) so
it can never collide with or disturb the main 144-trial experiment's
in-progress state."""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib import (
    ROOT, build_prompt, call_openrouter, domain_a_task_text, domain_b_task_text,
    load_domain_a_tasks, load_domain_b_fixtures, openrouter_balance, sleep_backoff,
)
from verify import verify_domain_a, verify_domain_b

BATCH_SIZE = 6
MIN_BALANCE = 5.0
MAX_ATTEMPTS = 3  # bounded auto-retry, same rationale as run_trial_batch.py (2026-08-25)

MATRIX_PATH = ROOT / "experiments" / "design_matrix_c3.json"
SCORED_CSV = ROOT / "experiments" / "results" / "scored_c3.csv"
SUMMARY_MD = ROOT / "experiments" / "results" / "summary_c3.md"
RAW_DIR = ROOT / "experiments" / "raw"  # shared raw/ dir is fine -- trial_ids are prefixed c3_

CSV_FIELDS = [
    "trial_id", "domain", "task_id", "condition", "model", "timestamp",
    "checkable_or_ground_truth", "fabricated", "matched_or_na", "additional_real_or_na", "abstention",
]


def load_matrix():
    return json.loads(MATRIX_PATH.read_text())


def save_matrix(rows):
    MATRIX_PATH.write_text(json.dumps(rows, indent=2))


def append_scored_row(row: dict):
    is_new = not SCORED_CSV.exists()
    with open(SCORED_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)


def regenerate_summary():
    """Reports C3 alongside the already-collected C0/C1/C2 rates from the
    main experiment's scored.csv, per EXPERIMENT_C3.md's analysis plan (C3 vs
    C2 is the direct comparison of interest, C3 vs C0/C1 is context)."""
    main_csv = ROOT / "experiments" / "results" / "scored.csv"
    main_rows = []
    if main_csv.exists():
        with open(main_csv) as f:
            main_rows = list(csv.DictReader(f))

    if not SCORED_CSV.exists():
        return
    with open(SCORED_CSV) as f:
        c3_rows = list(csv.DictReader(f))

    lines = ["# C3 running summary (auto-generated, do not hand-edit)\n",
             "See EXPERIMENT_C3.md for the pre-registered hypothesis and design.\n",
             f"Last updated: {datetime.now(timezone.utc).isoformat()}\n",
             f"C3 trials scored so far: {len(c3_rows)} / 48\n"]

    for domain in ("a", "b"):
        lines.append(f"\n## Domain {domain.upper()}\n")
        lines.append("| condition | trials | checkable/ground_truth | fabricated | fabrication_rate | abstention_rate |")
        lines.append("|---|---|---|---|---|---|")
        for cond, source_rows in (
            ("c0", main_rows), ("c1", main_rows), ("c2", main_rows), ("c3", c3_rows),
        ):
            crows = [r for r in source_rows if r["domain"] == domain and r["condition"] == cond]
            if not crows:
                continue
            total_checkable = sum(int(r["checkable_or_ground_truth"]) for r in crows)
            total_fab = sum(int(r["fabricated"]) for r in crows)
            abst = sum(1 for r in crows if r["abstention"] == "True")
            rate = f"{total_fab/total_checkable:.2%}" if total_checkable else "n/a"
            abst_rate = f"{abst/len(crows):.2%}"
            marker = " (this experiment)" if cond == "c3" else " (main experiment, reference)"
            lines.append(f"| {cond}{marker} | {len(crows)} | {total_checkable} | {total_fab} | {rate} | {abst_rate} |")

    SUMMARY_MD.write_text("\n".join(lines) + "\n")


def main():
    if not MATRIX_PATH.exists():
        print("design_matrix_c3.json missing — run generate_matrix_c3.py first.")
        sys.exit(1)

    # Self-healing safety net, same rationale as run_trial_batch.py (2026-08-25).
    from retry_stuck_errors import retry_stuck_errors
    n_recovered = retry_stuck_errors(MATRIX_PATH)
    if n_recovered:
        print(f"Recovered {n_recovered} stuck error row(s) back to pending.")

    try:
        bal = openrouter_balance()
    except Exception as e:
        print(f"Balance check failed ({e}), proceeding cautiously anyway.")
        bal = None

    if bal is not None and bal < MIN_BALANCE:
        print(f"OpenRouter balance ${bal:.2f} below stopping threshold ${MIN_BALANCE} — pausing, no trials run.")
        sys.exit(0)

    rows = load_matrix()
    pending = [r for r in rows if r["status"] == "pending"]
    if not pending:
        print("All C3 trials complete. Nothing to do.")
        return

    a_tasks = {t["id"]: t for t in load_domain_a_tasks()}
    b_fixtures = load_domain_b_fixtures()

    batch = pending[:BATCH_SIZE]
    print(f"Balance: ${bal:.2f}" if bal is not None else "Balance: unknown")
    print(f"{len(pending)} C3 pending, running {len(batch)} this batch.")

    for row in batch:
        try:
            if row["domain"] == "a":
                task = a_tasks[row["task_id"]]
                task_text = domain_a_task_text(task)
                prompt = build_prompt(task_text, row["condition"])
                resp = call_openrouter(row["model"], prompt, web=True)
                content = resp["content"]
                if not content.strip():
                    raise ValueError("empty response")
                v = verify_domain_a(content)
                scored = {
                    "trial_id": row["trial_id"], "domain": "a", "task_id": row["task_id"],
                    "condition": row["condition"], "model": row["model"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "checkable_or_ground_truth": v["checkable_claims"],
                    "fabricated": v["fabricated_claims"],
                    "matched_or_na": "",
                    "additional_real_or_na": "",
                    "abstention": v["abstention"],
                }
            else:
                fx = b_fixtures[row["task_id"]]
                task_text = domain_b_task_text(fx["code"])
                prompt = build_prompt(task_text, row["condition"])
                resp = call_openrouter(row["model"], prompt, web=False)
                content = resp["content"]
                if not content.strip():
                    raise ValueError("empty response")
                v = verify_domain_b(content, fx["code"], fx["bugs"])
                scored = {
                    "trial_id": row["trial_id"], "domain": "b", "task_id": row["task_id"],
                    "condition": row["condition"], "model": row["model"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "checkable_or_ground_truth": v["total_ground_truth"],
                    "fabricated": v["fabricated_issues"],
                    "matched_or_na": v["bugs_matched"],
                    "additional_real_or_na": v["additional_real_issues"],
                    "abstention": v["abstention"],
                }

            RAW_DIR.mkdir(exist_ok=True)
            (RAW_DIR / f"{row['trial_id']}.json").write_text(json.dumps(
                {"prompt": prompt, "response": content, "verification": v}, indent=2))

            append_scored_row(scored)
            row["status"] = "done"
            print(f"  {row['trial_id']} [{row['domain']}/{row['condition']}/{row['model']}] done — "
                  f"fabricated={scored['fabricated']}/{scored['checkable_or_ground_truth']}")

        except Exception as e:
            attempts = row.get("attempts", 0) + 1
            row["attempts"] = attempts
            history = row.get("error_history", [])
            history.append(str(e)[:300])
            row["error_history"] = history
            if attempts < MAX_ATTEMPTS:
                row["status"] = "pending"
                print(f"  {row['trial_id']} FAILED (attempt {attempts}/{MAX_ATTEMPTS}, will retry): {e}")
            else:
                row["status"] = "failed"
                print(f"  {row['trial_id']} FAILED (attempt {attempts}/{MAX_ATTEMPTS}, giving up): {e}")

        sleep_backoff(0)

    save_matrix(rows)
    regenerate_summary()
    from analyze_exploratory import regenerate_exploratory_report
    regenerate_exploratory_report(
        scored_csv=SCORED_CSV,
        out_path=ROOT / "experiments" / "results" / "exploratory_c3.md",
    )
    remaining = len([r for r in rows if r["status"] == "pending"])
    print(f"C3 batch done. {remaining} trials still pending.")


if __name__ == "__main__":
    main()
