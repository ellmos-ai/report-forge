#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report-forge -- Domaenen-neutraler Kern fuer anonymisierbare
Berichts-Pipelines (Extraktion -> LLM-Prompt -> Word-Vorlage).

License: MIT
"""

__version__ = "1.1.0"
__author__ = "Lukas Geiger"

from pathlib import Path

MODULE_PATH = Path(__file__).parent
SERVICES_PATH = MODULE_PATH / "services"
PACKAGE_ROOT = MODULE_PATH.parent
SCHEMAS_PATH = PACKAGE_ROOT / "schemas"
TEMPLATES_PATH = PACKAGE_ROOT / "templates"

from .workflow import ReportWorkflow, PrepareResult, FinishResult, publish_copy  # noqa: E402,F401
from .inbox import process_inbox, InboxItemResult  # noqa: E402,F401
from .config import load_config, resolve_setting  # noqa: E402,F401
