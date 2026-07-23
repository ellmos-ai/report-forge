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
Python-API (`ReportWorkflow.prepare()`/`.finish()`) direkt verwenden statt
diese CLI zu piped-stdin zu treiben.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from . import __version__
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
    result = ReportWorkflow().finish(
        session_dir=args.session,
        llm_json_path=args.json,
        output_folder=args.output,
        password=password,
        template_path=args.template,
    )
    if not result.success:
        print("Abschluss fehlgeschlagen: " + "; ".join(result.errors), file=sys.stderr)
        return 2
    print("Bericht lokal veröffentlicht.")
    return 0


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.info:
        print(f"report-forge v{__version__}")
        print("Drei-Phasen-Berichts-Pipeline-Kern (prepare -> externes LLM -> finish)")
        return 0

    handlers = {"prepare": cmd_prepare, "finish": cmd_finish}
    if args.command in handlers:
        return handlers[args.command](args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
