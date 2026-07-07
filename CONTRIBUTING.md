# Contributing to RepoLens

Thanks for helping improve RepoLens. The project is intentionally beginner-friendly and CLI-first for v0.1.

## Local Setup

Clone the repository, then create a virtual environment:

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

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Optional OpenAI provider dependency:

```bash
python -m pip install -e ".[dev,openai]"
```

## Running Tests

Run the full test suite:

```bash
python -m pytest
```

Tests must not require network access or a real `OPENAI_API_KEY`.

## v0.1 Project Constraints

Please keep v0.1 small and maintainable.

Do not add these in v0.1:

- Web UI
- Authentication
- Database
- Full AST engine
- Autonomous agent loop
- Target repository dependency installation
- Execution of target repository code

The v0.1 goal is a safe local CLI that analyzes public GitHub repositories and writes `PROJECT_MAP.md`.

## Good First Contributions

- Improve README clarity.
- Add small scanner fixtures.
- Improve skip-rule documentation.
- Add deterministic tests for technology detection.
- Improve report wording.
- Add examples for common project shapes.

## Proposing Analysis Quality Improvements

Analysis improvements are easiest to review when they are small and evidence-based.

When proposing a change, please include:

1. A short description of the repository pattern.
2. Example files or a small fixture.
3. Expected RepoLens behavior.
4. A deterministic test.
5. Any safety considerations.

Prefer lightweight heuristics before adding new dependencies. If a rule might produce false positives, include confidence levels or clear evidence paths.

## Pull Request Checklist

Before opening a pull request:

- Run `python -m pytest`.
- Update docs if behavior changes.
- Keep changes scoped to one idea.
- Avoid network-dependent tests.
- Avoid committing generated `PROJECT_MAP.md`.

## Security Notes

RepoLens treats analyzed repositories as untrusted input. Contributions should preserve these rules:

- Do not execute repository code.
- Do not import repository modules.
- Do not install repository dependencies.
- Do not print secrets or API keys.
- Keep file paths repository-relative in reports and logs.
