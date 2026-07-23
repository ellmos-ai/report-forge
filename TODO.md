# TODO

## Herkunft / Nächste Schritte

- [x] Kern aus foerderplaner-Skill extrahiert und generalisiert
  (2026-07-23): workflow.py (ReportWorkflow, mode=anonymized/plain),
  document_extraction.py, render_utils.py, schema_service.py,
  services/word_template_service.py (unverändert, war bereits generisch),
  services/pdf_processor.py (Stub, unverändert), services/document_pipeline.py
  (generalisiert -- Dokumenttyp-Registry domänen-neutral, Default nicht in
  ReportWorkflow verdrahtet, siehe Docstring dort), generator.py
  (generische Referenz-Implementierung + render_generic()).
- [x] 8 Kern-Smoke-Tests grün (tests/test_smoke.py).
- [ ] Namens-Kurzcheck: "report-forge" auf GitHub/npm/PyPI auf Kollisionen
  prüfen (nicht blockierend für die Erstveröffentlichung).
- [ ] Release-Gates (Lizenz-/Privacy-Scan, CI) analog worksheet-generator
  vor tatsächlicher Public-Stellung durchlaufen.
- [ ] Optional: document_pipeline.py (Prioritäts-/Kategorisierungs-
  Pipeline) tatsächlich als alternativer Extraktionspfad in
  ReportWorkflow.prepare() verdrahten (aktuell nur eigenständig nutzbar,
  Default bleibt document_extraction.extract_all_sources).
- [ ] CLI-getpass-Hänger unter Git Bash/umgeleitetem stdin (siehe SKILL.md
  "Bekannte Probleme") sauber fixen (TTY-Erkennung + Fallback).
