"""Execute the documented plain workflow using only synthetic local data."""

import json
import re
import shlex
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("guide", ["README.md", "README_de.md", "README_es.md"])
def test_plain_quickstart_renders_synthetic_report(guide, tmp_path, monkeypatch):
    text = (ROOT / guide).read_text(encoding="utf-8")
    snippet = re.search(r"```python\n(.*?)```", text, re.DOTALL).group(1)
    first, remaining = snippet.split("# Phase 2:", 1)
    final = remaining[remaining.index("# Phase 3:"):]
    monkeypatch.chdir(tmp_path)
    for name in ("source_docs", "quell_dokumente"):
        source = tmp_path / name
        source.mkdir()
        (source / "note.txt").write_text("Synthetic technical content.", encoding="utf-8")
    namespace = {}
    exec(compile(first, guide, "exec"), namespace)
    prepared = namespace["prepared"]
    data = json.loads((ROOT / "examples/example_report.json").read_text(encoding="utf-8"))
    (prepared.session_dir / "data_bundled/report.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    exec(compile(final, guide, "exec"), namespace)
    assert namespace["finished"].success
    assert namespace["finished"].output_folder.is_file()


@pytest.mark.parametrize("guide", ["README.md", "README_de.md", "README_es.md"])
def test_documented_cli_commands_with_synthetic_session(guide, tmp_path, monkeypatch):
    from report_forge.cli import main

    text = (ROOT / guide).read_text(encoding="utf-8")
    commands = [shlex.split(line)[3:] for line in text.splitlines()
                if line.startswith("python -m report_forge ")]
    prepare = next(command for command in commands if command[0] == "prepare")
    finish = next(command for command in commands if command[0] == "finish")
    monkeypatch.chdir(tmp_path)
    source = Path(prepare[prepare.index("--source") + 1])
    source.mkdir()
    (source / "note.txt").write_text("Synthetic technical content.", encoding="utf-8")
    assert main(prepare) == 0
    session = next(tmp_path.rglob("session.json")).parent
    data = session / "data_bundled/report.json"
    data.write_bytes((ROOT / "examples/example_report.json").read_bytes())
    finish[finish.index("--session") + 1] = str(session)
    finish[finish.index("--json") + 1] = str(data)
    assert main(finish) == 0
    assert Path(finish[finish.index("--output") + 1]).is_file()
    assert main(next(command for command in commands if command[0] == "--info")) == 0
