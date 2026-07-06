"""Command-line interface for RepoLens."""

from typing import Annotated

import typer

app = typer.Typer(
    name="repolens",
    help="Understand a public GitHub repository and generate a project map.",
    add_completion=False,
    no_args_is_help=True,
)

PIPELINE_STAGES = (
    "Validate GitHub URL",
    "Clone repository",
    "Scan files",
    "Analyze structure",
    "Summarize with LLM",
    "Generate PROJECT_MAP.md",
)


@app.callback()
def main() -> None:
    """RepoLens command group."""


@app.command()
def analyze(
    github_url: Annotated[
        str,
        typer.Argument(help="Public GitHub repository URL to analyze."),
    ],
) -> None:
    """Print the planned RepoLens analysis pipeline."""
    del github_url  # The URL will be used when repository support is implemented.

    for step_number, stage in enumerate(PIPELINE_STAGES, start=1):
        typer.echo(f"{step_number}. {stage}")
