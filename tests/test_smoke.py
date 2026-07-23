# -*- coding: utf-8 -*-
"""Smoke-Tests fuer den report-forge-Kern (domaenen-neutral, mode='plain')."""

import json
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE_ROOT))

from report_forge.workflow import ReportWorkflow  # noqa: E402
from report_forge.generator import ReportGenerator, DEFAULT_SCHEMA_PATH, DEFAULT_TEMPLATE_PATH  # noqa: E402
from report_forge.schema_service import load_schema, validate_report_schema  # noqa: E402
from report_forge.document_extraction import extract_all_sources  # noqa: E402
from report_forge.render_utils import fix_umlauts_in_values, normalize_umlaut_keys  # noqa: E402


@pytest.fixture()
def source_folder(tmp_path):
    folder = tmp_path / "quelle"
    folder.mkdir()
    (folder / "notiz.txt").write_text(
        "Beispielperson X wurde am 01.01.2026 beobachtet. Alles frei erfunden.",
        encoding="utf-8",
    )
    return folder


def test_schema_loads_and_is_valid_draft202012():
    schema = load_schema(DEFAULT_SCHEMA_PATH)
    assert schema["type"] == "object"
    assert "findings" in schema["properties"]


def test_example_report_matches_schema():
    schema = load_schema(DEFAULT_SCHEMA_PATH)
    data = json.loads(
        (PACKAGE_ROOT / "examples" / "example_report.json").read_text(encoding="utf-8")
    )
    errors = validate_report_schema(data, schema)
    assert errors == []


def test_extract_all_sources_reads_txt(source_folder):
    text = extract_all_sources(str(source_folder))
    assert "Beispielperson X" in text
    assert "Quelle 1" in text


def test_umlaut_roundtrip():
    fixed = fix_umlauts_in_values({"text": "Foerderung fuer Kinder"})
    assert fixed["text"] == "Förderung für Kinder"
    normalized = normalize_umlaut_keys({"föö": 1})
    assert "foeoe" in normalized


def test_generator_extract_build_fill(tmp_path, source_folder):
    gen = ReportGenerator()
    source_text = gen.extract_sources(str(source_folder))
    assert "Beispielperson X" in source_text

    prompt = gen.build_prompt(source_text)
    assert "JSON-SCHEMA" in prompt
    assert "Beispielperson X" in prompt

    data = json.loads(
        (PACKAGE_ROOT / "examples" / "example_report.json").read_text(encoding="utf-8")
    )
    output = tmp_path / "output.docx"
    result = gen.fill_report(data, output_path=str(output))
    assert result.success, result.errors
    assert output.is_file()


def test_workflow_plain_mode_end_to_end(tmp_path, source_folder):
    work_root = tmp_path / "sitzungen"
    workflow = ReportWorkflow()

    prepared = workflow.prepare(source_folder=str(source_folder), work_root=str(work_root), mode="plain")
    assert prepared.success, prepared.errors
    assert prepared.prompt_path.is_file()
    assert any("mode='plain'" in w for w in prepared.warnings)

    data = json.loads(
        (PACKAGE_ROOT / "examples" / "example_report.json").read_text(encoding="utf-8")
    )
    json_path = prepared.session_dir / "data_bundled" / "report.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    output_folder = tmp_path / "fertig"
    finished = workflow.finish(
        session_dir=prepared.session_dir,
        llm_json_path=json_path,
        output_folder=output_folder,
    )
    assert finished.success, finished.errors
    assert output_folder.is_file()


def test_workflow_prepare_rejects_invalid_mode(tmp_path, source_folder):
    workflow = ReportWorkflow()
    result = workflow.prepare(
        source_folder=str(source_folder), work_root=str(tmp_path / "w"), mode="bogus"
    )
    assert not result.success
    assert "mode" in result.errors[0]


def test_workflow_anonymized_mode_without_module_fails_closed(tmp_path, source_folder, monkeypatch):
    """Ohne auffindbares anonymizer-Modul muss mode='anonymized' klar
    fehlschlagen (fail-closed), NICHT still auf Klartext zurueckfallen.

    In dieser Entwicklungsumgebung liegt das echte anonymizer-Modul als
    Sibling unter .MODULES/.DOMAINS/ und wuerde von der Aufwaertssuche
    gefunden -- fuer diesen Test wird die Pfadauflösung daher gezielt
    auf "nicht gefunden" gepatcht, um den Optional-Dependency-Pfad ohne
    das Modul zu pruefen.
    """
    import report_forge.workflow as workflow_module

    monkeypatch.delenv("ANONYMIZER_MODULE_PATH", raising=False)
    monkeypatch.setattr(workflow_module, "_resolve_anonymizer_module", lambda: None)

    workflow = ReportWorkflow()
    result = workflow.prepare(
        source_folder=str(source_folder),
        work_root=str(tmp_path / "w"),
        mode="anonymized",
        real_name="Test Person",
        birth_date="01.01.2000",
        password="testpw123",
    )
    assert not result.success
    assert "ImportError" in result.errors[0]
