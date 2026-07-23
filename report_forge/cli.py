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
import os
import sys

from . import __version__
from .config import resolve_setting
from .inbox import process_inbox
from .workflow import ReportWorkflow


def cmd_prepare(args: argparse.Namespace) -> int:
    if args.mode == "anonymized":
        real_name = getpass.getpass("Klarname (verdeckte Eingabe): ")
        birth_date = getpass.getpass("Referenzdatum (verdeckte Eingabe): ")
        password = getpass.getpass("Schlüsselpasswort: ")
    else:
        real_name = birth_date = password = None

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
    password = getpass.getpass("Schlüsselpasswort (nur bei mode=anonymized nötig): ")
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
        password = os.environ.get("REPORT_FORGE_INBOX_PASSWORD") or getpass.getpass(
            "Schlüsselpasswort für diesen Inbox-Lauf: "
        )

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

    finish_parser = subparsers.add_parser("finish", help="LLM-JSON rendern und lokal veröffentlichen")
    finish_parser.add_argument("--session", required=True)
    finish_parser.add_argument("--json", required=True)
    finish_parser.add_argument("--output", required=True)
    finish_parser.add_argument("--template")
    finish_parser.add_argument("--output-dir", dest="output_dir", help="Publish-Ziel (überschreibt config)")

    inbox_parser = subparsers.add_parser(
        "process-inbox", help="Jeden Unterordner von inbox_dir als eigene Akte durch prepare() schicken (idempotent)"
    )
    inbox_parser.add_argument("--inbox-dir", dest="inbox_dir", help="überschreibt config")
    inbox_parser.add_argument("--work", required=True)
    inbox_parser.add_argument("--mode", choices=["anonymized", "plain"], default="anonymized")
    inbox_parser.add_argument("--dry-run", action="store_true")

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
