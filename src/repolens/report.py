"""PROJECT_MAP.md report composition."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import tempfile

from repolens.analyzer import AnalysisResult, Relationship
from repolens.context_builder import ContextBuildResult, RepositoryMetadata
from repolens.errors import ReportGenerationError
from repolens.llm import SummaryResult
from repolens.scanner import ScanResult


@dataclass(frozen=True)
class ReportInputs:
    """All deterministic and summary data needed to render PROJECT_MAP.md."""

    repository: RepositoryMetadata
    scan_result: ScanResult
    analysis_result: AnalysisResult
    context_result: ContextBuildResult
    summary_result: SummaryResult


class ReportComposer:
    """Render a stable Markdown PROJECT_MAP.md report."""

    def compose(self, inputs: ReportInputs) -> str:
        sections = [
            "# PROJECT_MAP.md",
            self._project_overview(inputs),
            self._how_to_read(inputs),
            self._recommended_reading_order(inputs),
            self._repository_metadata(inputs),
            self._technology_stack(inputs),
            self._file_inventory(inputs),
            self._important_files(inputs),
            self._relationships(inputs),
            self._inferred_data_flow(inputs),
            self._scope_and_limitations(inputs),
            self._generated_by(inputs),
        ]
        return "\n\n".join(section.rstrip() for section in sections) + "\n"

    def _project_overview(self, inputs: ReportInputs) -> str:
        project_summary = inputs.summary_result.project_summary
        lines = [
            "## Project Overview",
            "",
            _safe_text(project_summary.overview),
            "",
            "> AI-generated summaries may be inaccurate. Verify important conclusions against the source code.",
        ]
        if project_summary.evidence_paths:
            lines.extend(["", "Evidence paths:"])
            lines.extend(_bullet(path) for path in sorted(project_summary.evidence_paths))
        return "\n".join(lines)

    def _how_to_read(self, inputs: ReportInputs) -> str:
        lines = [
            "## How to Read This Report",
            "",
            "1. Start with **Project Overview** for the high-level purpose.",
            "2. Read **Recommended Reading Order** to decide where to begin in the code.",
            "3. Inspect **Important Files** for file-level responsibilities and evidence paths.",
            "4. Treat **Inferred Data Flow** as a hypothesis to verify against source code.",
        ]
        if inputs.analysis_result.ranked_files:
            lines.extend(["", "Reading-order preview:"])
            for ranked_file in inputs.analysis_result.ranked_files[:3]:
                reasons = "; ".join(_safe_text(reason) for reason in ranked_file.reasons)
                lines.append(f"- `{_safe_inline(ranked_file.path)}` - {reasons}")
        return "\n".join(lines)

    def _recommended_reading_order(self, inputs: ReportInputs) -> str:
        lines = ["## Recommended Reading Order", ""]
        if not inputs.analysis_result.ranked_files:
            lines.append("No ranked files were available.")
            return "\n".join(lines)

        for index, ranked_file in enumerate(inputs.analysis_result.ranked_files[:10], start=1):
            reasons = "; ".join(_safe_text(reason) for reason in ranked_file.reasons)
            lines.append(
                f"{index}. `{_safe_inline(ranked_file.path)}` - score {ranked_file.score}. {reasons}"
            )
        return "\n".join(lines)

    def _repository_metadata(self, inputs: ReportInputs) -> str:
        repository = inputs.repository
        scan = inputs.scan_result
        commit_sha = repository.commit_sha or "unknown"
        return "\n".join(
            [
                "## Repository Metadata",
                "",
                f"- Owner: `{_safe_inline(repository.owner)}`",
                f"- Repository: `{_safe_inline(repository.repo)}`",
                f"- Clone URL: `{_safe_inline(repository.clone_url)}`",
                f"- Commit SHA: `{_safe_inline(commit_sha)}`",
                f"- Total files seen: {scan.total_files_seen}",
                f"- Files included for analysis: {scan.included_count}",
                f"- Files skipped: {scan.skipped_count}",
            ]
        )

    def _technology_stack(self, inputs: ReportInputs) -> str:
        lines = ["## Technology Stack", ""]
        if not inputs.analysis_result.technologies:
            lines.append("No deterministic technology findings were detected.")
            return "\n".join(lines)

        for finding in inputs.analysis_result.technologies:
            evidence = ", ".join(f"`{_safe_inline(path)}`" for path in finding.evidence_paths)
            lines.append(
                f"- **{_safe_text(finding.name)}** "
                f"({_safe_text(finding.category)}, confidence: `{_safe_inline(finding.confidence)}`) "
                f"- {_safe_text(finding.reason)} Evidence: {evidence}"
            )
        return "\n".join(lines)

    def _file_inventory(self, inputs: ReportInputs) -> str:
        scan = inputs.scan_result
        lines = ["## Directory / File Inventory", "", "Language counts:"]
        if scan.language_counts:
            for language, count in sorted(scan.language_counts.items()):
                lines.append(f"- {_safe_text(language)}: {count}")
        else:
            lines.append("- none")

        lines.extend(["", "Included files:"])
        for file in sorted(scan.included_files, key=lambda item: item.path)[:100]:
            lines.append(
                f"- `{_safe_inline(file.path)}` - {_safe_text(file.language)}, "
                f"{file.size_bytes} bytes, analysis mode: `{_safe_inline(file.analysis_mode)}`"
            )

        if len(scan.included_files) > 100:
            lines.append(f"- ... {len(scan.included_files) - 100} more included files omitted.")

        skipped_counts: dict[str, int] = {}
        for skipped in scan.skipped_files:
            skipped_counts[skipped.reason] = skipped_counts.get(skipped.reason, 0) + 1
        lines.extend(["", "Skipped file reason counts:"])
        if skipped_counts:
            for reason, count in sorted(skipped_counts.items()):
                lines.append(f"- `{_safe_inline(reason)}`: {count}")
        else:
            lines.append("- none")
        return "\n".join(lines)

    def _important_files(self, inputs: ReportInputs) -> str:
        lines = ["## Important Files", ""]
        ranked_by_path = {file.path: file for file in inputs.analysis_result.ranked_files}
        if not inputs.summary_result.file_summaries:
            lines.append("No file summaries were generated.")
            return "\n".join(lines)

        for summary in inputs.summary_result.file_summaries:
            ranked = ranked_by_path.get(summary.path)
            score = f", score: {ranked.score}" if ranked else ""
            lines.append(f"### `{_safe_inline(summary.path)}`{score}")
            lines.append("")
            lines.append(_safe_text(summary.purpose))
            if ranked and ranked.reasons:
                lines.append("")
                lines.append("Ranking reasons:")
                lines.extend(_bullet(reason) for reason in ranked.reasons)
            if summary.key_symbols:
                lines.append("")
                lines.append("Key symbols:")
                lines.extend(_bullet(symbol) for symbol in summary.key_symbols)
            lines.append("")
        return "\n".join(lines).rstrip()

    def _relationships(self, inputs: ReportInputs) -> str:
        lines = ["## Lightweight Relationships", ""]
        if not inputs.analysis_result.relationships:
            lines.append("No lightweight relationships were detected.")
            return "\n".join(lines)

        for relationship in inputs.analysis_result.relationships:
            lines.append(
                f"- `{_safe_inline(relationship.source_path)}` -> `{_safe_inline(relationship.target)}` "
                f"({_safe_text(relationship.relationship_type)}, "
                f"confidence: `{_safe_inline(relationship.confidence)}`) - "
                f"{_safe_text(relationship.reason)} Evidence: `{_safe_inline(relationship.evidence)}`"
            )
        return "\n".join(lines)

    def _inferred_data_flow(self, inputs: ReportInputs) -> str:
        lines = [
            "## Inferred Data Flow",
            "",
            "**Inference notice:** This section is inferred from static file relationships and summaries. "
            "It is not a runtime trace, precise call graph, or verified execution path.",
            "",
        ]
        relationships = inputs.analysis_result.relationships
        if not relationships:
            lines.append("No inferred data-flow hints were available.")
            return "\n".join(lines)

        lines.extend(_inferred_relationship_sentence(relationship) for relationship in relationships[:20])
        return "\n".join(lines)

    def _scope_and_limitations(self, inputs: ReportInputs) -> str:
        provider_label = (
            "OpenAI LLM summaries"
            if inputs.summary_result.provider_name == "openai"
            else "Mock LLM summaries"
        )
        lines = [
            "## Analysis Scope and Limitations",
            "",
            f"- RepoLens uses lightweight static analysis and {provider_label} in this version.",
            "- Repository code was not executed, imported, built, or tested.",
            "- Skipped secret-like files, binary files, and other excluded files were not read into report context.",
            "- AI-generated summaries may be inaccurate and should be verified against source code.",
        ]
        all_limitations = list(inputs.scan_result.limitations) + list(inputs.context_result.limitations)
        if inputs.summary_result.project_summary.limitations:
            all_limitations.extend(inputs.summary_result.project_summary.limitations)

        unique_limitations = list(dict.fromkeys(all_limitations))
        if unique_limitations:
            lines.extend(["", "Recorded limitations:"])
            lines.extend(_bullet(limitation) for limitation in unique_limitations)
        return "\n".join(lines)

    def _generated_by(self, inputs: ReportInputs) -> str:
        return "\n".join(
            [
                "## Generated By RepoLens",
                "",
                "- Tool: RepoLens",
                f"- LLM provider: `{_safe_inline(inputs.summary_result.provider_name)}`",
                f"- LLM model: `{_safe_inline(inputs.summary_result.model_name)}`",
                f"- LLM requests made: {inputs.summary_result.requests_made}",
                f"- OpenAI integration: {_openai_integration_label(inputs.summary_result)}",
            ]
        )


def write_project_map(
    repository: RepositoryMetadata,
    scan_result: ScanResult,
    analysis_result: AnalysisResult,
    context_result: ContextBuildResult,
    summary_result: SummaryResult,
    output_path: Path = Path("PROJECT_MAP.md"),
) -> Path:
    """Compose and atomically write PROJECT_MAP.md."""
    inputs = ReportInputs(
        repository=repository,
        scan_result=scan_result,
        analysis_result=analysis_result,
        context_result=context_result,
        summary_result=summary_result,
    )
    content = ReportComposer().compose(inputs)
    return _atomic_write(output_path, content)


def generate_project_map(summary: ReportInputs, output_path: Path) -> Path:
    """Backward-compatible report generation wrapper."""
    content = ReportComposer().compose(summary)
    return _atomic_write(output_path, content)


def _atomic_write(output_path: Path, content: str) -> Path:
    final_path = output_path.resolve()
    final_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=final_path.parent,
            prefix=f".{final_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        temp_path.replace(final_path)
    except OSError as exc:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise ReportGenerationError(f"Could not write report to {final_path}: {exc}") from exc

    return final_path


def _safe_text(value: object) -> str:
    return escape(str(value), quote=False)


def _safe_inline(value: object) -> str:
    return str(value).replace("`", "\\`").replace("\n", " ")


def _bullet(value: object) -> str:
    return f"- {_safe_text(value)}"


def _openai_integration_label(summary_result: SummaryResult) -> str:
    if summary_result.provider_name == "openai":
        return "used in this run."
    return "not used in this run."


def _inferred_relationship_sentence(relationship: Relationship) -> str:
    source = f"`{_safe_inline(relationship.source_path)}`"
    target = f"`{_safe_inline(relationship.target)}`"
    relationship_type = str(relationship.relationship_type)
    confidence = f"confidence: `{_safe_inline(relationship.confidence)}`"

    if relationship_type == "imports":
        sentence = f"{source} likely imports or references {target}"
    elif relationship_type == "invokes-likely":
        sentence = f"{source} may invoke or start {target}"
    elif relationship_type == "configures":
        sentence = f"{source} appears to configure {target}"
    elif relationship_type == "references":
        sentence = f"{source} references {target}"
    else:
        sentence = f"{source} is related to {target} via `{_safe_inline(relationship_type)}`"

    return f"- Inferred: {sentence} ({confidence})."
