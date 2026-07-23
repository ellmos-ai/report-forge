---
name: report-forge
description: Domänen-neutraler Kern für anonymisierbare Berichts-Pipelines -- extrahiert Quelldokumente (Word/PDF/Text/Excel/Mail), erzeugt daraus einen LLM-Prompt gegen ein konfigurierbares JSON-Schema und befüllt eine Word-Vorlage mit dem LLM-Ergebnis. Anonymisierung ist schaltbar (mode="anonymized" über das optionale anonymizer-Modul >=0.2.5, oder mode="plain" ohne). Nutze dieses Modul als KERN für eigene Berichts-Skills/-Domänen (z.B. Förderberichte, Gutachten, Prüfberichte) -- es liefert keinen fertigen Bericht, sondern die Pipeline-Mechanik. Domänenspezifisches Schema, Word-Vorlage und Prompt-Inhalt liefert das jeweilige Overlay.
---

# report-forge -- Berichts-Pipeline-Kern

Generalisierter Kern, extrahiert aus dem privaten Skill `education/foerderplaner`
(Kern/Overlay-Umbau, 2026-07-23). Liefert die domänen-neutrale Mechanik für
Drei-Phasen-Berichts-Pipelines:

1. **prepare** -- Quelldokumente lesen, optional anonymisieren, LLM-Prompt
   atomar in einem Sitzungsverzeichnis ablegen.
2. **Externes LLM** -- außerhalb dieses Moduls; liest ausschließlich den
   Prompt und liefert schema-konformes JSON zurück.
3. **finish** -- JSON validieren, Word-Vorlage befüllen, optional
   de-anonymisieren, atomar lokal veröffentlichen.

## Anonymisierung: schaltbar

- `mode="anonymized"` (Default): nutzt das externe, optionale
  **anonymizer-Modul** (`.MODULES/.DOMAINS/anonymizer`, Version >=0.2.5
  empfohlen) über `ANONYMIZER_MODULE_PATH`/Aufwärtssuche/OneDrive-Fallback.
  Fehlt das Modul, bricht `prepare()`/`finish()` **fail-closed** mit
  klarer Fehlermeldung ab -- kein stiller Klartext-Fallback.
- `mode="plain"`: keine Anonymisierung. Nur für nachweislich unkritische
  Quelldaten (z.B. rein technische Inhalte ohne Personenbezug). Jeder
  `prepare(mode="plain")`-Aufruf gibt eine Warnung zurück.

## Dependency-Injection

`ReportWorkflow.__init__` nimmt vier Erweiterungspunkte:

- `anonymizer_factory`/`deanonymizer_factory`/`key_path_resolver`: nur für
  `mode="anonymized"` -- Default lazy-importiert das anonymizer-Modul.
- `generator_factory`: MUSS ein Objekt liefern mit
  `.extract_sources(folder) -> str`, `.build_prompt(text, schema_name) -> str`,
  `.fill_report(data, template_path, output_path) -> RenderResult`.
  Der Kern liefert `report_forge.generator.ReportGenerator` als
  funktionierenden, domänen-neutralen Default (nutzt das Beispielschema/
  -template). **Ein Overlay liefert hier normalerweise seine eigene,
  domänenspezifische Implementierung** (eigener Prompt-Inhalt, eigenes
  Word-Vorlagen-Layout).

## Platzhalter-Konvention der Word-Vorlage

`services/word_template_service.py` (domänen-neutral, unverändert aus dem
foerderplaner-Skill übernommen) unterstützt:

- `{{PLATZHALTER}}` -- einfache Text-Ersetzung in Absätzen, Tabellenzellen,
  Header/Footer (auch über mehrere Word-internen Runs verteilt).
- `{CODE-Feld}` in Tabellenzeilen (z.B. `{D350-Ziel}`, `{D350-Ist}`) --
  `fill_icf_placeholders_and_cleanup()` füllt passende Platzhalter und
  löscht Zeilen ohne Daten. Trotz des Methodennamens (Herkunft: ICF-
  Domäne) ist der Mechanismus generisch: `CODE` ist ein beliebiger
  String-Schlüssel, `Feld` ein beliebiger Datenfeld-Name.
- Generische Tabellen-Befüllung über `fill_table_rows(table, data_rows,
  column_mapping, template_row_index=1)`: kopiert eine Vorlagenzeile pro
  Datensatz (siehe `report_forge/generator.py::render_generic` für ein
  Minimalbeispiel mit dem neutralen `findings`-Feld).
- Checkboxen (`☐`/`☒` sowie Word-Content-Control-Checkboxen) über
  `set_checkbox(doc, label_contains, checked)`.

`fill_template()`-artige Business-Logik (welches Feld auf welchen
Platzhalter/welche Tabellenzeile abgebildet wird) ist bewusst NICHT Teil
des Kerns -- das ist die eigentliche Domänenlogik und gehört ins Overlay
(siehe `render_generic()` als minimales, aber lauffähiges Beispiel).

## Publish-Schritt (output_dir) und Abholort-Konvention (inbox_dir)

Zwei optionale Konfigurationsschlüssel in `config.json`/`config.local.json`
(Auflösung: CLI-Argument > `config.local.json` > `config.json` > nicht
gesetzt = Verhalten wie bisher, siehe `report_forge/config.py`):

- **`output_dir`**: Nach erfolgreichem `finish()` wird das fertige Dokument
  zusätzlich per Kopie dorthin veröffentlicht (`publish_copy()` in
  `workflow.py`). Das Session-/`output_folder`-Original bleibt
  unverändert bestehen -- der Publish-Schritt ist ein reiner Zusatz.
  Kollisionsschutz: existiert im Ziel bereits eine Datei gleichen Namens,
  wird `_JJJJMMTT-HHMM` angehängt; der Ordner wird bei Bedarf angelegt.
  **WARNUNG:** Zeigt `output_dir` auf einen Cloud-Sync-Pfad (OneDrive,
  Dropbox, Google Drive, ...), liegt die Klartext-Ablage der fertigen,
  de-anonymisierten Berichte dort in der **Verantwortung des Nutzers**
  -- dieses Modul trifft dazu keine Entscheidung und warnt nicht
  automatisch zur Laufzeit.
- **`inbox_dir`**: Abholort für den Batch-Befehl `process-inbox` /
  `report_forge.inbox.process_inbox()`. Jeder direkte Unterordner von
  `inbox_dir` gilt als eigene Quell-Akte und wird durch `prepare()`
  geschickt. **Kein Daemon/Watcher** -- der Befehl ist idempotent (Marker
  `.processed` je erfolgreich verarbeitetem Unterordner) und dafür
  gedacht, von einer Automation (Scheduled Task, Cron) periodisch selbst
  aufgerufen zu werden. Bei `mode="anonymized"` braucht jeder Unterordner
  zusätzlich eine `.identity.json` (`{"real_name": ..., "birth_date":
  ...}`, niemals einchecken/loggen) -- fehlt sie, wird der Unterordner
  mit Fehler übersprungen statt eines stillen Klartext-Fallbacks. Ein
  gemeinsames `password` (z.B. via `REPORT_FORGE_INBOX_PASSWORD`-Env für
  automatisierte Läufe, da `getpass` bei umgeleitetem stdin hängt) gilt
  für den gesamten Lauf.

## Neutrales Beispiel

`schemas/schema.example.json` + `templates/example_template.docx`
(selbst gebaut, `_tools/build_example_template.py`, keine Bilder) +
`examples/example_report.json` demonstrieren den vollen Zyklus ohne jede
Domänenannahme. Siehe `examples/README.md`.

## Bekannte Probleme

- CLI (`python -m report_forge prepare`/`finish`) hängt unter Windows/Git
  Bash bzw. bei umgeleitetem stdin: `getpass.getpass()` liest via `msvcrt`
  direkt von der Konsole und ignoriert Pipe/Heredoc-Eingaben. Workaround:
  `ReportWorkflow.prepare()`/`.finish()` direkt über die Python-API
  aufrufen (identischer Codepfad).

## Herkunft

Extrahiert aus `education/foerderplaner` (privater Skill) im Rahmen des
dort dokumentierten Kern/Overlay-Umbaus (`TODO.md`, Abschnitt
"Kern/Overlay-Umbau"). Der Overlay behält domänenspezifisches Schema
(`foerderbericht.json`), Word-Vorlage, `.WISSEN`-Anbindung und
Agent-Prompts (ICF-Katalog) und importiert diesen Kern.

## Dateien

```
report-forge/
├── report_forge/            # Python-Paket: workflow, generator, services,
│                             #   document_extraction, render_utils, schema_service, cli
├── schemas/schema.example.json
├── templates/example_template.docx
├── examples/                # Ein synthetisches Beispiel (Input + Output-Anleitung)
├── tests/test_smoke.py
├── _tools/build_example_template.py
├── config.json / config.local.example.json
└── TODO.md
```
