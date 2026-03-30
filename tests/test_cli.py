import json
import re
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from homelio.cli import app, extract_placeholders


def test_extract_placeholders_from_sample_template() -> None:
    template = Path(
        "materials/Материалы/02. Шаблоны/01_Анкета_участника_шаблон.docx"
    )

    placeholders = extract_placeholders(template)

    assert "[Полное наименование участника]" in placeholders
    assert "[ИНН]" in placeholders


def test_inspect_placeholders_cli_outputs_sample_placeholders() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["inspect-placeholders", "materials/Материалы/02. Шаблоны"])

    assert result.exit_code == 0
    assert "01_Анкета_участника_шаблон.docx" in result.stdout
    assert "[ИНН]" in result.stdout


def read_document_xml_text(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as archive:
        return archive.read("word/document.xml").decode("utf-8", errors="ignore")


def test_generate_creates_all_documents(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "generate",
            "--output-dir",
            str(tmp_path),
            "--document-date",
            "2026-03-26",
            "--outgoing-number",
            "№2603/1",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "01_Анкета_участника_заполнено.docx").exists()
    assert (tmp_path / "02_Заявка_на_участие_в_закупке_заполнено.docx").exists()
    assert (tmp_path / "03_Предложение_о_цене_договора_заполнено.docx").exists()


def test_generate_replaces_core_values_in_output(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "generate",
            "--output-dir",
            str(tmp_path),
            "--document-date",
            "2026-03-26",
            "--outgoing-number",
            "№2603/1",
        ],
    )

    assert result.exit_code == 0

    bid_application = read_document_xml_text(
        tmp_path / "02_Заявка_на_участие_в_закупке_заполнено.docx"
    )
    price_offer = read_document_xml_text(
        tmp_path / "03_Предложение_о_цене_договора_заполнено.docx"
    )

    assert "«26» марта 2026 года" in bid_application
    assert "№2603/1" in bid_application
    assert "Поставка кабельной продукции для производственной площадки «Север-1»" in bid_application
    assert "Кабель контрольный КВВГнг(А)-LS 10х1,5" in price_offer
    assert "432 600,00" in price_offer
    assert "[Наименование продукции]" not in price_offer


def test_generate_removes_all_placeholders_from_all_output_documents(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "generate",
            "--output-dir",
            str(tmp_path),
            "--document-date",
            "2026-03-26",
            "--outgoing-number",
            "№2603/1",
        ],
    )

    assert result.exit_code == 0

    for docx_name in [
        "01_Анкета_участника_заполнено.docx",
        "02_Заявка_на_участие_в_закупке_заполнено.docx",
        "03_Предложение_о_цене_договора_заполнено.docx",
    ]:
        document_xml = read_document_xml_text(tmp_path / docx_name)
        assert re.findall(r"\[[^\[\]]+\]", document_xml) == []


def test_generate_uses_missing_marker_for_missing_profile_value(tmp_path: Path) -> None:
    runner = CliRunner()
    source_profile = Path("materials/Материалы/04. Пример данных JSON/company_profile_example.json")
    profile_data = json.loads(source_profile.read_text(encoding="utf-8"))
    del profile_data["contact"]["email"]

    profile_override = tmp_path / "company_profile_missing_email.json"
    profile_override.write_text(json.dumps(profile_data, ensure_ascii=False), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "generate",
            "--profile",
            str(profile_override),
            "--output-dir",
            str(tmp_path),
            "--document-date",
            "2026-03-26",
            "--missing-marker",
            "<MISSING>",
        ],
    )

    assert result.exit_code == 0

    questionnaire_xml = read_document_xml_text(tmp_path / "01_Анкета_участника_заполнено.docx")

    assert "&lt;MISSING&gt;" in questionnaire_xml
    assert "[E-mail]" not in questionnaire_xml
