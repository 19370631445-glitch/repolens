"""Tests for deterministic technology detection and file ranking."""

from pathlib import Path

from repolens.analyzer import analyze_repository, detect_technologies, rank_files
from repolens.scanner import RepositoryScanner


def test_detects_python_project_and_python_frameworks(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["fastapi", "typer", "pydantic"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
""",
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text("Flask\npytest\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    technologies = detect_technologies(scan_result)
    by_name = {technology.name: technology for technology in technologies}

    assert by_name["Python"].confidence == "high"
    assert "pyproject.toml" in by_name["Python"].evidence_paths
    assert by_name["FastAPI"].evidence_paths == ["pyproject.toml"]
    assert by_name["Typer"].evidence_paths == ["pyproject.toml"]
    assert by_name["Pydantic"].evidence_paths == ["pyproject.toml"]
    assert by_name["Flask"].evidence_paths == ["requirements.txt"]
    assert set(by_name["pytest"].evidence_paths) == {"requirements.txt"}
    assert by_name["pytest config"].evidence_paths == ["pyproject.toml"]
    assert by_name["Ruff"].evidence_paths == ["pyproject.toml"]


def test_detects_package_json_dependencies(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        """
{
  "dependencies": {
    "react": "^18.0.0",
    "next": "^14.0.0",
    "express": "^4.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
""",
        encoding="utf-8",
    )
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    technologies = detect_technologies(scan_result)
    by_name = {technology.name: technology for technology in technologies}

    assert by_name["JavaScript/Node.js"].evidence_paths == ["package.json"]
    assert by_name["TypeScript"].evidence_paths == ["tsconfig.json"]
    assert by_name["React"].evidence_paths == ["package.json"]
    assert by_name["Next.js"].evidence_paths == ["package.json"]
    assert by_name["Vite"].evidence_paths == ["package.json"]
    assert by_name["Express"].evidence_paths == ["package.json"]


def test_detects_ci_and_config_files(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (tmp_path / "mypy.ini").write_text("[mypy]\n", encoding="utf-8")
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    technologies = detect_technologies(scan_result)
    by_name = {technology.name: technology for technology in technologies}

    assert by_name["GitHub Actions"].evidence_paths == [".github/workflows/ci.yml"]
    assert by_name["Docker"].evidence_paths == ["Dockerfile"]
    assert by_name["Docker Compose"].evidence_paths == ["docker-compose.yml"]
    assert by_name["mypy"].evidence_paths == ["mypy.ini"]
    assert by_name["pytest config"].evidence_paths == ["pytest.ini"]


def test_technology_findings_include_evidence_paths_and_reasons(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0.0"}}',
        encoding="utf-8",
    )

    scan_result = RepositoryScanner().scan(tmp_path)
    technologies = detect_technologies(scan_result)

    assert technologies
    assert all(technology.evidence_paths for technology in technologies)
    assert all(technology.reason for technology in technologies)
    assert all(technology.confidence in {"high", "medium", "low"} for technology in technologies)


def test_ranking_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("console.log('hello')\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)

    first = rank_files(scan_result)
    second = rank_files(scan_result)

    assert first == second


def test_readme_manifest_and_entry_points_rank_high(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "random.txt").write_text("notes\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    ranked = rank_files(scan_result)
    by_path = {file.path: file for file in ranked}

    top_paths = [file.path for file in ranked[:3]]
    assert "src/main.py" in top_paths
    assert "README.md" in top_paths
    assert "package.json" in top_paths
    assert by_path["README.md"].score > by_path["random.txt"].score
    assert by_path["package.json"].score > by_path["random.txt"].score
    assert by_path["src/main.py"].score > by_path["random.txt"].score


def test_lock_files_rank_lower_than_source_and_readme(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 3}\n', encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    ranked = rank_files(scan_result)
    by_path = {file.path: file for file in ranked}

    assert by_path["package-lock.json"].score < by_path["README.md"].score
    assert by_path["package-lock.json"].score < by_path["src/app.py"].score
    assert "metadata-only lock file" in by_path["package-lock.json"].reasons


def test_analyze_repository_returns_technologies_and_ranked_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)

    assert analysis.technologies
    assert analysis.ranked_files
