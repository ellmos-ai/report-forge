# Changelog

Alle relevanten Änderungen an `report-forge` werden in dieser Datei dokumentiert.

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
