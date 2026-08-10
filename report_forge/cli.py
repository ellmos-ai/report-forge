#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
cli.py -- Minimale CLI fuer report-forge (Referenz/Debug).

HINWEIS (bekanntes Problem, siehe README "Bekannte Probleme"): Unter
Windows liest `getpass.getpass()` ueber `msvcrt` direkt von der Konsole
und ignoriert umgeleitetes/gepipetes stdin (Git Bash, CI, Subprozess-
Aufrufe) -- der Aufruf blockiert dann unbegrenzt statt einen Fehler zu
werfen. Fuer automatisierte/nicht-interaktive Nutzung daher IMMER die
Python-API (`ReportWorkflow.prepare()`/`.finish()`/`process_inbox()`)
direkt verwenden statt diese CLI zu piped-stdin zu treiben.

`--output-dir` (finish) und `--inbox-dir`/`--work` (process-inbox) folgen
der Config-Auflösung CLI-Argument > config.local.json > config.json >
nicht gesetzt (siehe config.py).
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

from . import __version__
from .config import resolve_setting
from .inbox import process_inbox
from .workflow import ReportWorkflow


class SecretInputError(RuntimeError):
    """Raised when a required secret cannot be obtained without blocking."""


def _has_interactive_tty() -> bool:
    """Return whether both input and diagnostics are attached to a TTY."""
    try:
        return bool(sys.stdin.isatty() and sys.stderr.isatty())
    except (AttributeError, OSError):
        return False


def _read_secret(*, env_name: str, prompt: str) -> str:
    """Read a secret from a named environment variable or a real TTY.

    Values are never printed or included in errors.  Command-line arguments
    carry only the environment-variable *name*, never the secret itself.
    """
    value = os.environ.get(env_name)
    if value is not None:
        if value:
            return value
        raise SecretInputError(f"Umgebungsvariable {env_name} ist leer")
    if not _has_interactive_tty():
        raise SecretInputError(f"keine interaktive TTY; setze {env_name}")
    try:
        value = getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt, OSError) as exc:
        raise SecretInputError(f"interaktive Eingabe fehlgeschlagen; setze {env_name}") from exc
    if not value:
        raise SecretInputError(f"Eingabe leer; setze {env_name}")
    return value


def _secret_error(exc: SecretInputError) -> int:
    """Print a value-free diagnostic and return the standard CLI error code."""
    print(f"Secret-Eingabe nicht verfügbar: {exc}", file=sys.stderr)
    return 2


def _session_mode(session: str | os.PathLike[str]) -> str | None:
    """Read a session mode without prompting for a malformed/missing session."""
    session_file = Path(session).expanduser() / "session.json"
    if not session_file.is_file():
        return None
    try:
        metadata = json.loads(session_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    return str(metadata.get("mode", "anonymized"))


def cmd_prepare(args: argparse.Namespace) -> int:
    try:
        if args.mode == "anonymized":
            real_name = _read_secret(env_name=args.real_name_env, prompt="Klarname (verdeckte Eingabe): ")
            birth_date = _read_secret(env_name=args.birth_date_env, prompt="Referenzdatum (verdeckte Eingabe): ")
            password = _read_secret(env_name=args.password_env, prompt="Schlüsselpasswort: ")
        else:
            real_name = birth_date = password = None
    except SecretInputError as exc:
        return _secret_error(exc)

    result = ReportWorkflow().prepare(
        source_folder=args.source,
        work_root=args.work,
        mode=args.mode,
        real_name=real_name,
        birth_date=birth_date,
        password=password,
    )
    if not result.success:
        print("Vorbereitung fehlgeschlagen: " + "; ".join(result.errors), file=sys.stderr)
        return 2
    print(f"Sitzung erstellt ({result.client_id}). Prompt: {result.prompt_path}")
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    try:
        mode = _session_mode(args.session)
        password = (
            _read_secret(env_name=args.password_env, prompt="Schlüsselpasswort (nur bei mode=anonymized nötig): ")
            if mode not in (None, "plain")
            else None
        )
    except SecretInputError as exc:
        return _secret_error(exc)
    output_dir = resolve_setting("output_dir", cli_value=args.output_dir)
    result = ReportWorkflow().finish(
        session_dir=args.session,
        llm_json_path=args.json,
        output_folder=args.output,
        password=password,
        template_path=args.template,
        output_dir=output_dir,
    )
    if not result.success:
        print("Abschluss fehlgeschlagen: " + "; ".join(result.errors), file=sys.stderr)
        return 2
    print("Bericht lokal veröffentlicht.")
    if result.published_path:
        print(f"Zusätzlich veröffentlicht nach: {result.published_path}")
    for warning in result.warnings:
        print(f"WARNUNG: {warning}", file=sys.stderr)
    return 0


def cmd_process_inbox(args: argparse.Namespace) -> int:
    inbox_dir = resolve_setting("inbox_dir", cli_value=args.inbox_dir)
    if not inbox_dir:
        print("inbox_dir weder per --inbox-dir noch config gesetzt.", file=sys.stderr)
        return 2

    password = None
    if args.mode == "anonymized" and not args.dry_run:
        try:
            password = _read_secret(env_name=args.password_env, prompt="Schlüsselpasswort für diesen Inbox-Lauf: ")
        except SecretInputError as exc:
            return _secret_error(exc)

    results = process_inbox(
        ReportWorkflow(),
        inbox_dir=inbox_dir,
        work_root=args.work,
        mode=args.mode,
        password=password,
        dry_run=args.dry_run,
    )
    for item in results:
        print(f"[{item.status}] {item.folder.name}" + (f" -- {item.message}" if item.message else ""))
    return 0 if all(item.status != "error" for item in results) else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="report-forge — Berichts-Pipeline-Kern")
    parser.add_argument("--version", action="version", version=f"report-forge v{__version__}")
    parser.add_argument("--info", action="store_true", help="Modulinformationen anzeigen")

    subparsers = parser.add_subparsers(dest="command")

    prepare_parser = subparsers.add_parser("prepare", help="Quellen lesen, optional anonymisieren, Prompt erzeugen")
    prepare_parser.add_argument("--source", required=True)
    prepare_parser.add_argument("--work", required=True)
    prepare_parser.add_argument("--mode", choices=["anonymized", "plain"], default="anonymized")
    prepare_parser.add_argument(
        "--real-name-env", default="REPORT_FORGE_REAL_NAME", metavar="NAME",
        help="Umgebungsvariable für den Klarnamen (nur anonymized; kein Geheimnis als CLI-Wert)",
    )
    prepare_parser.add_argument(
        "--birth-date-env", default="REPORT_FORGE_BIRTH_DATE", metavar="NAME",
        help="Umgebungsvariable für das Referenzdatum (nur anonymized)",
    )
    prepare_parser.add_argument(
        "--password-env", default="REPORT_FORGE_PASSWORD", metavar="NAME",
        help="Umgebungsvariable für das Schlüsselpasswort (nur anonymized)",
    )

    finish_parser = subparsers.add_parser("finish", help="LLM-JSON rendern und lokal veröffentlichen")
    finish_parser.add_argument("--session", required=True)
    finish_parser.add_argument("--json", required=True)
    finish_parser.add_argument("--output", required=True)
    finish_parser.add_argument("--template")
    finish_parser.add_argument("--output-dir", dest="output_dir", help="Publish-Ziel (überschreibt config)")
    finish_parser.add_argument(
        "--password-env", default="REPORT_FORGE_PASSWORD", metavar="NAME",
        help="Umgebungsvariable für das Schlüsselpasswort (anonymized)",
    )

    inbox_parser = subparsers.add_parser(
        "process-inbox", help="Jeden Unterordner von inbox_dir als eigene Akte durch prepare() schicken (idempotent)"
    )
    inbox_parser.add_argument("--inbox-dir", dest="inbox_dir", help="überschreibt config")
    inbox_parser.add_argument("--work", required=True)
    inbox_parser.add_argument("--mode", choices=["anonymized", "plain"], default="anonymized")
    inbox_parser.add_argument("--dry-run", action="store_true")
    inbox_parser.add_argument(
        "--password-env", default="REPORT_FORGE_INBOX_PASSWORD", metavar="NAME",
        help="Umgebungsvariable für das gemeinsame Inbox-Passwort (anonymized)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.info:
        print(f"report-forge v{__version__}")
        print("Drei-Phasen-Berichts-Pipeline-Kern (prepare -> externes LLM -> finish)")
        return 0

    handlers = {"prepare": cmd_prepare, "finish": cmd_finish, "process-inbox": cmd_process_inbox}
    if args.command in handlers:
        return handlers[args.command](args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
