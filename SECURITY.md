# Security Policy / Sicherheitsrichtlinie

## Supported Versions / Unterstützte Versionen

| Version | Supported / Unterstützt |
| ------- | ----------------------- |
| 1.1.x   | :white_check_mark:      |
| < 1.1   | :x:                     |

---

## English Security Policy

### Core Security & Privacy Principles

`report-forge` is a domain-neutral engine for schema-bound, anonymizable report generation pipelines. It is designed around local-first data protection and strict process isolation:

1. **Local-First Processing & Zero-Egress:**
   - Source document extraction, prompt rendering, and `.docx` generation run entirely on the local system without telemetry, tracking, or unexpected network egress.
   - The engine does not send data to cloud services autonomously; LLM calls are orchestrated outside module boundaries by the caller.

2. **Fail-Closed Privacy & Anonymization:**
   - When configured with `mode="anonymized"` (default), sensitive personal identifiers (names, dates of birth, passwords) require the `anonymizer` module (>=0.2.5).
   - If the anonymizer module or required secrets are missing, execution terminates immediately (**fail-closed**) with a descriptive error. There is no silent fallback to unredacted plaintext.

3. **Secret & Identity Protection:**
   - Identity mapping files (`.identity.json`) and local configurations (`config.local.json`, `.env`) are strictly excluded from version control via `.gitignore`.
   - Secret inputs via CLI support non-interactive environment variables (`--*-env`) without printing or echoing sensitive credentials to logs or terminals.

4. **Output Directory Collision Protection:**
   - Document exports to `output_dir` apply collision protection timestamps (`_YYYYMMDD-HHMM`) to prevent silent overwriting of prior reports.

### Reporting a Vulnerability

If you discover a security vulnerability or privacy leak in `report-forge`, please report it privately:

1. **GitHub Security Advisory (Preferred):** Open a private report at [ellmos-ai/report-forge Security Advisories](https://github.com/ellmos-ai/report-forge/security/advisories).
2. **Email Contacts:** Send vulnerability details to `security@open-bricks.org` and `security@ellmos.ai` (CC: `lukas@open-bricks.org`, `support@lukasgeiger.com`).

**Service Level Agreement (SLA):**
- **Acknowledgment:** Within 48 hours.
- **Triage & Status Assessment:** Within 5 business days.
- **Remediation & Release Coordination:** As rapidly as verified automated tests permit.

Please do not disclose potential vulnerabilities publicly in issues or pull requests.

---

## Deutsche Sicherheitsrichtlinie (German)

### Sicherheits- und Datenschutzgrundsätze

`report-forge` ist ein domänen-neutraler Kern für schemagebundene, anonymisierbare Berichts-Pipelines. Das Modul folgt strikten Grundsätzen des Datenschutzes und der Prozessisolation:

1. **Local-First Verarbeitung & Zero-Egress:**
   - Dokumenten-Extraktion, Prompt-Zusammenstellung und die Erstellung von Word-Berichten (`.docx`) erfolgen vollständig lokal ohne Drittanbieter-Telemetrie oder unerwartete Netzwerkabflüsse.
   - Das Modul sendet keine Daten autonom an Cloud-Dienste; LLM-Aufrufe erfolgen bewusst außerhalb der Modulgrenzen durch den Aufrufer.

2. **Fail-Closed Datenschutz & Anonymisierung:**
   - Im Standardmodus `mode="anonymized"` werden personenbezogene Daten über das `anonymizer`-Modul (>=0.2.5) verschlüsselt und pseudonymisiert.
   - Fehlt das Anonymisierungsmodul oder ein erforderliches Passwort, bricht der Lauf **fail-closed** sofort ab. Es findet kein stiller Rückfall auf Klartext statt.

3. **Schutz vertraulicher Daten & Identitätsdateien:**
   - Identitätszuordnungen (`.identity.json`) und lokale Konfigurationen (`config.local.json`, `.env`) sind durch `.gitignore` vor unbeabsichtigtem Commit geschützt.
   - Die CLI unterstützt nicht-interaktive Umgebungs-Variablen (`--*-env`), sodass Passwörter niemals in Konsolen-Logs oder Shell-Historien exponiert werden.

4. **Kollisionsschutz bei Veröffentlichung:**
   - Beim automatischen Kopieren nach `output_dir` schützt ein Zeitstempel-Suffix (`_JJJJMMTT-HHMM`) bestehende Berichte vor unbeabsichtigtem Überschreiben.

### Sicherheitslücke melden

Wenn Sie eine Sicherheitslücke oder einen Datenschutzmangel in `report-forge` entdecken, melden Sie dies bitte vertraulich:

1. **GitHub Security Advisory (Bevorzugt):** Erstellen Sie einen privaten Bericht unter [ellmos-ai/report-forge Security Advisories](https://github.com/ellmos-ai/report-forge/security/advisories).
2. **E-Mail-Kontakt:** Senden Sie Ihren Bericht an `security@open-bricks.org` und `security@ellmos.ai` (CC: `lukas@open-bricks.org`, `support@lukasgeiger.com`).

**Verbindliche Reaktionsfristen (SLA):**
- **Eingangsbestätigung:** Innerhalb von 48 Stunden.
- **Ersteinschätzung (Triage):** Innerhalb von 5 Werktagen.
- **Behebung:** Schnellstmöglich nach bestandener Verifikation in der Testsuite.
