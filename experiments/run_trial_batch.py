"""Daily cron entrypoint. Processes BATCH_SIZE pending trials, verifies, logs, updates the matrix."""
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

MATRIX_PATH = ROOT / "experiments" / "design_matrix.json"
SCORED_CSV = ROOT / "experiments" / "results" / "scored.csv"
SUMMARY_MD = ROOT / "experiments" / "results" / "summary.md"
RAW_DIR = ROOT / "experiments" / "raw"

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
    if not SCORED_CSV.exists():
        return
    with open(SCORED_CSV) as f:
        rows = list(csv.DictReader(f))

    lines = ["# Running summary (auto-generated, do not hand-edit)\n",
             f"Last updated: {datetime.now(timezone.utc).isoformat()}\n",
             f"Trials scored so far: {len(rows)}\n"]

    for domain in ("a", "b"):
        drows = [r for r in rows if r["domain"] == domain]
        if not drows:
            continue
        lines.append(f"\n## Domain {domain.upper()}\n")
        lines.append("| condition | trials | checkable/ground_truth | fabricated | fabrication_rate | abstention_rate |")
        lines.append("|---|---|---|---|---|---|")
        for cond in ("c0", "c1", "c2"):
            crows = [r for r in drows if r["condition"] == cond]
            if not crows:
                continue
            total_checkable = sum(int(r["checkable_or_ground_truth"]) for r in crows)
            total_fab = sum(int(r["fabricated"]) for r in crows)
            abst = sum(1 for r in crows if r["abstention"] == "True")
            rate = f"{total_fab/total_checkable:.2%}" if total_checkable else "n/a"
            abst_rate = f"{abst/len(crows):.2%}"
            lines.append(f"| {cond} | {len(crows)} | {total_checkable} | {total_fab} | {rate} | {abst_rate} |")

    SUMMARY_MD.write_text("\n".join(lines) + "\n")


def main():
    if not MATRIX_PATH.exists():
        print("design_matrix.json missing — run generate_matrix.py first.")
        sys.exit(1)

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
        print("All trials complete. Nothing to do.")
        return

    a_tasks = {t["id"]: t for t in load_domain_a_tasks()}
    b_fixtures = load_domain_b_fixtures()

    batch = pending[:BATCH_SIZE]
    print(f"Balance: ${bal:.2f}" if bal is not None else "Balance: unknown")
    print(f"{len(pending)} pending, running {len(batch)} this batch.")

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
            row["status"] = "error"
            row["error"] = str(e)[:300]
            print(f"  {row['trial_id']} FAILED: {e}")

        sleep_backoff(0)

    save_matrix(rows)
    regenerate_summary()
    remaining = len([r for r in rows if r["status"] == "pending"])
    print(f"Batch done. {remaining} trials still pending.")


if __name__ == "__main__":
    main()
