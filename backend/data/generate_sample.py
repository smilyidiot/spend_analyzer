"""Generate a deterministic sample expenses CSV (stdlib only).

Run:  python backend/data/generate_sample.py
Produces ``sample_expenses.csv`` next to this script, including a couple of
deliberate duplicate payments and large outliers so the analytics have
something to surface.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

RNG = random.Random(42)

CATEGORIES = {
    "Travel": ["IndiGo", "Uber", "MakeMyTrip", "OYO Rooms"],
    "Software": ["AWS", "Atlassian", "GitHub", "Figma", "Slack"],
    "Office Supplies": ["Amazon Business", "Staples", "Croma"],
    "Events": ["Zomato Catering", "BookMyShow", "Taj Hotels"],
    "Consulting": ["Deloitte", "KPMG", "Accenture"],
    "Marketing": ["Google Ads", "LinkedIn", "Meta Ads"],
}
DEPARTMENTS = ["Engineering", "Sales", "Operations", "Marketing", "Finance"]


def main() -> None:
    rows = []
    start = date(2026, 4, 1)
    for day in range(183):  # ~6 months
        current = start + timedelta(days=day)
        for _ in range(RNG.randint(0, 4)):
            category = RNG.choice(list(CATEGORIES))
            vendor = RNG.choice(CATEGORIES[category])
            amount = round(RNG.uniform(500, 25000), 2)
            rows.append([current.isoformat(), amount, category, vendor, RNG.choice(DEPARTMENTS)])

    # Inject duplicate payments (same vendor + amount a day apart).
    dup_day = date(2026, 6, 10)
    rows.append([dup_day.isoformat(), 18500.00, "Software", "AWS", "Engineering"])
    rows.append([(dup_day + timedelta(days=1)).isoformat(), 18500.00, "Software", "AWS", "Engineering"])
    rows.append([date(2026, 7, 3).isoformat(), 9900.00, "Consulting", "KPMG", "Finance"])
    rows.append([date(2026, 7, 5).isoformat(), 9900.00, "Consulting", "KPMG", "Finance"])

    # Inject a couple of large outliers.
    rows.append([date(2026, 5, 20).isoformat(), 185000.00, "Consulting", "Deloitte", "Operations"])
    rows.append([date(2026, 8, 14).isoformat(), 142000.00, "Events", "Taj Hotels", "Sales"])

    rows.sort(key=lambda r: r[0])

    out = Path(__file__).resolve().parent / "sample_expenses.csv"
    with out.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "amount", "category", "vendor", "department"])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
