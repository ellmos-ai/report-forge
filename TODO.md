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
  Default bleibt document_extraction.extract_all_sources). TASKPLAN 1891.
- [ ] CLI-getpass-Hänger unter Git Bash/umgeleitetem stdin (siehe SKILL.md
  "Bekannte Probleme") sauber fixen (TTY-Erkennung + Fallback). TASKPLAN 1892.

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

## TASKWRITER-RECHECK 2026-08-02 — report-forge

Kanonischer Clone: `C:\_Local_DEV\repos\report-forge`, Branch `main`,
HEAD `355acb5ff1abe41b384a0d1e3a00925e6ac86215`, sauber und synchron zu
`origin/main` (`https://github.com/ellmos-ai/report-forge.git`); keine
`LOCK.user*`- oder `*WORKSTATION-LG*`-Datei gefunden. Es gibt keine
projektbezogenen TASKPLAN-Aufgaben vor diesem Recheck.

Die beiden expliziten offenen Punkte wurden als TASKPLAN 1891
(`DOCUMENT-PIPELINE`, medium/large/local) und 1892
(`CLI-NONINTERACTIVE`, high/medium/local) formalisiert. Zusätzlich sind die
belegten CI-/Packaging- und Dependency-Metadaten-Lücken als 1893
(`PACKAGE-CI`, medium/medium/local) und 1894
(`DEPENDENCY-CONTRACT`, medium/medium/local) erfasst. Jede Aufgabe enthält
Quelle, Soll/Ist-Ableitung, Definition of Done, Prüfweg und Blocker.

Keine Aufgabe wurde ausgeführt; kein Build, Test, Commit, Push, Publish,
Upload oder Änderung an anonymizer-/Cloud-Daten vorgenommen.
