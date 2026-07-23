# Beispiel

`example_report.json` ist ein rein synthetisches Beispiel für das neutrale
Schema in `schemas/schema.example.json`. Es demonstriert, wie
`ReportGenerator.fill_report()` (report_forge/generator.py) daraus mit
`templates/example_template.docx` ein DOCX erzeugt:

```python
from report_forge.generator import ReportGenerator
import json

gen = ReportGenerator()
data = json.loads(open("examples/example_report.json", encoding="utf-8").read())
result = gen.fill_report(data, output_path="output/example_report.docx")
print(result.success, result.errors)
```

Kein Klienten-/Personenbezug -- "Beispielperson X" und alle Inhalte sind
frei erfunden.
