"""Unit tests for the Pandas analytics core."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from app import analytics

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_expenses.csv"


@pytest.fixture(scope="module")
def df():
    return analytics.load_transactions(str(SAMPLE))


def test_load_rejects_missing_columns():
    bad = io.StringIO("foo,bar\n1,2\n")
    with pytest.raises(analytics.DataValidationError):
        analytics.load_transactions(bad)


def test_load_drops_invalid_rows():
    csv = "date,amount,category,vendor\n2026-01-01,100,Travel,Uber\nnotadate,50,X,Y\n2026-01-02,-5,Z,W\n"
    df = analytics.load_transactions(io.StringIO(csv))
    assert len(df) == 1  # bad date and negative amount dropped
    assert df.iloc[0]["vendor"] == "Uber"


def test_summary_fields(df):
    s = analytics.summary(df)
    assert s["transaction_count"] == len(df)
    assert s["total_spend"] > 0
    assert s["start_date"] <= s["end_date"]


def test_category_shares_sum_to_100(df):
    cats = analytics.by_category(df)
    assert abs(cats["share_pct"].sum() - 100.0) < 0.5
    assert cats["total"].is_monotonic_decreasing


def test_duplicates_detect_injected_payments(df):
    dups = analytics.duplicate_payments(df)
    pairs = {(r.vendor, r.amount) for r in dups.itertuples()}
    assert ("AWS", 18500.00) in pairs
    assert ("KPMG", 9900.00) in pairs
    assert dups["recoverable"].sum() >= 18500.00 + 9900.00


def test_outliers_flag_large_transactions(df):
    outs = analytics.outliers(df)
    assert (outs["amount"] >= 142000.0).any()


def test_build_report_shape(df):
    report = analytics.build_report(df)
    assert set(report) >= {
        "summary", "by_category", "by_vendor", "by_month",
        "outliers", "duplicate_suspects", "potential_recovery", "insights",
    }
    assert report["potential_recovery"] > 0
    assert isinstance(report["insights"], list) and report["insights"]
