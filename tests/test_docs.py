from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_example_project_map_exists_and_is_linked_from_readme() -> None:
    example_path = ROOT / "examples" / "PROJECT_MAP.example.md"
    readme_path = ROOT / "README.md"

    assert example_path.exists()

    example_text = example_path.read_text(encoding="utf-8")
    required_sections = [
        "## Project Overview",
        "## How to Read This Report",
        "## Recommended Reading Order",
        "## Technology Stack",
        "## Important Files",
        "## Lightweight Relationships",
        "## Inferred Data Flow",
        "## Analysis Scope and Limitations",
    ]
    for section in required_sections:
        assert section in example_text
    assert "Mock summary" not in example_text
    assert "may imports" not in example_text
    assert "may invokes-likely" not in example_text

    readme_text = readme_path.read_text(encoding="utf-8")
    assert "examples/PROJECT_MAP.example.md" in readme_text


def test_gitignore_ignores_generated_report_but_not_example_report() -> None:
    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    gitignore_lines = {
        line.strip()
        for line in gitignore_text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    assert "PROJECT_MAP.md" in gitignore_lines
    assert "examples/PROJECT_MAP.example.md" not in gitignore_lines


def test_release_polish_documents_exist_and_are_linked() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    expected_paths = [
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "docs/RELEASE_CHECKLIST.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/analysis_quality_issue.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
    ]

    for relative_path in expected_paths:
        assert (ROOT / relative_path).exists()

    assert "CONTRIBUTING.md" in readme_text
    assert "CHANGELOG.md" in readme_text
    assert "examples/PROJECT_MAP.example.md" in readme_text
    assert "Roadmap" in readme_text
    assert "Who is this for?" in readme_text
    assert "OpenAI provider sends selected repository snippets to OpenAI" in readme_text
    assert "Mock provider stays local and does not call OpenAI" in readme_text
    assert "Python 3.11+" in readme_text
    assert "Git installed" in readme_text


def test_pyproject_release_metadata_is_reasonable() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["name"] == "repolens"
    assert project["version"] == "0.1.1"
    assert project["requires-python"] == ">=3.11"
    assert "typer>=0.12,<1" in project["dependencies"]
    assert "pytest>=8,<9" in project["optional-dependencies"]["dev"]
    assert "openai>=1,<2" in project["optional-dependencies"]["openai"]
