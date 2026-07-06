"""Tests for the RepoLens command-line interface."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from repolens.cli import app
from repolens.git_source import ClonedRepository
from repolens.scanner import ScanResult, ScannedFile, SkippedFile

runner = CliRunner()


def test_analyze_command_exists(monkeypatch) -> None:
    """The analyze command should run and print the planned pipeline."""

    @contextmanager
    def fake_clone_repository(github_url: str) -> Iterator[ClonedRepository]:
        assert github_url == "https://github.com/example/project"
        yield ClonedRepository(
            owner="example",
            repo="project",
            clone_url="https://github.com/example/project.git",
            local_path=Path("temporary-placeholder"),
            commit_sha="abc123",
        )

    def fake_scan_files(repository_path: Path) -> ScanResult:
        assert repository_path == Path("temporary-placeholder")
        return ScanResult(
            root_path=repository_path,
            total_files_seen=3,
            included_files=[
                ScannedFile(
                    path="src/index.js",
                    size_bytes=25,
                    extension=".js",
                    is_text=True,
                    language="JavaScript",
                )
            ],
            skipped_files=[
                SkippedFile(path=".git", reason="skipped_directory"),
                SkippedFile(path="node_modules", reason="skipped_directory"),
            ],
            language_counts={"JavaScript": 1},
        )

    monkeypatch.setattr("repolens.cli.clone_repository", fake_clone_repository)
    monkeypatch.setattr("repolens.cli.scan_files", fake_scan_files)

    result = runner.invoke(
        app,
        ["analyze", "https://github.com/example/project"],
    )

    assert result.exit_code == 0
    assert "1. Validate GitHub URL" in result.stdout
    assert "2. Clone repository" in result.stdout
    assert "Owner: example" in result.stdout
    assert "Repo: project" in result.stdout
    assert "Commit: abc123" in result.stdout
    assert "3. Scan files" in result.stdout
    assert "Total files seen: 3" in result.stdout
    assert "Included files: 1" in result.stdout
    assert "Skipped files: 2" in result.stdout
    assert "Detected language counts: JavaScript: 1" in result.stdout
    assert "6. Generate PROJECT_MAP.md (placeholder)" in result.stdout
