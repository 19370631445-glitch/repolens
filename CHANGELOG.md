# Changelog

All notable changes to RepoLens will be documented in this file.

This project follows a lightweight changelog style for the early v0.x phase.

## Unreleased

- Continue improving first-run clarity, report usefulness, and analysis quality.

## v0.1.1 - Planned

First-impression and trust polish for GitHub visitors.

### Improved

- Replaced placeholder-style sample report text with realistic explanations.
- Added a `How to Read This Report` section to generated `PROJECT_MAP.md`.
- Moved `Recommended Reading Order` near the top of generated reports.
- Improved inferred data-flow wording to use natural hypothesis language.
- Clarified Mock vs OpenAI provider expectations in the README.
- Added explicit OpenAI privacy warnings.
- Split README install instructions into user and contributor paths.
- Added prerequisites, positioning, badges, and an output preview.

## v0.1.0 - Planned

Initial CLI-first release.

### Added

- `repolens analyze <github-url>` command.
- Public GitHub HTTPS URL validation and normalization.
- Shallow clone into a safe temporary workspace.
- Repository scanner with conservative file filters and resource limits.
- Technology detection for Python and JavaScript/TypeScript projects.
- Explainable important-file ranking.
- Lightweight Python and JavaScript/TypeScript relationship extraction.
- Context builder for bounded LLM summarization.
- Deterministic Mock LLM provider.
- Optional OpenAI provider.
- `PROJECT_MAP.md` report composer.
- Example report at `examples/PROJECT_MAP.example.md`.

### Safety

- Target repository code is not executed, imported, built, or tested.
- Common secrets, private keys, binary files, dependency folders, and build outputs are skipped.
- Repository content is treated as untrusted data.

### Known Limitations

- Relationship extraction is heuristic, not a precise call graph.
- Inferred data flow is static inference, not runtime tracing.
- Mock LLM summaries are placeholders.
- OpenAI summaries should be verified against source code.
