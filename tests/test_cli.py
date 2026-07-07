"""Tests for the RepoLens command-line interface."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from repolens.analyzer import AnalysisResult, RankedFile, Relationship, TechnologyFinding
from repolens.cli import app
from repolens.context_builder import ContextBuildResult, ContextFile, RepositoryMetadata
from repolens.git_source import ClonedRepository
from repolens.llm import FileSummary, LLMUsage, ModuleSummary, ProjectSummary, SummaryResult
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

    def fake_summarize_context(context_result: ContextBuildResult) -> SummaryResult:
        assert context_result.total_context_characters == 1234
        return SummaryResult(
            file_summaries=[
                FileSummary(
                    path="src/index.js",
                    purpose="Mock file summary",
                    key_symbols=[],
                    notes=[],
                    evidence_paths=["src/index.js"],
                )
            ],
            module_summaries=[
                ModuleSummary(
                    name="src",
                    paths=["src/index.js"],
                    responsibility="Mock module summary",
                )
            ],
            project_summary=ProjectSummary(
                overview="Mock project summary",
                main_technologies=["JavaScript/Node.js"],
                important_paths=["src/index.js"],
                limitations=[],
                evidence_paths=["src/index.js"],
            ),
            usage=LLMUsage(),
            provider_name="mock",
            model_name="mock-deterministic-v0",
            requests_made=3,
        )

    def fake_write_project_map(
        repository: RepositoryMetadata,
        scan_result: ScanResult,
        analysis_result: AnalysisResult,
        context_result: ContextBuildResult,
        summary_result: SummaryResult,
        output_path: Path,
    ) -> Path:
        assert repository.owner == "example"
        assert scan_result.total_files_seen == 3
        assert len(analysis_result.relationships) == 1
        assert context_result.total_context_characters == 1234
        assert summary_result.project_summary.overview == "Mock project summary"
        assert output_path == Path("custom-map.md")
        return Path("custom-map.md").resolve()

    monkeypatch.setattr("repolens.cli.clone_repository", fake_clone_repository)
    monkeypatch.setattr("repolens.cli.scan_files", fake_scan_files)
    monkeypatch.setattr("repolens.cli.analyze_repository", fake_analyze_repository)
    monkeypatch.setattr("repolens.cli.build_context", fake_build_context)
    monkeypatch.setattr("repolens.cli.summarize_context", fake_summarize_context)
    monkeypatch.setattr("repolens.cli.write_project_map", fake_write_project_map)

    result = runner.invoke(
        app,
        ["analyze", "https://github.com/example/project", "--output", "custom-map.md"],
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
    assert "5. Summarize with LLM" in result.stdout
    assert "File summaries generated: 1" in result.stdout
    assert "Module summaries generated: 1" in result.stdout
    assert "Project summary generated: yes" in result.stdout
    assert "6. Generate PROJECT_MAP.md" in result.stdout
    assert "PROJECT_MAP.md written to:" in result.stdout
    assert "custom-map.md" in result.stdout
