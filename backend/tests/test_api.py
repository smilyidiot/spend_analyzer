"""API tests using FastAPI's TestClient."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_expenses.csv"
client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_sample_report_matches_schema():
    r = client.get("/api/sample")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["transaction_count"] > 0
    assert len(body["by_category"]) > 0


def test_analyze_uploaded_csv():
    with SAMPLE.open("rb") as fh:
        r = client.post("/api/analyze", files={"file": ("expenses.csv", fh, "text/csv")})
    assert r.status_code == 200
    assert r.json()["potential_recovery"] > 0


def test_analyze_rejects_bad_csv():
    r = client.post("/api/analyze", files={"file": ("bad.csv", b"foo,bar\n1,2\n", "text/csv")})
    assert r.status_code == 422


def test_excel_and_pdf_reports():
    with SAMPLE.open("rb") as fh:
        xlsx = client.post("/api/report?fmt=excel", files={"file": ("e.csv", fh, "text/csv")})
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"  # xlsx is a zip
    with SAMPLE.open("rb") as fh:
        pdf = client.post("/api/report?fmt=pdf", files={"file": ("e.csv", fh, "text/csv")})
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
