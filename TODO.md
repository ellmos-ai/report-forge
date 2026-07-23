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
- [x] Namens-Kurzcheck "report-forge" auf GitHub/npm/PyPI: vom Operator
  geprüft (frei) und Repo `ellmos-ai/report-forge` angelegt.
- [x] Release-Gates-Stichprobe + PUBLIC-Schaltung: vom Operator erledigt,
  Registry/Katalog (41 Module) nachgezogen.
- [ ] Optional: document_pipeline.py (Prioritäts-/Kategorisierungs-
  Pipeline) tatsächlich als alternativer Extraktionspfad in
  ReportWorkflow.prepare() verdrahten (aktuell nur eigenständig nutzbar,
  Default bleibt document_extraction.extract_all_sources).
- [ ] CLI-getpass-Hänger unter Git Bash/umgeleitetem stdin (siehe SKILL.md
  "Bekannte Probleme") sauber fixen (TTY-Erkennung + Fallback).

## Feature: output_dir/inbox_dir + Publish-Schritt (2026-07-23)

- [x] `config.py`: Auflösung CLI-Argument > config.local.json >
  config.json > nicht gesetzt (`resolve_setting()`/`load_config()`).
- [x] `workflow.py`: `publish_copy()` + `ReportWorkflow.finish(...,
  output_dir=...)` -- Kopie zusätzlich nach `output_dir`, Original in
  `output_folder` bleibt unverändert, Kollisionsschutz per
  `_JJJJMMTT-HHMM`-Suffix. De-Anonymisierung selbst unangetastet
  (bleibt fail-closed lokal) -- Publish ist bewusst nachgelagert.
- [x] `inbox.py`: `process_inbox()` + CLI-Befehl `process-inbox`
  (idempotent über `.processed`-Marker, `.identity.json` für
  mode="anonymized" pflicht, `--dry-run`, kein Daemon/Watcher).
- [x] 14 neue Tests (`tests/test_output_inbox.py`), alle grün (22/22
  gesamt inkl. bestehender 8).
- [x] Cloud-Sync-Warnung für `output_dir` in `SKILL.md` + `README.md`
  dokumentiert.
