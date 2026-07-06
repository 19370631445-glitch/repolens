"""Tests for the RepoLens command-line interface."""

from typer.testing import CliRunner

from repolens.cli import app

runner = CliRunner()


def test_analyze_command_exists() -> None:
    """The analyze command should run and print the planned pipeline."""
    result = runner.invoke(
        app,
        ["analyze", "https://github.com/example/project"],
    )

    assert result.exit_code == 0
    assert "1. Validate GitHub URL" in result.stdout
    assert "6. Generate PROJECT_MAP.md" in result.stdout
