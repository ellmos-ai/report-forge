#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
Copyright (c) 2026 Lukas Geiger

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

schema_service.py -- Konfigurierbare JSON-Schema-Mechanik
=============================================================

Der eigentliche Berichts-Vertrag (z.B. foerderbericht.json) ist IMMER
Sache des Overlays/der konkreten Domaene -- dieses Modul liefert nur den
Lade- und ValidierungsMECHANISMUS (Pfad-basiert, kein hartcodierter
Domaenen-Name).

Version: 1.0.0
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


def load_schema(schema_path: str | Path) -> dict:
    """
    Laedt ein JSON-Schema von einem expliziten Pfad.

    Args:
        schema_path: Pfad zur Schema-JSON-Datei (z.B. aus config.json
            eines Overlays: `schema_path: "schemas/foerderbericht.json"`)

    Raises:
        FileNotFoundError: wenn die Datei nicht existiert
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema nicht gefunden: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema_by_name(schemas_dir: str | Path, schema_name: str) -> dict:
    """Komfort-Variante: laedt `<schemas_dir>/<schema_name>.json`."""
    return load_schema(Path(schemas_dir) / f"{schema_name}.json")


def validate_report_schema(report_data: dict, schema: dict) -> List[str]:
    """
    Validiert report_data gegen ein bereits geladenes JSON-Schema
    (Draft 2020-12) und gibt eine Liste wertfreier Fehlermeldungen zurueck
    (keine Nutzdaten in den Meldungen, nur JSON-Pfad + Validator-Name --
    sicher fuer Logs/Fehlerausgaben).
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["JSON-Schema-Validierung nicht verfügbar (jsonschema fehlt)"]

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return [f"Berichtsschema ist ungültig ({type(exc).__name__})"]

    errors: List[str] = []
    for error in sorted(
        Draft202012Validator(schema).iter_errors(report_data),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$" + "".join(f"[{part!r}]" for part in error.absolute_path)
        errors.append(f"Schemafehler bei {path} ({error.validator})")
    return errors
