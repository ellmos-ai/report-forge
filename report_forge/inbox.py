#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
inbox.py -- Idempotenter Batch-Verarbeiter für einen Abholort (inbox_dir)
=============================================================================

KEIN Daemon/Watcher. `process_inbox()` verarbeitet bei jedem Aufruf jeden
direkten Unterordner von `inbox_dir` als eigene Quell-Akte durch
`ReportWorkflow.prepare()` -- gedacht zum Aufruf durch Automationen
(Scheduled Task, Cron, o.ä.), die diese Funktion/den CLI-Befehl
`process-inbox` periodisch selbst anstoßen.

Marker-Datei `.processed` im Unterordner nach ERFOLGREICHER Verarbeitung
-> beim nächsten Lauf übersprungen (idempotent). Fehlgeschlagene
Unterordner bekommen KEINEN Marker und werden beim nächsten Lauf erneut
versucht.

mode="anonymized": jeder zu verarbeitende Unterordner MUSS eine
Identitäts-Datei `.identity.json` mit `{"real_name": "...",
"birth_date": "..."}` enthalten (niemals einchecken/loggen!) -- das
gemeinsame `password` gilt für den gesamten Inbox-Lauf. Fehlt die Datei,
wird der Unterordner mit status="error" übersprungen (fail-closed, kein
stiller Klartext-Fallback und kein impliziter Rate auf Ordnernamen).

mode="plain": keine Identitäts-Datei nötig.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .workflow import PrepareResult, ReportWorkflow

MARKER_FILENAME = ".processed"
IDENTITY_FILENAME = ".identity.json"


@dataclass
class InboxItemResult:
    folder: Path
    status: str  # "processed" | "skipped" | "error" | "dry_run"
    prepare_result: PrepareResult | None = None
    message: str = ""


def _read_identity(folder: Path) -> tuple[str, str] | None:
    identity_path = folder / IDENTITY_FILENAME
    if not identity_path.is_file():
        return None
    try:
        data = json.loads(identity_path.read_text(encoding="utf-8"))
        real_name = str(data.get("real_name", "")).strip()
        birth_date = str(data.get("birth_date", "")).strip()
        if not real_name or not birth_date:
            return None
        return real_name, birth_date
    except (json.JSONDecodeError, OSError):
        return None


def process_inbox(
    workflow: ReportWorkflow,
    *,
    inbox_dir: str | Path,
    work_root: str | Path,
    mode: str = "anonymized",
    password: str | None = None,
    schema_name: str | None = None,
    dry_run: bool = False,
) -> list[InboxItemResult]:
    """Verarbeitet jeden direkten Unterordner von inbox_dir (siehe Modul-Docstring)."""
    inbox = Path(inbox_dir).expanduser().resolve()
    results: list[InboxItemResult] = []

    if not inbox.is_dir():
        return [InboxItemResult(folder=inbox, status="error", message="inbox_dir nicht gefunden")]

    for entry in sorted(inbox.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue

        marker = entry / MARKER_FILENAME
        if marker.exists():
            results.append(InboxItemResult(folder=entry, status="skipped", message="bereits verarbeitet (.processed)"))
            continue

        if mode == "anonymized":
            identity = _read_identity(entry)
            if identity is None:
                results.append(
                    InboxItemResult(
                        folder=entry,
                        status="error",
                        message=f"{IDENTITY_FILENAME} fehlt oder unvollständig (real_name/birth_date)",
                    )
                )
                continue
            real_name, birth_date = identity
        else:
            real_name = birth_date = None

        if dry_run:
            results.append(InboxItemResult(folder=entry, status="dry_run", message="würde verarbeitet"))
            continue

        prepared = workflow.prepare(
            source_folder=entry,
            work_root=work_root,
            mode=mode,
            real_name=real_name,
            birth_date=birth_date,
            password=password,
            schema_name=schema_name,
        )
        if prepared.success:
            marker.write_text("", encoding="utf-8")
            results.append(InboxItemResult(folder=entry, status="processed", prepare_result=prepared))
        else:
            results.append(
                InboxItemResult(
                    folder=entry,
                    status="error",
                    prepare_result=prepared,
                    message="; ".join(prepared.errors) or "prepare() fehlgeschlagen",
                )
            )

    return results
