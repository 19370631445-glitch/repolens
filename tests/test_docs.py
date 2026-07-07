from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_example_project_map_exists_and_is_linked_from_readme() -> None:
    example_path = ROOT / "examples" / "PROJECT_MAP.example.md"
    readme_path = ROOT / "README.md"

    assert example_path.exists()

    example_text = example_path.read_text(encoding="utf-8")
    required_sections = [
        "## Project Overview",
        "## Technology Stack",
        "## Important Files",
        "## Lightweight Relationships",
        "## Inferred Data Flow",
        "## Analysis Scope and Limitations",
    ]
    for section in required_sections:
        assert section in example_text

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
