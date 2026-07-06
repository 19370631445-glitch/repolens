# RepoLens

RepoLens is an early-stage, open-source CLI for understanding unfamiliar code repositories.

The approved v0.1 direction is a bounded pipeline that will eventually analyze a public GitHub repository and generate a `PROJECT_MAP.md`. This initial skeleton does not clone repositories or call an LLM yet.

## Current status

The placeholder command prints the planned pipeline:

1. Validate GitHub URL
2. Clone repository
3. Scan files
4. Analyze structure
5. Summarize with LLM
6. Generate PROJECT_MAP.md

No target repository code is downloaded or executed in this version.

## Requirements

- Python 3.11 or newer
- `pip`

## Local installation

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

Install RepoLens and its test dependency:

```bash
python -m pip install -e ".[dev]"
```

## Usage

Run the placeholder CLI with a public GitHub URL:

```bash
repolens analyze https://github.com/example/project
```

The command currently prints stages only. Real URL validation, cloning, scanning, analysis, LLM calls, and report generation are deliberately left for later milestones.

## Tests

```bash
python -m pytest
```

## Project documents

- `PRD.md` — product scope and requirements
- `TECH_DESIGN.md` — approved architecture and security boundaries
- `ROADMAP.md` — v0.1 milestones and future direction

## License

MIT

