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

workflow.py -- Fail-closed Drei-Phasen-Workflow (Kern)
=========================================================

Portiert und generalisiert aus dem privaten foerderplaner-Skill
(scripts/workflow.py, FoerderplanWorkflow). Orchestriert:

  1. prepare()  -- Quelldokumente lesen, optional anonymisieren,
                   LLM-Prompt atomar ablegen (Sitzungsverzeichnis)
  2. Externes LLM -- ausserhalb dieses Moduls; liest NUR den Prompt und
                   liefert schema-konformes JSON
  3. finish()    -- JSON validieren, Word-Vorlage befuellen, optional
                   de-anonymisieren, atomar lokal veroeffentlichen

Anonymisierung ist SCHALTBAR ueber den `mode`-Parameter:
  - mode="anonymized" (Default): nutzt das externe anonymizer-Modul
    (>=0.2.5) als OPTIONALE Abhaengigkeit -- lazy importiert, erst wenn
    dieser Modus tatsaechlich genutzt wird. Fehlt das Modul, bricht
    prepare()/finish() in diesem Modus fail-closed mit einer klaren
    Fehlermeldung ab (kein stiller Klartext-Fallback).
  - mode="plain": keine Anonymisierung, keine Sitzungs-/Schluessel-
    Verschluesselung -- Quelltext geht UNVERAENDERT in den Prompt. Nur
    sinnvoll, wenn die Quelldokumente nachweislich keine personenbezogenen
    Daten enthalten (z.B. rein technische/synthetische Inhalte). Jeder
    Aufruf mit mode="plain" gibt eine Warnung zurueck.

Die Residualpruefung (Vergleich der bekannten sensiblen Scan-Werte gegen
den fertigen Prompt) schliesst die Scan-Kategorie "ner_review_only" aus
(anonymizer-Modul >=0.2.3): Diese Kategorie ist eine nicht-destruktive
Warnkategorie -- Begriffe darin bleiben absichtlich unveraendert im
anonymisierten Text stehen und duerfen daher weder den Abbruch ausloesen
noch ins Ersetzungs-Mapping einfliessen (siehe RESIDUAL_CHECK_EXCLUDED_
CATEGORIES).

Version: 1.0.0 (generalisiert aus foerderplaner FoerderplanWorkflow, inkl.
des dort am 2026-07-23 gefundenen und gefixten ner_review_only-Bugs)
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SESSION_FORMAT = "report-forge-session-v1"

# Scan-Kategorien, die NICHT in die Residualprüfung (known_sensitive) einfließen.
# "ner_review_only" ist die nicht-destruktive Warnkategorie des anonymizer-Moduls
# ab Version 0.2.3 (Anker-Prinzip): Diese Begriffe wurden geprüft und bewusst
# NICHT ersetzt (bleiben unverändert im anonymisierten Text stehen). Explizit als
# Denylist benannt, damit neue, noch unbekannte Scan-Kategorien sicherheitshalber
# weiterhin als sensibel gelten.
RESIDUAL_CHECK_EXCLUDED_CATEGORIES = frozenset({"ner_review_only"})


@dataclass
class PrepareResult:
    success: bool = False
    session_dir: Path | None = None
    session_path: Path | None = None
    prompt_path: Path | None = None
    anonymized_folder: Path | None = None
    client_id: str = ""
    files_processed: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FinishResult:
    success: bool = False
    output_folder: Path | None = None
    files_processed: int = 0
    replacements: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _atomic_create_text(path: Path, content: str) -> None:
    """Publish complete UTF-8 content without overwriting an existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _resolve_anonymizer_module() -> Path | None:
    """
    Findet den Pfad zum optionalen anonymizer-Modul (>=0.2.5).

    Portiert aus dem foerderplaner-Overlay (services/anonymizer_service.py),
    da diese Pfadauflösung selbst domänen-neutral ist und der Kern
    eigenständig (ohne Overlay) funktionsfähig sein soll.

    Auflösung (in dieser Reihenfolge):
      1. ENV `ANONYMIZER_MODULE_PATH`
      2. Aufwärtssuche von dieser Datei aus nach `.MODULES/.DOMAINS/anonymizer`
         bzw. `.MODULES/anonymizer`
      3. Nutzerneutraler OneDrive-Pfad über `Path.home()`
    """
    env = os.environ.get("ANONYMIZER_MODULE_PATH")
    if env and (Path(env).expanduser() / "anonymizer_modul" / "core.py").exists():
        return Path(env).expanduser().resolve()

    here = Path(__file__).resolve()
    relative_candidates = (
        Path(".MODULES") / ".DOMAINS" / "anonymizer",
        Path(".MODULES") / "anonymizer",
    )
    for parent in here.parents:
        for rel in relative_candidates:
            cand = parent / rel
            if (cand / "anonymizer_modul" / "core.py").exists():
                return cand

    onedrive_ai = Path.home() / "OneDrive" / ".TOPICS" / ".AI"
    for rel in relative_candidates:
        cand = onedrive_ai / rel
        if (cand / "anonymizer_modul" / "core.py").exists():
            return cand.resolve()

    return None


def _default_anonymizer_factories():
    """
    Lazy-Import des optionalen anonymizer-Moduls (>=0.2.5).

    Wird NUR aufgerufen, wenn mode="anonymized" tatsaechlich genutzt wird
    und keine expliziten Factories injiziert wurden. Fehlt das Modul,
    wird ein klarer ImportError geworfen (fail-closed, kein stiller
    Klartext-Fallback).
    """
    module_dir = _resolve_anonymizer_module()
    if module_dir is not None and str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

    try:
        from anonymizer_modul.core import (  # type: ignore
            DocumentAnonymizer,
            DocumentDeanonymizer,
            get_key_path,
        )
    except ImportError as exc:
        raise ImportError(
            "mode='anonymized' erfordert das optionale anonymizer-Modul "
            "(>=0.2.5), das nicht gefunden wurde. Entweder das Modul "
            "installieren/ueber ANONYMIZER_MODULE_PATH auffindbar machen, "
            "oder explizit mode='plain' verwenden (nur fuer nachweislich "
            "unkritische Quelldaten)."
        ) from exc
    return DocumentAnonymizer, DocumentDeanonymizer, get_key_path


class ReportWorkflow:
    """Koordiniert Extraktion, optionale Anonymisierung, Prompt-Erzeugung
    und lokale Klartext-Publikation.

    SESSION_FORMAT ist ein Klassenattribut (nicht das Modul-Level-Default),
    damit Overlays per Subklasse ihr eigenes, historisch gewachsenes
    Sitzungsformat beibehalten koennen (z.B. um bereits archivierte
    Sitzungen weiter verarbeiten zu koennen), ohne die Kern-Logik zu
    duplizieren:

        class MyOverlayWorkflow(ReportWorkflow):
            SESSION_FORMAT = "my-overlay-session-v1"
    """

    SESSION_FORMAT = SESSION_FORMAT

    def __init__(
        self,
        *,
        anonymizer_factory: Callable[[], Any] | None = None,
        deanonymizer_factory: Callable[[], Any] | None = None,
        generator_factory: Callable[[], Any] | None = None,
        key_path_resolver: Callable[[str], Path] | None = None,
    ) -> None:
        """
        Alle vier Parameter sind Dependency-Injection-Punkte fuer Overlays:

        - anonymizer_factory/deanonymizer_factory/key_path_resolver: nur
          fuer mode="anonymized" benoetigt; Default lazy-importiert das
          optionale anonymizer-Modul erst beim ersten Aufruf.
        - generator_factory: MUSS ein Objekt liefern, das
          `.extract_sources(folder) -> str`, `.build_prompt(text, schema_name) -> str`
          und `.fill_report(data, template_path, output_path) -> RenderResult`
          bereitstellt. Der Kern liefert `report_forge.generator.ReportGenerator`
          als generischen Default; ein Overlay uebergibt hier typischerweise
          seine eigene, domaenenspezifische Implementierung (z.B. mit ICF-
          Katalog im Prompt und einer Word-Vorlage mit fester Feldstruktur).
        """
        self._anonymizer_factory = anonymizer_factory
        self._deanonymizer_factory = deanonymizer_factory
        self._key_path_resolver = key_path_resolver

        if generator_factory is None:
            from .generator import ReportGenerator

            generator_factory = ReportGenerator
        self._generator_factory = generator_factory

    def _resolve_anonymizer_factories(self):
        if self._anonymizer_factory and self._deanonymizer_factory and self._key_path_resolver:
            return self._anonymizer_factory, self._deanonymizer_factory, self._key_path_resolver
        anonymizer_cls, deanonymizer_cls, key_path_fn = _default_anonymizer_factories()
        return (
            self._anonymizer_factory or anonymizer_cls,
            self._deanonymizer_factory or deanonymizer_cls,
            self._key_path_resolver or key_path_fn,
        )

    # -----------------------------------------------------------------
    # Phase 1: prepare
    # -----------------------------------------------------------------

    def prepare(
        self,
        *,
        source_folder: str | Path,
        work_root: str | Path,
        mode: str = "anonymized",
        real_name: str | None = None,
        birth_date: str | None = None,
        password: str | None = None,
        schema_name: str | None = None,
    ) -> PrepareResult:
        """Create an LLM prompt, optionally only after complete anonymization succeeds."""
        if mode not in ("anonymized", "plain"):
            result = PrepareResult()
            result.errors.append("mode muss 'anonymized' oder 'plain' sein")
            return result

        if mode == "anonymized":
            return self._prepare_anonymized(
                source_folder=source_folder,
                work_root=work_root,
                real_name=real_name or "",
                birth_date=birth_date or "",
                password=password or "",
                schema_name=schema_name,
            )
        return self._prepare_plain(
            source_folder=source_folder, work_root=work_root, schema_name=schema_name
        )

    def _prepare_plain(
        self, *, source_folder: str | Path, work_root: str | Path, schema_name: str | None
    ) -> PrepareResult:
        result = PrepareResult()
        source = Path(source_folder).expanduser().resolve()
        work = Path(work_root).expanduser().resolve()
        if not source.is_dir():
            result.errors.append("Quellordner fehlt oder ist kein Verzeichnis")
            return result
        if _is_within(work, source) or _is_within(source, work):
            result.errors.append("Arbeits- und Quellordner dürfen sich nicht überlappen")
            return result

        result.warnings.append(
            "mode='plain': Quelltext wird UNVERAENDERT (nicht anonymisiert) in den "
            "Prompt übernommen. Nur für nachweislich unkritische Quelldaten verwenden."
        )

        session_dir: Path | None = None
        try:
            generator = self._generator_factory()
            source_text = generator.extract_sources(str(source))
            if not source_text.strip() or source_text.startswith("[FEHLER"):
                result.errors.append("Aus den Quelldokumenten konnte kein Text extrahiert werden")
                return result

            prompt = generator.build_prompt(source_text, schema_name)

            client_id = "PLAIN_" + secrets.token_hex(4).upper()
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            session_dir = work / f"{client_id}-{stamp}"
            session_dir.mkdir(parents=True, exist_ok=False)

            bundled = session_dir / "data_bundled"
            prompt_path = bundled / "prompt.txt"
            _atomic_create_text(prompt_path, prompt)

            session_path = session_dir / "session.json"
            metadata = {
                "format": self.SESSION_FORMAT,
                "mode": "plain",
                "client_id": client_id,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "prompt": "data_bundled/prompt.txt",
            }
            _atomic_create_text(session_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")

            result.success = True
            result.session_dir = session_dir
            result.session_path = session_path
            result.prompt_path = prompt_path
            result.client_id = client_id
            return result
        except FileExistsError:
            result.errors.append("Sitzungsartefakt existiert bereits; es wurde nichts überschrieben")
        except Exception as exc:
            result.errors.append(f"Vorbereitung abgebrochen ({type(exc).__name__})")
        if session_dir is not None:
            shutil.rmtree(session_dir, ignore_errors=True)
        return result

    def _prepare_anonymized(
        self,
        *,
        source_folder: str | Path,
        work_root: str | Path,
        real_name: str,
        birth_date: str,
        password: str,
        schema_name: str | None,
    ) -> PrepareResult:
        result = PrepareResult()
        source = Path(source_folder).expanduser().resolve()
        work = Path(work_root).expanduser().resolve()
        if not source.is_dir():
            result.errors.append("Quellordner fehlt oder ist kein Verzeichnis")
            return result
        if _is_within(work, source) or _is_within(source, work):
            result.errors.append("Arbeits- und Quellordner dürfen sich nicht überlappen")
            return result
        if not real_name.strip() or not birth_date.strip() or not password:
            result.errors.append("Name, Geburtsdatum und Passwort sind erforderlich")
            return result

        session_dir: Path | None = None
        try:
            anonymizer_cls, _deanonymizer_cls, _key_path_fn = self._resolve_anonymizer_factories()
            anonymizer = anonymizer_cls()
            scanned = anonymizer.scan_folder_for_sensitive_data(str(source))
            profile = anonymizer.create_profile(
                real_name=real_name, geburtsdatum=birth_date, scanned_data=scanned
            )
            client_id = str(profile.client_id)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            session_dir = work / f"{client_id}-{stamp}-{secrets.token_hex(4)}"
            session_dir.mkdir(parents=True, exist_ok=False)
            anonymized_folder = session_dir / "data_ano"

            anonymized = anonymizer.anonymize_folder(
                folder=str(source),
                profile=profile,
                password=password,
                output_folder=str(anonymized_folder),
            )
            result.warnings.extend(str(v) for v in getattr(anonymized, "warnings", []))
            errors = [str(v) for v in getattr(anonymized, "errors", [])]
            if errors:
                result.errors.extend(errors)
                shutil.rmtree(session_dir, ignore_errors=True)
                return result

            generator = self._generator_factory()
            source_text = generator.extract_sources(str(anonymized_folder))
            if not source_text.strip() or source_text.startswith("[FEHLER"):
                result.errors.append(
                    "Aus den anonymisierten Dokumenten konnte kein Text extrahiert werden"
                )
                shutil.rmtree(session_dir, ignore_errors=True)
                return result
            prompt = generator.build_prompt(source_text, schema_name)

            known_sensitive = {real_name.strip(), birth_date.strip()}
            if isinstance(scanned, dict):
                for category, values in scanned.items():
                    if category in RESIDUAL_CHECK_EXCLUDED_CATEGORIES:
                        continue
                    if isinstance(values, (list, tuple, set)):
                        known_sensitive.update(
                            str(value).strip() for value in values if len(str(value).strip()) >= 3
                        )
            prompt_folded = prompt.casefold()
            if any(value and value.casefold() in prompt_folded for value in known_sensitive):
                result.errors.append("Residualprüfung fand bekannte Klartextdaten im Prompt")
                shutil.rmtree(session_dir, ignore_errors=True)
                return result

            bundled = session_dir / "data_bundled"
            prompt_path = bundled / "prompt.txt"
            _atomic_create_text(prompt_path, prompt)
            session_path = session_dir / "session.json"
            metadata = {
                "format": self.SESSION_FORMAT,
                "mode": "anonymized",
                "client_id": client_id,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "anonymized_folder": "data_ano",
                "prompt": "data_bundled/prompt.txt",
                "key_location": "external-encrypted-store",
            }
            _atomic_create_text(session_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")

            result.success = True
            result.session_dir = session_dir
            result.session_path = session_path
            result.prompt_path = prompt_path
            result.anonymized_folder = anonymized_folder
            result.client_id = client_id
            result.files_processed = int(getattr(anonymized, "processed_files", 0))
            return result
        except FileExistsError:
            result.errors.append("Sitzungsartefakt existiert bereits; es wurde nichts überschrieben")
        except Exception as exc:
            result.errors.append(f"Vorbereitung abgebrochen ({type(exc).__name__})")
        if session_dir is not None:
            shutil.rmtree(session_dir, ignore_errors=True)
        return result

    # -----------------------------------------------------------------
    # Phase 3: finish
    # -----------------------------------------------------------------

    def finish(
        self,
        *,
        session_dir: str | Path,
        llm_json_path: str | Path,
        output_folder: str | Path,
        password: str | None = None,
        template_path: str | Path | None = None,
    ) -> FinishResult:
        """Render a report and (if the session was anonymized) deanonymize it
        into a local output tree."""
        result = FinishResult()
        session = Path(session_dir).expanduser().resolve()
        json_path = Path(llm_json_path).expanduser().resolve()
        output = Path(output_folder).expanduser().resolve()
        if not session.is_dir() or not (session / "session.json").is_file():
            result.errors.append("Gültige Sitzung fehlt")
            return result
        if not _is_within(json_path, session):
            result.errors.append("LLM-JSON muss innerhalb der Sitzung liegen")
            return result
        if not json_path.is_file():
            result.errors.append("LLM-JSON fehlt")
            return result
        if output.exists():
            result.errors.append("Klartext-Ziel muss neu sein")
            return result

        try:
            metadata = json.loads((session / "session.json").read_text(encoding="utf-8"))
            if metadata.get("format") != self.SESSION_FORMAT:
                result.errors.append("Unbekanntes Sitzungsformat")
                return result
            session_mode = metadata.get("mode", "anonymized")
            report_data = json.loads(json_path.read_text(encoding="utf-8"))
            if not isinstance(report_data, dict):
                result.errors.append("LLM-JSON muss ein Objekt enthalten")
                return result

            generator = self._generator_factory()

            if session_mode == "plain":
                output.parent.mkdir(parents=True, exist_ok=True)
                generated = generator.fill_report(
                    report_data, str(template_path) if template_path else None, str(output)
                )
                result.warnings.extend(str(v) for v in getattr(generated, "warnings", []))
                generated_errors = [str(v) for v in getattr(generated, "errors", [])]
                if generated_errors or not getattr(generated, "success", False):
                    result.errors.extend(generated_errors or ["Bericht konnte nicht erzeugt werden"])
                    return result
                result.success = True
                result.output_folder = output
                return result

            client_id = str(metadata.get("client_id", ""))
            if not client_id:
                result.errors.append("Client-ID fehlt in der Sitzung")
                return result

            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="report-forge-finish-") as temporary:
                anonymized_report = Path(temporary) / "report.docx"
                generated = generator.fill_report(
                    report_data, str(template_path) if template_path else None, str(anonymized_report)
                )
                result.warnings.extend(str(v) for v in getattr(generated, "warnings", []))
                generated_errors = [str(v) for v in getattr(generated, "errors", [])]
                if generated_errors or not getattr(generated, "success", False):
                    result.errors.extend(
                        generated_errors or ["Anonymisierter Bericht konnte nicht erzeugt werden"]
                    )
                    return result

                publish_root = Path(tempfile.mkdtemp(prefix=".report-forge-publish-", dir=output.parent))
                staged_output = publish_root / "payload"
                try:
                    _anonymizer_cls, deanonymizer_cls, key_path_fn = self._resolve_anonymizer_factories()
                    deanonymizer = deanonymizer_cls()
                    deanon = deanonymizer.deanonymize_folder(
                        folder=temporary,
                        schluessel_path=str(key_path_fn(client_id)),
                        password=password or "",
                        output_folder=str(staged_output),
                        client_id=client_id,
                    )
                    result.warnings.extend(str(v) for v in getattr(deanon, "warnings", []))
                    deanon_errors = [str(v) for v in getattr(deanon, "errors", [])]
                    if deanon_errors or not staged_output.is_dir():
                        result.errors.extend(deanon_errors or ["De-Anonymisierung ohne Ausgabe beendet"])
                        return result
                    result.files_processed = int(getattr(deanon, "processed_files", 0))
                    result.replacements = int(getattr(deanon, "replacements_total", 0))
                    os.replace(staged_output, output)
                finally:
                    shutil.rmtree(publish_root, ignore_errors=True)

            result.success = True
            result.output_folder = output
            return result
        except Exception as exc:
            result.errors.append(f"Abschluss abgebrochen ({type(exc).__name__})")
            return result
