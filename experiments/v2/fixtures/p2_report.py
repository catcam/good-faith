import csv
from collections import defaultdict
from datetime import date


def load_sales(path: str) -> list:
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append({
                "day": date.fromisoformat(row["day"]),
                "region": row["region"].strip(),
                "amount": float(row["amount"]),
            })
    return rows


def totals_by_region(rows: list) -> dict:
    totals = defaultdict(float)
    for r in rows:
        totals[r["region"]] += r["amount"]
    return dict(totals)


def average_per_day(rows: list) -> float:
    days = {r["day"] for r in rows}
    return sum(r["amount"] for r in rows) / len(days)


def top_regions(rows: list, n: int = 3) -> list:
    totals = totals_by_region(rows)
    return sorted(totals.items(), key=lambda kv: kv[1])[:n]


def in_range(rows: list, start: date, end: date) -> list:
    """Rows with start <= day <= end."""
    return [r for r in rows if start <= r["day"] <= end]


def write_summary(rows: list, path: str) -> None:
    totals = totals_by_region(rows)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["region", "total"])
        for region in sorted(totals):
            w.writerow([region, f"{totals[region]:.2f}"])
