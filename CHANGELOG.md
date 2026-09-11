# Changelog

Alle relevanten Änderungen an `report-forge` werden in dieser Datei dokumentiert.

## [1.1.6] - 2026-09-11

### Hinzugefügt
- **Bilinguale Sequenzdiagramme & Schnellnavigation**: Interaktives bilinguales Mermaid-Sequenzdiagramm (`sequenceDiagram` mit `autonumber` und strikt gequoteten Kanten- und Knotentexten) in `README.md` und `README_de.md` implementiert; 12-teilige Schnellnavigation mit 1:1 Ankerparität ergänzt.
- **Lokales Marketing- und Discoverability-Register**: `MARKETING-LOG.txt` im Repo-Root mit 4 Ziel-Personas (DPO/CISO, Diagnostik- und Förderberichts-Entwickler, Compliance-Audit-Ingenieure, Autonome KI-Agenten-Architekten), Discoverability-Keywords, Verzeichnis-Empfehlungen (Awesome-Listen, LibHunt, PyPI) und 3 Integrations-Blueprints angelegt.
- **Governance- und Laufzeit-Invarianten**: 8 formale Systeminvarianten (`INV-FORGE-01` bis `INV-FORGE-08`) in beiden READMEs und `llms.txt` dokumentiert und vertraglich abgesichert.
- **Geschwister-Repositories & Ökosystem-Matrix**: Tabellarische Vernetzung zu `anonymizer`, `foerderplaner`, `worksheet-generator`, `coma`, `usmc` und `open-bricks` in beiden READMEs verankert.
- **Erweiterte Vertragstest-Suite**: 5 neue Contract-Tests in `tests/test_metadata.py` (erweiterte PEP 621 URLs, Marketing-Log-Validierung, Sequenzdiagramm-Syntax, Invarianten-Präsenz, bilinguale Ankerparität und Badges); Test-Suite auf 43 Tests erweitert (100% grün).

### Geändert
- **PEP 621 Standard-Metadaten**: `pyproject.toml` um `Security`, `Marketing Log`, `Parent Organization` (`ellmos-ai`) und `Umbrella Ecosystem` (`open-bricks`) URLs sowie zusätzliche Discoverability-Keywords (`template-engine`, `local-first`, `privacy-by-design`, `json-schema`) erweitert.
- **Badge- & Dokumentations-Parität**: Shields.io Badges in `README.md` und `README_de.md` auf 43 passed Tests, Ruff Code-Style, llms.txt ready, Organisation ellmos-ai und Dach open-bricks synchronisiert.
- **Version Bump**: Version in `pyproject.toml` und `report_forge/__init__.py` auf `1.1.6` angehoben.

## [1.1.5] - 2026-09-10

### Hinzugefügt
- **Vertragstest-Suite**: Neue Vertragstest-Suite in `tests/test_metadata.py` mit 8 Contract-Tests (PEP 621 Metadaten, `.gitignore`-Hygiene, CI-Matrix-Spezifikation, Stale-Workflow, `SECURITY.md`-Präsenz & SLA, bilinguale README-Parität, Versionsparität, Schema- und Vorlagen-Invarianz).
- **GitHub Actions Stale-Workflow**: Automatisiertes Schließen inaktiver Issues und PRs via `.github/workflows/stale.yml`.
- **Bilinguale Sicherheitsrichtlinie**: `SECURITY.md` mit Local-First Zero-Egress Prinzipien, Fail-Closed Anonymisierungsgarantie, verbindlicher 48h-Reaktions-SLA und 5-Werktage-Triage-Zusage.
- **PEP 621 URLs & Linter**: Erweiterung von `pyproject.toml` um `Documentation`, `Issues`, `Changelog` URLs, `requires-python = ">=3.10"`, `ruff` als Test-Dependency sowie `[tool.ruff]` Konfiguration.

### Geändert
- **CI-Matrix-Härtung**: `.github/workflows/tests.yml` mit Concurrency (`cancel-in-progress: true`), Ruff Code-Style-Check und Bytecode-Kompilierungsprüfung (`compileall`) gehärtet.
- **Code-Hygiene**: Unbenutzte Imports in `report_forge/inbox.py` (`field`) und `tests/test_smoke.py` (`DEFAULT_TEMPLATE_PATH`) entfernt (`ruff check` 100% sauber).
- **Gitignore-Härtung**: Multi-Host-Sync-Konflikte (`*-conflict-*`, `*.sync-*`), Multi-Agent-Locks (`LOCK`, `LOCK.*`, `*.lock`, `LOCK*.txt`), Caches (`.ruff_cache/`, `.coverage`, `htmlcov/`, `wheelhouse/`) und Editor-Backups in `.gitignore` aufgenommen.
- **Dokumentations- und Badge-Parität**: `README.md` und `README_de.md` mit 38 passed Tests, Security-Badge und Sicherheitsabschnitt synchronisiert; `llms.txt` aktualisiert.
- **Version Bump**: Version in `pyproject.toml` und `report_forge/__init__.py` auf `1.1.5` angehoben.

## [1.1.4] - 2026-07-30

### Hinzugefügt
- **Bilinguale Dokumentation**: Deutsche Dokumentation (`README_de.md`) angelegt, Sprach-Umschalter (`[English](README.md) | [Deutsch](README_de.md)`) in `README.md` & `README_de.md` ergänzt.
- **Pytest Status Badge**: Shields.io Badge für 22 bestandene Tests (`22 passed`) integriert.

### Geändert
- **Verification Timestamp**: `llms.txt` Last-Checked Datum auf 2026-07-30 aktualisiert.
- **Version Bump**: `pyproject.toml` Version auf 1.1.4 angehoben.

## [1.1.3] - 2026-07-27

### Hinzugefügt
- **GitHub Actions CI Workflow**: Automated Multi-Python Matrix Testing (Python 3.10, 3.11, 3.12) under `.github/workflows/tests.yml`.
- **CI Build Status Badge**: Status-Badge in `README.md` integriert.

### Geändert
- **Verification Timestamp**: `llms.txt` Last-Checked Datum auf 2026-07-27 aktualisiert.
- **Version Bump**: `pyproject.toml` Version auf 1.1.3 angehoben.

## [1.1.2] - 2026-07-25

### Hinzugefügt
- **PEP 621 `pyproject.toml`**: Standardkonfiguration für Paket-Metadaten, PyPI-Packaging und `pytest`-Pfade.
- **Mermaid-Architekturdiagramm**: Visuelle Darstellung der 3-Phasen-Pipeline (`prepare` → LLM → `finish`) in `README.md`.
- **GFM LLM-Callout**: Strukturierte KI-/Agenten-Hinweisbox in `README.md`.

### Geändert
- **Verification Timestamp**: `llms.txt` Last-Checked Datum auf 2026-07-25 aktualisiert.

## [1.1.1] - 2026-07-24

### Hinzugefügt
- **Maschinenlesbares `llms.txt`**: Im Root-Verzeichnis angelegt für KI-Agenten, RAG-Indexierung und Crawler.
- **Badges & Schnellübersicht**: Shields.io Status-Badges und tabellarische Merkmalsübersicht in `README.md` integriert.

### Geändert
- **Dokumentations-Hygiene**: Nutzerführung und Schnellstart-Beispiele in `README.md` überarbeitet und gegliedert.

## [1.1.0] - 2026-07-23

### Hinzugefügt
- **Batch-Inbox & Veröffentlichung**: `output_dir` (Publish-Copy mit Zeitstempel-Kollisionsschutz) und `inbox_dir` (Batch-Runner `process-inbox`) hinzugefügt.
- **Kern-/Overlay-Trennung**: Erstes autonomes Release als domänen-neutraler Pipeline-Kern.

## [1.0.0] - 2026-07-23

### Hinzugefügt
- Initiales Release aus `education/foerderplaner`.
