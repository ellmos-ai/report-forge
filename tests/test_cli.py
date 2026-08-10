# -*- coding: utf-8 -*-
"""Deterministische CLI-Secret- und Nichtinteraktivitätsverträge."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import report_forge.cli as cli


def test_read_secret_prefers_named_environment_variable(monkeypatch):
    monkeypatch.setenv("REPORT_FORGE_TEST_SECRET", "fixture-secret")
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: pytest.fail("TTY prompt must not run"))

    assert cli._read_secret(env_name="REPORT_FORGE_TEST_SECRET", prompt="ignored") == "fixture-secret"


def test_read_secret_fails_fast_without_tty_and_does_not_leak_value(monkeypatch):
    monkeypatch.delenv("REPORT_FORGE_TEST_SECRET", raising=False)
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)

    with pytest.raises(cli.SecretInputError, match="REPORT_FORGE_TEST_SECRET") as error:
        cli._read_secret(env_name="REPORT_FORGE_TEST_SECRET", prompt="ignored")

    assert "fixture-secret" not in str(error.value)


def test_prepare_noninteractive_missing_secret_returns_clear_exit(monkeypatch, capsys, tmp_path: Path):
    monkeypatch.delenv("REPORT_FORGE_PREPARE_NAME", raising=False)
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)
    args = cli.build_parser().parse_args(
        [
            "prepare",
            "--source",
            str(tmp_path / "source"),
            "--work",
            str(tmp_path / "work"),
            "--real-name-env",
            "REPORT_FORGE_PREPARE_NAME",
        ]
    )

    assert cli.cmd_prepare(args) == 2
    stderr = capsys.readouterr().err
    assert "REPORT_FORGE_PREPARE_NAME" in stderr
    assert "getpass" not in stderr
    assert "fixture-secret" not in stderr


def test_prepare_noninteractive_uses_named_environment_contract(monkeypatch, tmp_path: Path, capsys):
    values = {
        "REPORT_FORGE_NAME": "Fixture Person",
        "REPORT_FORGE_DATE": "01.01.2000",
        "REPORT_FORGE_KEY": "fixture-key",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)
    calls = {}

    class FakeWorkflow:
        def prepare(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(success=True, client_id="fixture", prompt_path=tmp_path / "prompt.txt")

    monkeypatch.setattr(cli, "ReportWorkflow", FakeWorkflow)
    args = cli.build_parser().parse_args(
        [
            "prepare",
            "--source",
            str(tmp_path / "source"),
            "--work",
            str(tmp_path / "work"),
            "--real-name-env",
            "REPORT_FORGE_NAME",
            "--birth-date-env",
            "REPORT_FORGE_DATE",
            "--password-env",
            "REPORT_FORGE_KEY",
        ]
    )

    assert cli.cmd_prepare(args) == 0
    assert calls["real_name"] == values["REPORT_FORGE_NAME"]
    assert calls["birth_date"] == values["REPORT_FORGE_DATE"]
    assert calls["password"] == values["REPORT_FORGE_KEY"]
    assert values["REPORT_FORGE_KEY"] not in capsys.readouterr().out


def test_finish_plain_session_does_not_prompt_without_tty(monkeypatch, tmp_path: Path):
    session = tmp_path / "session"
    session.mkdir()
    (session / "session.json").write_text(json.dumps({"mode": "plain"}), encoding="utf-8")
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)
    calls = {}

    class FakeWorkflow:
        def finish(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(success=True, published_path=None, warnings=[])

    monkeypatch.setattr(cli, "ReportWorkflow", FakeWorkflow)
    args = cli.build_parser().parse_args(
        [
            "finish",
            "--session",
            str(session),
            "--json",
            str(session / "report.json"),
            "--output",
            str(tmp_path / "output.docx"),
        ]
    )

    assert cli.cmd_finish(args) == 0
    assert calls["password"] is None


def test_finish_anonymized_session_fails_fast_without_tty(monkeypatch, capsys, tmp_path: Path):
    session = tmp_path / "session"
    session.mkdir()
    (session / "session.json").write_text(json.dumps({"mode": "anonymized"}), encoding="utf-8")
    monkeypatch.delenv("REPORT_FORGE_FINISH_KEY", raising=False)
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)
    args = cli.build_parser().parse_args(
        [
            "finish",
            "--session",
            str(session),
            "--json",
            str(session / "report.json"),
            "--output",
            str(tmp_path / "output.docx"),
            "--password-env",
            "REPORT_FORGE_FINISH_KEY",
        ]
    )

    assert cli.cmd_finish(args) == 2
    assert "REPORT_FORGE_FINISH_KEY" in capsys.readouterr().err


def test_process_inbox_uses_named_environment_contract_without_tty(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("REPORT_FORGE_BATCH_KEY", "batch-secret")
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)
    calls = {}

    def fake_process(workflow, **kwargs):
        calls.update(kwargs)
        return []

    monkeypatch.setattr(cli, "process_inbox", fake_process)
    args = cli.build_parser().parse_args(
        [
            "process-inbox",
            "--inbox-dir",
            str(tmp_path / "inbox"),
            "--work",
            str(tmp_path / "work"),
            "--password-env",
            "REPORT_FORGE_BATCH_KEY",
        ]
    )

    assert cli.cmd_process_inbox(args) == 0
    assert calls["password"] == "batch-secret"


def test_process_inbox_missing_secret_returns_clear_exit(monkeypatch, capsys, tmp_path: Path):
    monkeypatch.delenv("REPORT_FORGE_BATCH_KEY", raising=False)
    monkeypatch.setattr(cli, "_has_interactive_tty", lambda: False)
    args = cli.build_parser().parse_args(
        [
            "process-inbox",
            "--inbox-dir",
            str(tmp_path / "inbox"),
            "--work",
            str(tmp_path / "work"),
            "--password-env",
            "REPORT_FORGE_BATCH_KEY",
        ]
    )

    assert cli.cmd_process_inbox(args) == 2
    assert "REPORT_FORGE_BATCH_KEY" in capsys.readouterr().err
