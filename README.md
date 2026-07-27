# report-forge

![CI](https://github.com/ellmos-ai/report-forge/actions/workflows/tests.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-Domain--Neutral-green.svg)
![Privacy](https://img.shields.io/badge/privacy-Local--First-orange.svg)
![Status](https://img.shields.io/badge/status-released-brightgreen.svg)

> [!NOTE]
> Dieses Repository ist für KI-Agenten und automatisierte Workflows optimiert. Maschinenlesbare Spezifikationen und Integrationshinweise befinden sich in [`llms.txt`](llms.txt) sowie [`SKILL.md`](SKILL.md).

Domänen-neutraler Kern für anonymisierbare Berichts-Pipelines: Quelldokumente extrahieren → LLM-Prompt gegen ein konfigurierbares JSON-Schema erzeugen → Word-Vorlage mit dem LLM-Ergebnis befüllen. Anonymisierung ist über `mode="anonymized"` / `mode="plain"` schaltbar.

---

## 🏗️ Systemarchitektur

```mermaid
flowchart LR
    A["Quelldokumente\n(Word/PDF/Text/Excel)"] -->|prepare| B["Session Workspace\n(prompt.txt & data_bundled)"]
    B -->|External LLM| C["JSON-Response\n(report.json)"]
    C -->|finish| D["Finaler Bericht\n(.docx in output_dir)"]

    subgraph Privacy ["Datenschutz-Schicht"]
        E["anonymizer module\n(mode='anonymized')"]
    end
    E -.- B
```

---

## ⚡ Schnellübersicht

| Merkmal | Beschreibung |
|---|---|
| **Architektur** | 3-Phasen Pipeline (`prepare` → LLM → `finish`) |
| **Datenschutz** | Fail-Closed Anonymisierung (`mode="anonymized"`) via `anonymizer`-Modul (≥0.2.5) oder unverschlüsselt (`mode="plain"`) |
| **Vorlagen** | Word (`.docx`) mit `{{PLATZHALTER}}`, dynamischen Tabellenzeilen und Checkbox-Steuerung |
| **Automatisierung** | Idempotenter Batch-Runner (`process-inbox`) für periodische Hintergrundverarbeitung |
| **Output & Storage** | Local-First Veröffentlichung (`output_dir`) mit automatischem Zeitstempel-Kollisionsschutz |

---

## 📦 Installation

```bash
pip install -r requirements.txt
```
*(Optionale Anonymisierung benötigt das separat installierte `anonymizer`-Modul >=0.2.5)*

---

## 🚀 Schnellstart (mode="plain", ohne Anonymisierung)

```python
from report_forge.workflow import ReportWorkflow

workflow = ReportWorkflow()

# Phase 1: Quelldaten lesen und LLM-Prompt vorbereiten
prepared = workflow.prepare(
    source_folder="quelle/",
    work_root="sitzungen/",
    mode="plain",
)
# -> prepared.prompt_path enthält den fertigen LLM-Prompt

# Phase 2: Externes LLM aufrufen (außerhalb des Moduls)
#          Ergebnis als JSON in prepared.session_dir / "data_bundled" / "report.json" ablegen

# Phase 3: JSON-Ergebnis validieren, Word-Vorlage befüllen und Bericht finalisieren
finished = workflow.finish(
    session_dir=prepared.session_dir,
    llm_json_path=prepared.session_dir / "data_bundled" / "report.json",
    output_folder="fertig/bericht.docx",
)
```

> **Anonymisierter Modus (`mode="anonymized"`, Default):**
> Bei `prepare()` sind zusätzlich `real_name`, `birth_date` und `password` erforderlich; bei `finish()` ist `password` notwendig. Das `anonymizer`-Modul (>=0.2.5) muss vorhanden sein (siehe `SKILL.md`).

---

## 📥 Batch-Abholort (`inbox_dir`) & Publish-Schritt (`output_dir`)

Optionale Schlüssel in `config.json` oder `config.local.json`:
- **`output_dir`**: Kopiert fertige Berichte automatisch in einen zentralen Veröffentlichungsordner.
- **`inbox_dir`**: Abholort für den automatisierten Batch-Befehl `process-inbox`.

```bash
python -m report_forge process-inbox --work sitzungen/ --mode plain --dry-run
```

---

## 🧪 Tests

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q
```

---

## 📄 Lizenz

MIT, siehe [LICENSE](LICENSE).
