# -*- coding: utf-8 -*-
"""Tests fuer output_dir/inbox_dir-Config, Publish-Schritt und process-inbox."""

import json
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE_ROOT))

from report_forge.config import load_config, resolve_setting  # noqa: E402
from report_forge.workflow import ReportWorkflow, publish_copy  # noqa: E402
from report_forge.inbox import process_inbox, IDENTITY_FILENAME, MARKER_FILENAME  # noqa: E402


# ---------------------------------------------------------------------
# Config-Auflösung
# ---------------------------------------------------------------------


def _write_config(tmp_path, config_json, local_json=None):
    (tmp_path / "config.json").write_text(json.dumps(config_json), encoding="utf-8")
    if local_json is not None:
        (tmp_path / "config.local.json").write_text(json.dumps(local_json), encoding="utf-8")


def test_resolve_setting_cli_wins(tmp_path):
    _write_config(tmp_path, {"defaults": {"output_dir": "from-config"}})
    assert resolve_setting("output_dir", cli_value="from-cli", package_root=tmp_path) == "from-cli"


def test_resolve_setting_local_overrides_config(tmp_path):
    _write_config(
        tmp_path,
        {"defaults": {"output_dir": "from-config"}},
        local_json={"defaults": {"output_dir": "from-local"}},
    )
    assert resolve_setting("output_dir", package_root=tmp_path) == "from-local"


def test_resolve_setting_falls_back_to_config_json(tmp_path):
    _write_config(tmp_path, {"defaults": {"output_dir": "from-config"}})
    assert resolve_setting("output_dir", package_root=tmp_path) == "from-config"


def test_resolve_setting_unset_returns_none(tmp_path):
    _write_config(tmp_path, {"defaults": {}})
    assert resolve_setting("output_dir", package_root=tmp_path) is None


def test_load_config_merges_local_over_base(tmp_path):
    _write_config(
        tmp_path,
        {"defaults": {"a": 1, "b": 2}},
        local_json={"defaults": {"b": 99}},
    )
    cfg = load_config(tmp_path)
    assert cfg["defaults"] == {"a": 1, "b": 99}


# ---------------------------------------------------------------------
# Publish-Kopie
# ---------------------------------------------------------------------


def test_publish_copy_from_file(tmp_path):
    src = tmp_path / "session-output.docx"
    src.write_bytes(b"fake docx content")
    dest_dir = tmp_path / "output"

    published = publish_copy(src, dest_dir)
    assert published.parent == dest_dir
    assert published.name == "session-output.docx"
    assert published.read_bytes() == b"fake docx content"
    assert src.exists()  # Original bleibt bestehen


def test_publish_copy_from_directory_finds_report_docx(tmp_path):
    src_dir = tmp_path / "session-folder"
    src_dir.mkdir()
    (src_dir / "report.docx").write_bytes(b"anonymized-mode output")
    dest_dir = tmp_path / "output"

    published = publish_copy(src_dir, dest_dir)
    assert published.name == "report.docx"
    assert published.read_bytes() == b"anonymized-mode output"


def test_publish_copy_collision_gets_timestamp_suffix(tmp_path):
    src = tmp_path / "bericht.docx"
    src.write_bytes(b"v1")
    dest_dir = tmp_path / "output"
    dest_dir.mkdir()
    (dest_dir / "bericht.docx").write_bytes(b"already there")

    published = publish_copy(src, dest_dir)
    assert published.name != "bericht.docx"
    assert published.stem.startswith("bericht_")
    assert published.suffix == ".docx"
    assert published.read_bytes() == b"v1"
    assert (dest_dir / "bericht.docx").read_bytes() == b"already there"  # unangetastet


def test_publish_copy_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        publish_copy(tmp_path / "does-not-exist", tmp_path / "out")


def test_finish_plain_mode_with_output_dir_publishes(tmp_path):
    source = tmp_path / "quelle"
    source.mkdir()
    (source / "notiz.txt").write_text("Testinhalt, synthetisch.", encoding="utf-8")

    workflow = ReportWorkflow()
    prepared = workflow.prepare(source_folder=str(source), work_root=str(tmp_path / "sitzungen"), mode="plain")
    assert prepared.success, prepared.errors

    data = json.loads((PACKAGE_ROOT / "examples" / "example_report.json").read_text(encoding="utf-8"))
    json_path = prepared.session_dir / "data_bundled" / "report.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "publish-ziel"
    finished = workflow.finish(
        session_dir=prepared.session_dir,
        llm_json_path=json_path,
        output_folder=tmp_path / "fertig" / "bericht.docx",
        output_dir=output_dir,
    )
    assert finished.success, finished.errors
    assert finished.published_path is not None
    assert finished.published_path.parent == output_dir
    assert finished.published_path.is_file()
    assert finished.output_folder.is_file()  # Session-Original bleibt bestehen


# ---------------------------------------------------------------------
# process-inbox
# ---------------------------------------------------------------------


def test_process_inbox_plain_mode_marks_processed_and_skips_next_run(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    client_a = inbox / "klient-a"
    client_a.mkdir()
    (client_a / "notiz.txt").write_text("Synthetischer Testinhalt A.", encoding="utf-8")

    workflow = ReportWorkflow()
    work_root = tmp_path / "sitzungen"

    first_run = process_inbox(workflow, inbox_dir=inbox, work_root=work_root, mode="plain")
    assert len(first_run) == 1
    assert first_run[0].status == "processed"
    assert (client_a / MARKER_FILENAME).exists()
    sessions_after_first = list(work_root.rglob("prompt.txt"))
    assert len(sessions_after_first) == 1

    second_run = process_inbox(workflow, inbox_dir=inbox, work_root=work_root, mode="plain")
    assert len(second_run) == 1
    assert second_run[0].status == "skipped"
    # Kein neuer Prompt entstanden -- idempotent
    assert list(work_root.rglob("prompt.txt")) == sessions_after_first


def test_process_inbox_dry_run_does_not_write_marker_or_session(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    client_a = inbox / "klient-a"
    client_a.mkdir()
    (client_a / "notiz.txt").write_text("Synthetischer Testinhalt.", encoding="utf-8")

    workflow = ReportWorkflow()
    work_root = tmp_path / "sitzungen"

    results = process_inbox(workflow, inbox_dir=inbox, work_root=work_root, mode="plain", dry_run=True)
    assert results[0].status == "dry_run"
    assert not (client_a / MARKER_FILENAME).exists()
    assert not work_root.exists() or not list(work_root.rglob("prompt.txt"))


def test_process_inbox_anonymized_mode_requires_identity_file(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    client_a = inbox / "klient-ohne-identity"
    client_a.mkdir()
    (client_a / "notiz.txt").write_text("Synthetischer Testinhalt.", encoding="utf-8")

    workflow = ReportWorkflow()
    results = process_inbox(
        workflow, inbox_dir=inbox, work_root=tmp_path / "sitzungen", mode="anonymized", password="pw"
    )
    assert results[0].status == "error"
    assert IDENTITY_FILENAME in results[0].message
    assert not (client_a / MARKER_FILENAME).exists()


def test_process_inbox_ignores_hidden_and_file_entries(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / ".hidden").mkdir()
    (inbox / "stray-file.txt").write_text("kein Ordner", encoding="utf-8")

    results = process_inbox(ReportWorkflow(), inbox_dir=inbox, work_root=tmp_path / "sitzungen", mode="plain")
    assert results == []
