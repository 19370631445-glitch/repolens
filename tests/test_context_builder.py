"""Tests for bounded LLM context construction."""

from pathlib import Path

from repolens.analyzer import AnalysisResult, RankedFile, Relationship, analyze_repository
from repolens.context_builder import (
    ContextBuilder,
    ContextLimits,
    RepositoryMetadata,
    build_context,
)
from repolens.scanner import RepositoryScanner


def test_context_reads_only_included_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET_TOKEN=bad\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\x00binary")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)
    result = build_context(_metadata(), scan_result, analysis)
    all_context = _all_batch_text(result.batches)

    assert any(file.path == "README.md" for file in result.context_files)
    assert "SECRET_TOKEN=bad" not in all_context
    assert "\x00binary" not in all_context
    assert all(file.path != ".env" for file in result.context_files)
    assert all(file.path != "image.png" for file in result.context_files)


def test_context_respects_max_file_characters(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("abcdefghijklmnopqrstuvwxyz", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)
    result = build_context(
        _metadata(),
        scan_result,
        analysis,
        limits=ContextLimits(max_characters_per_file=5, max_total_context_characters=10_000),
    )

    context_file = _context_file(result, "README.md")
    assert context_file.content == "abcde"
    assert context_file.truncated is True
    assert context_file.truncation_reason == "max_characters_per_file"
    assert "Truncated context file: README.md" in result.limitations


def test_context_respects_max_total_context_characters(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("a" * 500, encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)
    result = build_context(
        _metadata(),
        scan_result,
        analysis,
        limits=ContextLimits(max_total_context_characters=300),
    )

    assert result.total_context_characters <= 300
    assert result.limitations


def test_context_records_total_budget_truncation(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("a" * 1_000, encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)
    result = build_context(
        _metadata(),
        scan_result,
        analysis,
        limits=ContextLimits(max_total_context_characters=500),
    )

    assert result.truncated_files_count >= 1 or any(
        "Truncated" in limitation for limitation in result.limitations
    )


def test_context_output_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("import src.utils\n", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("VALUE = 1\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)

    first = build_context(_metadata(), scan_result, analysis)
    second = build_context(_metadata(), scan_result, analysis)

    assert first == second


def test_context_paths_are_repository_relative(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)
    result = build_context(_metadata(), scan_result, analysis)

    assert result.context_files
    assert result.context_files[0].path == "src/app.py"
    assert str(tmp_path) not in result.context_files[0].path


def test_context_file_snippets_include_untrusted_delimiters_and_metadata(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)
    result = build_context(_metadata(), scan_result, analysis)
    rendered = result.context_files[0].render()

    assert "REPOLENS_UNTRUSTED_REPOSITORY_FILE" in rendered
    assert 'path="src/app.py"' in rendered
    assert 'language="Python"' in rendered
    assert 'analysis_mode="source"' in rendered
    assert 'truncated="false"' in rendered


def test_context_includes_structured_batches(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    analysis = AnalysisResult(
        technologies=[],
        ranked_files=[RankedFile(path="README.md", score=100, reasons=["docs"])],
        relationships=[
            Relationship(
                source_path="README.md",
                target="src/app.py",
                relationship_type="references",
                confidence="low",
                evidence="src/app.py",
                reason="test relationship",
            )
        ],
    )
    scan_result = RepositoryScanner().scan(tmp_path)

    result = ContextBuilder().build(_metadata(), scan_result, analysis)
    batch_names = [batch.name for batch in result.batches]

    assert batch_names == [
        "repository_overview",
        "technology_findings",
        "directory_tree_file_inventory",
        "important_files",
        "relationship_context",
        "limitations_context",
    ]
    assert "README.md -> src/app.py" in _all_batch_text(result.batches)


def test_metadata_only_lock_file_content_is_omitted(tmp_path: Path) -> None:
    (tmp_path / "package-lock.json").write_text(
        '{"veryLargeLockFile": true}',
        encoding="utf-8",
    )

    scan_result = RepositoryScanner().scan(tmp_path)
    analysis = analyze_repository(scan_result)
    result = build_context(_metadata(), scan_result, analysis)
    context_file = _context_file(result, "package-lock.json")

    assert context_file.analysis_mode == "metadata"
    assert "content intentionally omitted" in context_file.content
    assert "veryLargeLockFile" not in context_file.content


def _metadata() -> RepositoryMetadata:
    return RepositoryMetadata(
        owner="example",
        repo="demo",
        clone_url="https://github.com/example/demo.git",
        commit_sha="abc123",
    )


def _all_batch_text(batches) -> str:
    return "\n".join(batch.content for batch in batches)


def _context_file(result, path: str):
    return next(file for file in result.context_files if file.path == path)
