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
