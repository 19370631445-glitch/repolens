# RepoLens

Understand unfamiliar GitHub repositories in minutes with an AI-assisted PROJECT_MAP.md.

RepoLens is an open-source, CLI-first repository understanding tool. Give it a public GitHub repository URL and it builds a local, traceable `PROJECT_MAP.md` using safe static analysis, lightweight relationship extraction, bounded context building, and the current Mock LLM summarization pipeline.

## Current Status

- v0.1 local pipeline works end-to-end for public GitHub repositories.
- Mock LLM is still the default provider, so no API key or real LLM network call is required for safe local testing.
- OpenAI provider support is available behind `--provider openai`.

## Quick Start

### Install

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install RepoLens with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

To use the OpenAI provider, install the optional OpenAI dependency too:

```bash
python -m pip install -e ".[dev,openai]"
```

### Run

Analyze a public GitHub repository:

```bash
repolens analyze https://github.com/owner/repo
```

Optionally choose the report path:

```bash
repolens analyze https://github.com/owner/repo --output PROJECT_MAP.md
```

### Output

RepoLens writes a Markdown report:

```text
PROJECT_MAP.md
```

## LLM Providers

RepoLens defaults to the deterministic Mock provider:

```bash
repolens analyze https://github.com/owner/repo --provider mock
```

To use the OpenAI provider, set `OPENAI_API_KEY` first.

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

On macOS or Linux:

```bash
export OPENAI_API_KEY="your-api-key"
```

Then run:

```bash
repolens analyze https://github.com/owner/repo --provider openai
```

You can choose a model explicitly:

```bash
repolens analyze https://github.com/owner/repo --provider openai --model gpt-4.1-mini
```

OpenAI API usage may cost money. Start with a small repository when testing.

## Example Output

See [examples/PROJECT_MAP.example.md](examples/PROJECT_MAP.example.md) for a realistic sample report based on a small mock repository.

## What RepoLens Does

1. Validates a public GitHub HTTPS repository URL.
2. Performs a shallow clone into a temporary workspace.
3. Scans files with safe filters and conservative resource limits.
4. Detects technologies from manifest and config evidence.
5. Ranks important files with explainable deterministic rules.
6. Extracts lightweight Python and JavaScript/TypeScript relationships.
7. Builds bounded context for summarization.
8. Uses the selected LLM provider to create structured summaries.
9. Generates `PROJECT_MAP.md`.

## Safety

- RepoLens does not execute target repository code.
- RepoLens does not import target repository modules.
- RepoLens skips common secrets, private keys, `.env` files, binary/media files, generated folders, and dependency folders.
- Repository content is treated as untrusted data and wrapped with explicit delimiters before summarization.
- Generated reports include limitations and inference labels.

## Limitations

- RepoLens uses lightweight heuristics, not a full AST engine.
- Relationships are not precise call graphs.
- Inferred data flow is static inference, not runtime tracing.
- Mock LLM summaries are deterministic placeholders and should be verified against source code.
- OpenAI-powered summarization requires `OPENAI_API_KEY` and may produce imperfect summaries.

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

- `PRD.md`
- `TECH_DESIGN.md`
- `ROADMAP.md`

## License

MIT
