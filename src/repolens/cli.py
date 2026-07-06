"""Command-line interface for RepoLens."""

from typing import Annotated

import typer

from repolens.analyzer import AnalysisResult, analyze_repository
from repolens.errors import RepoLensError
from repolens.git_source import clone_repository, validate_github_url
from repolens.scanner import ScanResult, scan_files

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
    """Run the first RepoLens pipeline stages for a public GitHub repository."""
    try:
        typer.echo(f"1. {PIPELINE_STAGES[0]}")
        validate_github_url(github_url)

        typer.echo(f"2. {PIPELINE_STAGES[1]}")

        with clone_repository(github_url) as repository:
            typer.echo("Repository cloned successfully.")
            typer.echo(f"Owner: {repository.owner}")
            typer.echo(f"Repo: {repository.repo}")
            if repository.commit_sha:
                typer.echo(f"Commit: {repository.commit_sha}")
            else:
                typer.echo("Commit: unavailable")

            typer.echo(f"3. {PIPELINE_STAGES[2]}")
            scan_result = scan_files(repository.local_path)
            _print_scan_summary(scan_result)

            typer.echo(f"4. {PIPELINE_STAGES[3]}")
            analysis_result = analyze_repository(scan_result)
            _print_analysis_summary(analysis_result)

            for step_number, stage in enumerate(PIPELINE_STAGES[4:], start=5):
                typer.echo(f"{step_number}. {stage} (placeholder)")
    except RepoLensError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _print_scan_summary(scan_result: ScanResult) -> None:
    typer.echo("Scan summary:")
    typer.echo(f"  Total files seen: {scan_result.total_files_seen}")
    typer.echo(f"  Included files: {scan_result.included_count}")
    typer.echo(f"  Skipped files: {scan_result.skipped_count}")

    if scan_result.language_counts:
        language_summary = ", ".join(
            f"{language}: {count}"
            for language, count in sorted(scan_result.language_counts.items())
        )
    else:
        language_summary = "none"
    typer.echo(f"  Detected language counts: {language_summary}")


def _print_analysis_summary(analysis_result: AnalysisResult) -> None:
    typer.echo("Detected technologies:")
    if not analysis_result.technologies:
        typer.echo("  none")
    for technology in analysis_result.technologies:
        evidence = ", ".join(technology.evidence_paths)
        typer.echo(
            f"  - {technology.name} "
            f"({technology.category}, {technology.confidence}) "
            f"[evidence: {evidence}]"
        )

    typer.echo("Top important files:")
    if not analysis_result.ranked_files:
        typer.echo("  none")
    for index, ranked_file in enumerate(analysis_result.ranked_files[:10], start=1):
        reasons = "; ".join(ranked_file.reasons)
        typer.echo(f"  {index}. {ranked_file.path} (score: {ranked_file.score}) - {reasons}")
