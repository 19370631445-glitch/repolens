"""Tests for the RepoLens command-line interface."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from repolens.analyzer import AnalysisResult, RankedFile, Relationship, TechnologyFinding
from repolens.cli import app
from repolens.context_builder import ContextBuildResult, ContextFile, RepositoryMetadata
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

    def fake_analyze_repository(scan_result: ScanResult) -> AnalysisResult:
        assert scan_result.total_files_seen == 3
        return AnalysisResult(
            technologies=[
                TechnologyFinding(
                    name="JavaScript/Node.js",
                    category="runtime",
                    confidence="high",
                    evidence_paths=["package.json"],
                    reason="Node.js package manifest is present.",
                )
            ],
            ranked_files=[
                RankedFile(
                    path="src/index.js",
                    score=125,
                    reasons=["source file under src/ or app/", "common application entry point"],
                )
            ],
            relationships=[
                Relationship(
                    source_path="src/index.js",
                    target="src/app.js",
                    relationship_type="imports",
                    confidence="high",
                    evidence='import app from "./app"',
                    reason="JavaScript import pattern.",
                )
            ],
        )

    def fake_build_context(
        repository_metadata: ClonedRepository,
        scan_result: ScanResult,
        analysis_result: AnalysisResult,
    ) -> ContextBuildResult:
        assert repository_metadata.owner == "example"
        assert scan_result.total_files_seen == 3
        assert len(analysis_result.relationships) == 1
        context_file = ContextFile(
            path="src/index.js",
            language="JavaScript",
            analysis_mode="source",
            content="console.log('hello')",
            truncated=False,
            character_count=20,
        )
        return ContextBuildResult(
            repository=RepositoryMetadata(
                owner="example",
                repo="project",
                clone_url="https://github.com/example/project.git",
                commit_sha="abc123",
            ),
            batches=[],
            context_files=[context_file],
            total_context_characters=1234,
            limitations=[],
        )

    monkeypatch.setattr("repolens.cli.clone_repository", fake_clone_repository)
    monkeypatch.setattr("repolens.cli.scan_files", fake_scan_files)
    monkeypatch.setattr("repolens.cli.analyze_repository", fake_analyze_repository)
    monkeypatch.setattr("repolens.cli.build_context", fake_build_context)

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
    assert "4. Analyze structure" in result.stdout
    assert "Detected technologies:" in result.stdout
    assert "JavaScript/Node.js" in result.stdout
    assert "Top important files:" in result.stdout
    assert "src/index.js" in result.stdout
    assert "Relationship summary:" in result.stdout
    assert "Total relationships found: 1" in result.stdout
    assert "src/index.js -> src/app.js" in result.stdout
    assert "Build LLM context" in result.stdout
    assert "Context files included: 1" in result.stdout
    assert "Total context characters: 1234" in result.stdout
    assert "Truncated files: 0" in result.stdout
    assert "6. Generate PROJECT_MAP.md (placeholder)" in result.stdout
