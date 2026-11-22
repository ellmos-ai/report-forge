# Contributing to report-forge / Mitwirken an report-forge

Language: [English](#english) | [Deutsch](#deutsch)

---

<a id="english"></a>
## English

Thank you for contributing to `report-forge`!

### Development Setup

```bash
python -m pip install -e ".[test,formats]"
```

### Verification Gates

Before opening a pull request, verify all local gates:

```bash
PYTHONIOENCODING=utf-8 python -m pytest -ra -q
ruff check .
python -m compileall -q .
git diff --check
```

### Architectural & Privacy Guardrails

- **Local-First & Zero-Egress (`INV-FORGE-08`)**: Do not introduce telemetry, remote API calls, or network dependencies into core extraction, schema validation, or DOCX rendering.
- **Fail-Closed Anonymization (`INV-FORGE-03`)**: `mode="anonymized"` must never fall back silently to cleartext when `anonymizer` or secrets are missing.
- **No PII in Fixtures or Tests**: Use strictly synthetic data (e.g., `Example Person` / `Beispielperson X`). Never commit `.identity.json`, `config.local.json`, or real documents.
- **Documentation Parity**: Keep `README.md`, `README_de.md`, `README_es.md`, and `llms.txt` aligned when behavior or test contracts change.

### Pull Request Process

1. Work on a dedicated feature or hygiene branch (`chore/...`, `fix/...`, `feat/...`).
2. Keep changes focused and add contract or regression tests in `tests/`.
3. Follow our [Code of Conduct](CODE_OF_CONDUCT.md) and [Security Policy](SECURITY.md).

---

<a id="deutsch"></a>
## Deutsch

Vielen Dank für dein Interesse an der Mitarbeit an `report-forge`!

### Entwicklungsumgebung

```bash
python -m pip install -e ".[test,formats]"
```

### Qualitäts- und Prüf-Gates

Vor jedem Pull Request sollten alle lokalen Prüfungen grün sein:

```bash
PYTHONIOENCODING=utf-8 python -m pytest -ra -q
ruff check .
python -m compileall -q .
git diff --check
```

### Architektur- & Datenschutz-Leitplanken

- **Local-First & Zero-Egress (`INV-FORGE-08`)**: Keine Telemetrie, keine versteckten Remote-Aufrufe und keine Netzwerkabhängigkeiten im Kern.
- **Fail-Closed Anonymisierung (`INV-FORGE-03`)**: `mode="anonymized"` darf bei fehlendem `anonymizer`-Modul oder fehlenden Secrets niemals still auf Klartext zurückfallen.
- **Keine echten Personendaten**: Ausschließlich synthetische Testdaten verwenden. Niemals `.identity.json`, `config.local.json` oder reale Dokumente committen.
- **Dokumentations-Parität**: `README.md`, `README_de.md`, `README_es.md` und `llms.txt` konsistent halten.

### Pull-Request-Ablauf

1. Auf einem eigenen Feature- oder Hygiene-Branch arbeiten (`chore/...`, `fix/...`, `feat/...`).
2. Änderungen klar abgrenzen und passende Tests in `tests/` ergänzen.
3. [Verhaltenskodex](CODE_OF_CONDUCT.md) und [Sicherheitsrichtlinie](SECURITY.md) beachten.
