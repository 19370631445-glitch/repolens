# RepoLens

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Status alpha](https://img.shields.io/badge/status-alpha-orange)

Understand unfamiliar GitHub repositories in minutes with an AI-assisted `PROJECT_MAP.md`.

RepoLens is a CLI-first, open-source repository understanding tool for developers who need to quickly orient themselves inside a new, inherited, or open-source codebase. Give RepoLens a public GitHub repository URL, and it produces a traceable Markdown map with project overview, technology evidence, important files, lightweight relationships, inferred data flow, and known limitations.

> v0.1 is intentionally small: safe local analysis first, no hosting required, and Mock LLM as the default provider.

## Who is this for?

- Developers onboarding to an unfamiliar repository.
- Maintainers reviewing an inherited or legacy codebase.
- Open-source contributors deciding where to start reading.
- Builders who want a local CLI workflow before adding heavier tooling.

## Who is this not for?

- Security audits or compliance reviews.
- Precise call graphs or runtime tracing.
- Private/proprietary repository analysis without explicit approval.
- Large-scale code intelligence platforms with databases, vector search, or hosted Web UI.

## Why RepoLens?

Reading an unfamiliar repository often starts with the same questions:

- What does this project do?
- Which files should I read first?
- What technologies and frameworks does it use?
- How do the main modules appear to relate?
- What are the limits of this automated analysis?

RepoLens turns those first-pass questions into a local `PROJECT_MAP.md` that you can read, share, and verify against the source code.

## Current Status

- v0.1 local pipeline works end-to-end for public GitHub repositories.
- Mock mode is for testing the pipeline and does not call OpenAI.
- OpenAI mode is for useful natural-language summaries.
- Static analysis works in both Mock and OpenAI modes.
- JavaScript/TypeScript and Python receive the most targeted heuristics. Other languages receive generic directory/file-level analysis.

## Features

- Python 3.11+ CLI: `repolens analyze <github-url>`
- Public GitHub HTTPS URL validation
- Shallow clone with `git clone --depth 1`
- Safe repository scanning with skip rules for dependencies, build output, binaries, secrets, and symlinks
- Deterministic technology detection from manifests and config files
- Explainable important-file ranking
- Lightweight Python and JavaScript/TypeScript relationship extraction
- Bounded context building with untrusted repository content delimiters
- Mock LLM summaries by default
- Optional OpenAI provider
- Markdown report generation to `PROJECT_MAP.md`

## Prerequisites

- Python 3.11+
- Git installed and available on your `PATH`
- Internet access for cloning public GitHub repositories

## Quick Start: Mock Provider

Mock provider is the safest way to try RepoLens. It exercises the local pipeline and does not call OpenAI.

### User install

From a local clone of this repository:

```bash
python -m venv .venv
python -m pip install .
```

On Windows PowerShell, activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Analyze a small public Python repository:

```bash
repolens analyze https://github.com/pallets/markupsafe --provider mock
```

Write to a custom output path:

```bash
repolens analyze https://github.com/pallets/markupsafe --provider mock --output PROJECT_MAP.md
```

Output:

```text
PROJECT_MAP.md
```

### Contributor install

Use this if you want to run tests or work on RepoLens itself:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pytest
```

## Example Output Preview

RepoLens generates a Markdown reading map. A report starts with guidance like this:

```md
## Recommended Reading Order

1. `src/app.py` - score 125. Common application entry point; source file under src/ or app/.
2. `README.md` - score 100. Project overview and usage notes.
3. `pyproject.toml` - score 85. Dependency and tooling metadata.

## Inferred Data Flow

- Inferred: `src/app.py` likely imports routing definitions from `src/routes.py`.
- Inferred: `Dockerfile` may start the app through `src/app.py`.
```

See [examples/PROJECT_MAP.example.md](examples/PROJECT_MAP.example.md) for a fuller sample report.

## OpenAI Usage

OpenAI mode is intended for more useful natural-language summaries than Mock mode.

Install the optional OpenAI dependency:

```bash
python -m pip install -e ".[dev,openai]"
```

Set `OPENAI_API_KEY`.

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

macOS or Linux:

```bash
export OPENAI_API_KEY="your-api-key"
```

Run with OpenAI:

```bash
repolens analyze https://github.com/pallets/markupsafe --provider openai
```

Choose a model explicitly:

```bash
repolens analyze https://github.com/pallets/markupsafe --provider openai --model gpt-4.1-mini
```

OpenAI API usage may cost money. Start with a small repository when testing.

### OpenAI privacy warning

- Mock provider stays local and does not call OpenAI.
- OpenAI provider sends selected repository snippets to OpenAI for summarization.
- Do not use OpenAI mode on private or proprietary repositories unless you are allowed to share selected code snippets with OpenAI.
- RepoLens never executes model-generated commands.

## What the Report Includes

- Project Overview
- How to Read This Report
- Recommended Reading Order
- Repository Metadata
- Technology Stack
- Directory / File Inventory
- Important Files
- Lightweight Relationships
- Inferred Data Flow
- Analysis Scope and Limitations
- Generated By RepoLens

## Safety

- RepoLens does not execute target repository code.
- RepoLens does not import target repository modules.
- RepoLens does not install target repository dependencies.
- RepoLens skips common secrets, private keys, `.env` files, binary/media files, generated folders, and dependency folders.
- Repository content is treated as untrusted data and wrapped with explicit delimiters before summarization.
- Model output is never used to control the pipeline or execute commands.

## Limitations

- RepoLens uses lightweight heuristics, not a full AST engine.
- Relationships are not precise call graphs.
- Inferred data flow is static inference, not runtime tracing.
- Mock LLM summaries are deterministic placeholders for testing the pipeline.
- OpenAI-powered summaries may be incomplete or inaccurate and should be verified against source code.
- v0.1 focuses on public GitHub repositories, Python, and JavaScript/TypeScript.

## Roadmap

- v0.1: CLI release with safe scanning, deterministic analysis, Mock/OpenAI providers, and `PROJECT_MAP.md`.
- v0.1.1: First-impression polish, clearer README, better sample output, and stronger safety warnings.
- v0.2: Better analysis quality, richer examples, improved language/framework coverage, and report polish.
- v1.0: A more mature repository-understanding workflow while preserving safety, traceability, and local-first defaults.

See [ROADMAP.md](ROADMAP.md) for more detail.

## Contributing

Contributions are welcome, especially:

- Better technology detection rules
- Safer and clearer scanner filters
- Improved importance-ranking heuristics
- Higher-quality report wording
- Small fixture repositories for analysis-quality tests

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Development

Run tests:

```bash
python -m pytest
```

Pytest uses a project-local temp directory:

```text
.tmp/pytest
```

## Project Documents

- [PRD.md](PRD.md)
- [TECH_DESIGN.md](TECH_DESIGN.md)
- [ROADMAP.md](ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)

## License

MIT
