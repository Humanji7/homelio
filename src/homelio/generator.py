from __future__ import annotations

import copy
import json
import zipfile
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSMAP = {"w": W_NS}

MONTHS_RU = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


@dataclass
class GenerationOptions:
    document_date: date
    outgoing_number: str = ""
    missing_marker: str = ""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_mapping_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def get_by_path(data: Any, path: str | None) -> Any:
    if path in (None, ""):
        return data

    current = data
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def format_money(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return str(value)
    formatted = f"{number:,.2f}"
    return formatted.replace(",", " ").replace(".", ",")


def format_date_text(value: date) -> str:
    return f"«{value.day:02d}» {MONTHS_RU[value.month]} {value.year} года"


def format_value(value: Any, formatter: str | None, missing_marker: str) -> str:
    if value is None:
        return missing_marker
    if formatter == "money":
        return format_money(value)
    return str(value)


def build_context(
    profile: dict[str, Any],
    tender: dict[str, Any],
    calc: dict[str, Any],
    options: GenerationOptions,
) -> dict[str, Any]:
    return {
        "profile": profile,
        "tender": tender,
        "calc": calc,
        "system": {
            "current_date_text": format_date_text(options.document_date),
            "outgoing_number": options.outgoing_number,
        },
        "derived": {
            "price_rows": build_price_rows(tender=tender, calc=calc),
        },
    }


def build_price_rows(tender: dict[str, Any], calc: dict[str, Any]) -> list[dict[str, Any]]:
    tender_items = {item["line_no"]: item for item in tender.get("items", [])}
    calc_items = {item["line_no"]: item for item in calc.get("items", [])}
    line_nos = sorted(set(tender_items) | set(calc_items))
    rows: list[dict[str, Any]] = []
    for line_no in line_nos:
        row: dict[str, Any] = {"line_no": line_no}
        row.update(tender_items.get(line_no, {}))
        row.update(calc_items.get(line_no, {}))
        rows.append(row)
    return rows


def resolve_mapping_value(
    context: dict[str, Any],
    mapping: dict[str, Any],
    *,
    missing_marker: str,
) -> str:
    source_root = mapping.get("source_root")
    source_path = mapping.get("source_path")
    formatter = mapping.get("formatter")
    value = get_by_path(context.get(source_root), source_path)
    return format_value(value, formatter, missing_marker)


def replace_text_tokens(node: etree._Element, replacements: dict[str, str]) -> None:
    for text_node in node.xpath(".//w:t", namespaces=NSMAP):
        current = text_node.text
        if not current:
            continue
        for token, value in replacements.items():
            if token in current:
                current = current.replace(token, value)
        text_node.text = current


def find_rows_with_marker(root: etree._Element, marker_token: str) -> list[etree._Element]:
    rows: list[etree._Element] = []
    for row in root.xpath(".//w:tr", namespaces=NSMAP):
        texts = "".join(row.xpath(".//w:t/text()", namespaces=NSMAP))
        if marker_token in texts:
            rows.append(row)
    return rows


def set_row_number(row: etree._Element, value: Any) -> None:
    first_cell = row.xpath("./w:tc[1]//w:t", namespaces=NSMAP)
    if first_cell:
        first_cell[0].text = "" if value is None else str(value)


def render_repeating_rows(
    root: etree._Element,
    repeating_blocks: list[dict[str, Any]],
    context: dict[str, Any],
    *,
    missing_marker: str,
) -> None:
    for block in repeating_blocks:
        marker_token = block["marker_token"]
        rows = find_rows_with_marker(root, marker_token)
        if not rows:
            continue

        parent = rows[0].getparent()
        insert_at = parent.index(rows[0])
        template_row = copy.deepcopy(rows[0])
        for row in rows:
            parent.remove(row)

        collection_root = context.get(block["collection_root"])
        items = get_by_path(collection_root, block.get("collection_path")) or []
        if not items:
            items = [{}]

        for offset, item in enumerate(items):
            rendered_row = copy.deepcopy(template_row)
            row_number_path = get_by_path(block.get("row_number"), "source_path")
            if row_number_path:
                set_row_number(rendered_row, get_by_path(item, row_number_path))

            replacements = {
                token: format_value(
                    get_by_path(item, token_mapping.get("source_path")),
                    token_mapping.get("formatter"),
                    missing_marker,
                )
                for token, token_mapping in block.get("tokens", {}).items()
            }
            replace_text_tokens(rendered_row, replacements)
            parent.insert(insert_at + offset, rendered_row)


def render_docx(
    template_path: Path,
    output_path: Path,
    document_mapping: dict[str, Any],
    context: dict[str, Any],
    *,
    missing_marker: str,
) -> None:
    with zipfile.ZipFile(template_path, "r") as source_zip:
        document_xml = source_zip.read("word/document.xml")
        root = etree.fromstring(document_xml)

        render_repeating_rows(
            root,
            document_mapping.get("repeating_rows", []),
            context,
            missing_marker=missing_marker,
        )

        replacements = {
            token: resolve_mapping_value(context, mapping, missing_marker=missing_marker)
            for token, mapping in document_mapping.get("placeholders", {}).items()
        }
        replace_text_tokens(root, replacements)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w") as target_zip:
            for item in source_zip.infolist():
                content = source_zip.read(item.filename)
                if item.filename == "word/document.xml":
                    content = etree.tostring(
                        root,
                        encoding="UTF-8",
                        xml_declaration=True,
                        standalone="yes",
                    )
                target_zip.writestr(item, content)


def generate_documents(
    *,
    project_root: Path,
    profile_path: Path,
    tender_path: Path,
    calc_path: Path,
    mapping_path: Path,
    output_dir: Path,
    options: GenerationOptions,
) -> list[Path]:
    profile = load_json(profile_path)
    tender = load_json(tender_path)
    calc = load_json(calc_path)
    config = load_mapping_config(mapping_path)
    context = build_context(profile=profile, tender=tender, calc=calc, options=options)

    generated: list[Path] = []
    for document_mapping in config.get("documents", []):
        template_path = project_root / document_mapping["template_file"]
        output_path = output_dir / document_mapping["output_file"]
        render_docx(
            template_path=template_path,
            output_path=output_path,
            document_mapping=document_mapping,
            context=context,
            missing_marker=options.missing_marker,
        )
        generated.append(output_path)
    return generated

