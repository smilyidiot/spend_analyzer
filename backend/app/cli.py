"""Command-line interface for the spend analyzer.

Examples
--------
    python -m app.cli analyze data/sample_expenses.csv
    python -m app.cli analyze data/sample_expenses.csv --excel report.xlsx --pdf report.pdf
    python -m app.cli sample
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from . import analytics, exporters

cli = typer.Typer(add_completion=False, help="Spend Analyzer command-line tools.")

_SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_expenses.csv"


def _run(csv_path: Path, excel: Path | None, pdf: Path | None, as_json: bool) -> None:
    try:
        df = analytics.load_transactions(str(csv_path))
    except analytics.DataValidationError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    report = analytics.build_report(df)

    if as_json:
        typer.echo(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        typer.secho("\nSpend Analyzer", fg=typer.colors.CYAN, bold=True)
        typer.echo(f"  Period        : {s['start_date']} to {s['end_date']}")
        typer.echo(f"  Total spend   : {s['currency']} {s['total_spend']:,.2f}")
        typer.echo(f"  Transactions  : {s['transaction_count']}")
        typer.echo(f"  Recoverable   : {s['currency']} {report['potential_recovery']:,.2f}")
        typer.secho("\n  Top categories:", bold=True)
        for row in report["by_category"][:5]:
            typer.echo(f"    {row['category']:<18} {s['currency']} {row['total']:>12,.0f}  ({row['share_pct']:>4.0f}%)")
        if report["insights"]:
            typer.secho("\n  Insights:", bold=True)
            for note in report["insights"]:
                typer.echo(f"    • {note}")

    if excel:
        excel.write_bytes(exporters.to_excel(report))
        typer.secho(f"Wrote Excel report -> {excel}", fg=typer.colors.GREEN)
    if pdf:
        pdf.write_bytes(exporters.to_pdf(report))
        typer.secho(f"Wrote PDF report   -> {pdf}", fg=typer.colors.GREEN)


@cli.command()
def analyze(
    csv_path: Path = typer.Argument(..., exists=True, readable=True, help="Transactions CSV."),
    excel: Path = typer.Option(None, "--excel", help="Write an Excel report to this path."),
    pdf: Path = typer.Option(None, "--pdf", help="Write a PDF report to this path."),
    as_json: bool = typer.Option(False, "--json", help="Print the full report as JSON."),
) -> None:
    """Analyse a transactions CSV and optionally export Excel/PDF reports."""
    _run(csv_path, excel, pdf, as_json)


@cli.command()
def sample(
    excel: Path = typer.Option(None, "--excel"),
    pdf: Path = typer.Option(None, "--pdf"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Run the analysis on the bundled sample dataset."""
    _run(_SAMPLE, excel, pdf, as_json)


if __name__ == "__main__":
    cli()
