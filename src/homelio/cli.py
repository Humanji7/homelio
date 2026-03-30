from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

import typer

from homelio.generator import GenerationOptions, generate_documents

app = typer.Typer(no_args_is_help=True, add_completion=False, help="HOMELIO helper CLI.")

PLACEHOLDER_PATTERN = re.compile(r"\[[^\[\]]+\]")


def _iter_docx_files(path: Path) -> list[Path]:
    if path.is_file() and path.suffix.lower() == ".docx":
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*.docx") if item.is_file())
    return []


def extract_placeholders(docx_path: Path) -> list[str]:
    """Return unique placeholders found in a DOCX XML payload."""
    found: set[str] = set()
    with zipfile.ZipFile(docx_path) as archive:
        for name in archive.namelist():
            if not name.startswith("word/") or not name.endswith(".xml"):
                continue
            text = archive.read(name).decode("utf-8", errors="ignore")
            found.update(PLACEHOLDER_PATTERN.findall(text))
    return sorted(found)


@app.callback()
def main_callback() -> None:
    """Utilities for preparing and inspecting the test-assignment workspace."""


@app.command("inspect-placeholders")
def inspect_placeholders(
    paths: list[Path] = typer.Argument(..., exists=True, readable=True),
    as_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Inspect DOCX files or directories and list unique placeholders."""
    results: dict[str, list[str]] = {}
    for path in paths:
        for docx_path in _iter_docx_files(path):
            placeholders = extract_placeholders(docx_path)
            if placeholders:
                results[str(docx_path)] = placeholders

    if not results:
        typer.echo("No DOCX placeholders found.", err=True)
        raise typer.Exit(code=1)

    if as_json:
        typer.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for docx_path, placeholders in results.items():
        typer.echo(docx_path)
        for placeholder in placeholders:
            typer.echo(f"  - {placeholder}")


@app.command("generate")
def generate(
    profile: Path = typer.Option(
        Path("materials/Материалы/04. Пример данных JSON/company_profile_example.json"),
        exists=True,
        readable=True,
        help="Path to profile JSON.",
    ),
    tender: Path = typer.Option(
        Path("materials/Материалы/04. Пример данных JSON/tender_example.json"),
        exists=True,
        readable=True,
        help="Path to tender JSON.",
    ),
    calc: Path = typer.Option(
        Path("materials/Материалы/04. Пример данных JSON/calc_example.json"),
        exists=True,
        readable=True,
        help="Path to calc JSON.",
    ),
    mapping: Path = typer.Option(
        Path("config/mappings/documents.yaml"),
        exists=True,
        readable=True,
        help="Path to mapping config.",
    ),
    output_dir: Path = typer.Option(
        Path("output"),
        help="Directory where generated DOCX files will be written.",
    ),
    document_date: str = typer.Option(
        date.today().isoformat(),
        help="System document date used for generated date fields.",
    ),
    outgoing_number: str = typer.Option(
        "",
        help="Outgoing bid number. Leave empty when the source data does not provide it.",
    ),
    missing_marker: str = typer.Option(
        "",
        help="Replacement for missing values. Empty string keeps fields blank.",
    ),
) -> None:
    """Generate filled DOCX files from JSON sources."""
    generated = generate_documents(
        project_root=Path.cwd(),
        profile_path=profile,
        tender_path=tender,
        calc_path=calc,
        mapping_path=mapping,
        output_dir=output_dir,
        options=GenerationOptions(
            document_date=date.fromisoformat(document_date),
            outgoing_number=outgoing_number,
            missing_marker=missing_marker,
        ),
    )
    for path in generated:
        typer.echo(path)


def main() -> None:
    try:
        app()
    except BrokenPipeError:
        sys.stderr.close()


if __name__ == "__main__":
    main()
