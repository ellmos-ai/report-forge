"""Contract and hygiene tests for report-forge repository metadata.

Verifies PEP 621 compliance, .gitignore hygiene, CI matrix configuration,
bilingual documentation parity, security policy, and schema/template contracts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_text(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    assert path.exists(), f"Expected file {relative_path} does not exist"
    return path.read_text(encoding="utf-8")


def test_gitignore_hygiene():
    """Verify .gitignore contains essential security, lock, cache, and sync patterns."""
    content = _read_text(".gitignore")
    lines = {
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.startswith("#")
    }

    required_patterns = [
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        ".ruff_cache/",
        ".coverage",
        ".env",
        "*-conflict-*",
        "*.sync-conflict-*",
        "*.sync-temp-*",
        "LOCK",
        "LOCK.*",
        "LOCK*.txt",
        "*.lock",
        "config.local.json",
        "output/",
    ]
    for pattern in required_patterns:
        assert pattern in lines, f"Missing required .gitignore pattern: {pattern}"


def test_pyproject_pep621_metadata():
    """Verify pyproject.toml adheres to PEP 621 standard metadata fields."""
    if sys.version_info >= (3, 11):
        import tomllib
        with open(REPO_ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
    else:
        import tomli as tomllib
        with open(REPO_ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)

    project = data.get("project", {})
    assert project.get("name") == "report-forge"
    assert project.get("version") == "1.1.5"
    assert "description" in project
    assert project.get("requires-python") == ">=3.10"
    assert project.get("license") == "MIT"

    # Authors
    authors = project.get("authors", [])
    assert any(a.get("name") == "Lukas Geiger" for a in authors)

    # Keywords & Classifiers
    keywords = project.get("keywords", [])
    assert "report-generation" in keywords
    assert "anonymization" in keywords
    assert "pipeline" in keywords

    classifiers = project.get("classifiers", [])
    assert "Programming Language :: Python :: 3.10" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Programming Language :: Python :: 3.12" in classifiers

    # URLs
    urls = project.get("urls", {})
    assert urls.get("Homepage") == "https://github.com/ellmos-ai/report-forge"
    assert urls.get("Repository") == "https://github.com/ellmos-ai/report-forge"
    assert urls.get("Documentation") == "https://github.com/ellmos-ai/report-forge#readme"
    assert urls.get("Issues") == "https://github.com/ellmos-ai/report-forge/issues"
    assert urls.get("Changelog") == "https://github.com/ellmos-ai/report-forge/blob/main/CHANGELOG.md"

    # Optional test dependencies
    opt_deps = project.get("optional-dependencies", {})
    assert "test" in opt_deps
    assert any("pytest" in d for d in opt_deps["test"])
    assert any("ruff" in d for d in opt_deps["test"])


def test_version_parity():
    """Verify version in report_forge.__init__ matches pyproject.toml."""
    import report_forge
    if sys.version_info >= (3, 11):
        import tomllib
        with open(REPO_ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
    else:
        import tomli as tomllib
        with open(REPO_ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)

    assert report_forge.__version__ == data["project"]["version"]


def test_ci_matrix_workflow_definition():
    """Verify GitHub Actions CI matrix tests Python 3.10, 3.11, and 3.12."""
    content = _read_text(".github/workflows/tests.yml")
    assert "name: Tests" in content
    assert "matrix:" in content
    assert '"3.10"' in content
    assert '"3.11"' in content
    assert '"3.12"' in content
    assert "cancel-in-progress: true" in content
    assert "compileall" in content
    assert "ruff check ." in content
    assert "pytest" in content


def test_stale_workflow_definition():
    """Verify GitHub Actions stale workflow is defined for issue and PR management."""
    content = _read_text(".github/workflows/stale.yml")
    assert "Stale Issues & PRs" in content
    assert "actions/stale@v9" in content
    assert "schedule:" in content


def test_security_policy_present_and_sla():
    """Verify SECURITY.md is present with 48h SLA response and contacts."""
    content = _read_text("SECURITY.md")
    assert "48 hours" in content or "48 Stunden" in content
    assert "5 business days" in content or "5 Werktagen" in content
    assert "security@open-bricks.org" in content
    assert "security@ellmos.ai" in content


def test_readme_bilingual_parity():
    """Verify presence and cross-links between English and German READMEs."""
    en_content = _read_text("README.md")
    de_content = _read_text("README_de.md")

    assert "README_de.md" in en_content
    assert "README.md" in de_content

    # Both must display the header banner
    assert "assets/banner.svg" in en_content
    assert "assets/banner.svg" in de_content


def test_schema_and_template_contracts():
    """Verify schema, template, and module path invariants."""
    import report_forge
    from report_forge.generator import DEFAULT_SCHEMA_PATH, DEFAULT_TEMPLATE_PATH
    from report_forge.schema_service import load_schema, validate_report_schema

    assert DEFAULT_SCHEMA_PATH.is_file()
    assert DEFAULT_TEMPLATE_PATH.is_file()
    assert report_forge.SCHEMAS_PATH.is_dir()
    assert report_forge.TEMPLATES_PATH.is_dir()

    schema = load_schema(DEFAULT_SCHEMA_PATH)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    example_path = REPO_ROOT / "examples" / "example_report.json"
    data = json.loads(example_path.read_text(encoding="utf-8"))
    errors = validate_report_schema(data, schema)
    assert errors == []
