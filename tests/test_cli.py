"""Tests for the RepoLens command-line interface."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from repolens.cli import app
from repolens.git_source import ClonedRepository

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

    monkeypatch.setattr("repolens.cli.clone_repository", fake_clone_repository)

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
    assert "6. Generate PROJECT_MAP.md (placeholder)" in result.stdout
