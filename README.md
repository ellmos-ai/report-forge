# report-forge

Domänen-neutraler Kern für anonymisierbare Berichts-Pipelines: Quelldokumente
extrahieren → LLM-Prompt gegen ein konfigurierbares JSON-Schema erzeugen →
Word-Vorlage mit dem LLM-Ergebnis befüllen. Anonymisierung ist über
`mode="anonymized"`/`mode="plain"` schaltbar.

Siehe `SKILL.md` für die vollständige Dokumentation (Anonymisierungs-Modi,
Dependency-Injection-Punkte, Platzhalter-Konvention, bekannte Probleme).

## Installation

```bash
pip install -r requirements.txt  # python-docx, jsonschema; anonymizer-Modul optional
```

## Schnellstart (mode="plain", ohne Anonymisierung)

```python
from report_forge.workflow import ReportWorkflow

workflow = ReportWorkflow()
prepared = workflow.prepare(
    source_folder="quelle/", work_root="sitzungen/", mode="plain",
)
# -> prepared.prompt_path enthält den fertigen LLM-Prompt

# ... externes LLM aufrufen, Ergebnis als JSON in
#     prepared.session_dir / "data_bundled" / "report.json" ablegen ...

finished = workflow.finish(
    session_dir=prepared.session_dir,
    llm_json_path=prepared.session_dir / "data_bundled" / "report.json",
    output_folder="fertig/bericht.docx",
)
```

Für `mode="anonymized"` (Default) sind zusätzlich `real_name`,
`birth_date` und `password` bei `prepare()` sowie `password` bei
`finish()` erforderlich; das anonymizer-Modul (>=0.2.5) muss auffindbar
sein (siehe `SKILL.md`).

## Publish-Schritt & Abholort (output_dir / inbox_dir)

Optionale `config.json`/`config.local.json`-Schlüssel `output_dir`
(kopiert fertige Berichte zusätzlich dorthin) und `inbox_dir`
(Abholort für den idempotenten Batch-Befehl `process-inbox`). Details,
Kollisionsschutz und die **Cloud-Sync-Warnung** für `output_dir`: siehe
`SKILL.md`, Abschnitt "Publish-Schritt (output_dir) und
Abholort-Konvention (inbox_dir)".

```bash
python -m report_forge process-inbox --work sitzungen/ --mode plain --dry-run
```

## Tests

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q
```

## Lizenz

MIT, siehe `LICENSE`.
