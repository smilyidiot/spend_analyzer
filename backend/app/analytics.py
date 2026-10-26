"""Core spend-analytics computations built on Pandas / NumPy.

Every public function takes a cleaned :class:`pandas.DataFrame` (see
:func:`load_transactions`) and returns plain Python / Pandas objects so the
same logic can be reused from the API, the CLI and the test-suite.

Expected columns: ``date`` (datetime), ``amount`` (float), ``category`` (str),
``vendor`` (str) and an optional ``department`` (str).
"""

from __future__ import annotations

from datetime import timedelta
from io import StringIO
from typing import IO

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("date", "amount", "category", "vendor")


class DataValidationError(ValueError):
    """Raised when an input file is missing columns or has no usable rows."""


def load_transactions(source: str | IO[str] | bytes) -> pd.DataFrame:
    """Load and clean a transactions CSV from a path, file-like object or bytes.

    Coerces ``date`` to datetime and ``amount`` to numeric, drops rows that
    fail to parse, trims whitespace on text columns and validates the schema.
    """
    if isinstance(source, bytes):
        source = StringIO(source.decode("utf-8"))

    df = pd.read_csv(source)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected at least: {', '.join(REQUIRED_COLUMNS)}."
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    for col in ("category", "vendor", "department"):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    df = df.dropna(subset=["date", "amount", "category", "vendor"])
    df = df[df["amount"] > 0].reset_index(drop=True)

    if df.empty:
        raise DataValidationError("No valid transactions found after cleaning.")
    return df


def summary(df: pd.DataFrame, currency: str = "INR") -> dict:
    """High-level totals across the whole dataset."""
    return {
        "total_spend": round(float(df["amount"].sum()), 2),
        "transaction_count": int(len(df)),
        "average_transaction": round(float(df["amount"].mean()), 2),
        "median_transaction": round(float(df["amount"].median()), 2),
        "distinct_vendors": int(df["vendor"].nunique()),
        "distinct_categories": int(df["category"].nunique()),
        "start_date": df["date"].min().date().isoformat(),
        "end_date": df["date"].max().date().isoformat(),
        "currency": currency,
    }


def by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Spend aggregated by category, descending, with share of total."""
    total = df["amount"].sum()
    out = (
        df.groupby("category", observed=True)["amount"]
        .agg(total="sum", count="count")
        .sort_values("total", ascending=False)
        .reset_index()
    )
    out["share_pct"] = (out["total"] / total * 100).round(2)
    out["total"] = out["total"].round(2)
    return out


def by_vendor(df: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Top ``top`` vendors by spend."""
    out = (
        df.groupby("vendor", observed=True)["amount"]
        .agg(total="sum", count="count")
        .sort_values("total", ascending=False)
        .head(top)
        .reset_index()
    )
    out["total"] = out["total"].round(2)
    return out


def by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly spend with month-over-month percentage change."""
    monthly = (
        df.set_index("date")
        .resample("MS")["amount"]
        .sum()
        .rename("total")
        .reset_index()
    )
    monthly["month"] = monthly["date"].dt.strftime("%Y-%m")
    monthly["mom_change_pct"] = (monthly["total"].pct_change() * 100).round(2)
    monthly["total"] = monthly["total"].round(2)
    return monthly[["month", "total", "mom_change_pct"]]


def outliers(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """Flag unusually large transactions using the IQR rule (``Q3 + k*IQR``)."""
    q1, q3 = df["amount"].quantile([0.25, 0.75])
    threshold = q3 + k * (q3 - q1)
    flagged = df[df["amount"] > threshold].copy()
    flagged = flagged.sort_values("amount", ascending=False)
    flagged["threshold"] = round(float(threshold), 2)
    return flagged


def duplicate_payments(df: pd.DataFrame, window_days: int = 5) -> pd.DataFrame:
    """Detect likely duplicate payments: same vendor and amount within a window.

    Returns one row per suspected duplicate group with the recoverable amount
    (every charge after the first in the group).
    """
    groups = []
    for (vendor, amount), grp in df.groupby(["vendor", "amount"], observed=True):
        if len(grp) < 2:
            continue
        dates = grp["date"].sort_values().reset_index(drop=True)
        # Only treat as duplicates if any two charges fall within the window.
        if (dates.diff().dropna() <= timedelta(days=window_days)).any():
            groups.append(
                {
                    "vendor": vendor,
                    "amount": round(float(amount), 2),
                    "occurrences": int(len(grp)),
                    "dates": [d.date().isoformat() for d in dates],
                    "recoverable": round(float(amount) * (len(grp) - 1), 2),
                }
            )
    cols = ["vendor", "amount", "occurrences", "dates", "recoverable"]
    result = pd.DataFrame(groups, columns=cols)
    if not result.empty:
        result = result.sort_values("recoverable", ascending=False).reset_index(drop=True)
    return result


def _insights(summ: dict, cats: pd.DataFrame, months: pd.DataFrame, dups: pd.DataFrame) -> list[str]:
    """Short, human-readable takeaways derived from the aggregates."""
    notes: list[str] = []
    if not cats.empty:
        top = cats.iloc[0]
        notes.append(
            f"{top['category']} is the largest category at "
            f"{summ['currency']} {top['total']:,.0f} ({top['share_pct']:.0f}% of spend)."
        )
    changes = months.dropna(subset=["mom_change_pct"])
    if not changes.empty:
        last = changes.iloc[-1]
        direction = "up" if last["mom_change_pct"] >= 0 else "down"
        notes.append(
            f"Spend in {last['month']} was {direction} "
            f"{abs(last['mom_change_pct']):.0f}% month over month."
        )
    if not dups.empty:
        notes.append(
            f"{len(dups)} suspected duplicate payment group(s) worth "
            f"{summ['currency']} {dups['recoverable'].sum():,.0f} in potential recovery."
        )
    return notes


def build_report(df: pd.DataFrame, top_vendors: int = 10, currency: str = "INR") -> dict:
    """Assemble the full analytics report as a JSON-serialisable dict."""
    summ = summary(df, currency=currency)
    cats = by_category(df)
    vendors = by_vendor(df, top=top_vendors)
    months = by_month(df)
    outs = outliers(df)
    dups = duplicate_payments(df)

    return {
        "summary": summ,
        "by_category": cats.to_dict(orient="records"),
        "by_vendor": vendors.to_dict(orient="records"),
        "by_month": months.where(pd.notnull(months), None).to_dict(orient="records"),
        "outliers": [
            {
                "date": row["date"].date().isoformat(),
                "vendor": row["vendor"],
                "category": row["category"],
                "amount": round(float(row["amount"]), 2),
            }
            for _, row in outs.iterrows()
        ],
        "duplicate_suspects": dups.to_dict(orient="records"),
        "potential_recovery": round(float(dups["recoverable"].sum()) if not dups.empty else 0.0, 2),
        "insights": _insights(summ, cats, months, dups),
    }
