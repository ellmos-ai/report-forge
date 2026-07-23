#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
config.py -- Konfigurations-Auflösung (config.json / config.local.json)
============================================================================

Auflösungsreihenfolge für jede Einstellung: CLI-Argument > config.local.json
> config.json > nicht gesetzt (None). `config.local.json` ist gitignored
(siehe .gitignore) und überschreibt Werte aus `config.json` innerhalb des
"defaults"-Objekts (flacher Merge, keine Rekursion nötig für die aktuellen
Einstellungen).

Version: 1.0.0
"""

from __future__ import annotations

import json
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def load_config(package_root: str | Path | None = None) -> dict:
    """Lädt config.json und merged config.local.json (falls vorhanden)."""
    root = Path(package_root) if package_root else PACKAGE_ROOT
    config: dict = {}

    config_path = root / "config.json"
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    local_path = root / "config.local.json"
    if local_path.is_file():
        local = json.loads(local_path.read_text(encoding="utf-8"))
        merged_defaults = dict(config.get("defaults", {}))
        merged_defaults.update(local.get("defaults", {}))
        config["defaults"] = merged_defaults

    return config


def resolve_setting(
    key: str,
    *,
    cli_value: str | None = None,
    package_root: str | Path | None = None,
    config: dict | None = None,
) -> str | None:
    """
    Löst eine einzelne Einstellung auf: CLI-Argument > config.local.json
    > config.json > None (= nicht gesetzt, Verhalten wie ohne dieses
    Feature -- z.B. kein Publish-Schritt, wenn `output_dir` unresolved
    bleibt).
    """
    if cli_value:
        return cli_value
    cfg = config if config is not None else load_config(package_root)
    value = cfg.get("defaults", {}).get(key)
    return value or None
