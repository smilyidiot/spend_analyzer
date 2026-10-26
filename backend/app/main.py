"""FastAPI service exposing the spend-analytics engine.

Endpoints
---------
``GET  /api/health``   — liveness probe.
``GET  /api/sample``   — analytics for the bundled sample dataset.
``POST /api/analyze``  — analytics for an uploaded CSV.
``POST /api/report``   — download an Excel or PDF report for an uploaded CSV.
"""

from __future__ import annotations

import io
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import __version__, analytics, exporters
from .models import Report

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "data" / "sample_expenses.csv"

app = FastAPI(
    title="Spend Analyzer API",
    version=__version__,
    description="Pandas-powered spend analytics with Excel/PDF report export.",
)

# The React dev server and static hosting call this API from another origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _report_from_bytes(raw: bytes) -> dict:
    try:
        df = analytics.load_transactions(raw)
    except analytics.DataValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return analytics.build_report(df)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/sample", response_model=Report)
def sample() -> dict:
    """Run the analytics on the bundled sample dataset (handy for demos)."""
    df = analytics.load_transactions(str(SAMPLE_CSV))
    return analytics.build_report(df)


@app.post("/api/analyze", response_model=Report)
async def analyze(file: UploadFile = File(...)) -> dict:
    """Analyse an uploaded transactions CSV and return the full report."""
    return _report_from_bytes(await file.read())


@app.post("/api/report")
async def report(
    file: UploadFile = File(...),
    fmt: str = Query("excel", pattern="^(excel|pdf)$"),
) -> StreamingResponse:
    """Return a downloadable Excel (``fmt=excel``) or PDF (``fmt=pdf``) report."""
    data = analytics.build_report(_df_guard(await file.read()))
    if fmt == "excel":
        buffer = exporters.to_excel(data)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "spend_report.xlsx"
    else:
        buffer = exporters.to_pdf(data)
        media = "application/pdf"
        filename = "spend_report.pdf"
    return StreamingResponse(
        io.BytesIO(buffer),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _df_guard(raw: bytes):
    try:
        return analytics.load_transactions(raw)
    except analytics.DataValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
