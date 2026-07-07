# RepoLens Release Checklist

Use this checklist before publishing a RepoLens release.

## 1. Version and Metadata

- [ ] Confirm `pyproject.toml` version is correct.
- [ ] Confirm `src/repolens/__init__.py` version matches.
- [ ] Confirm package metadata is accurate.
- [ ] Confirm README install commands are current.

## 2. Documentation

- [ ] Review `README.md`.
- [ ] Review `CHANGELOG.md`.
- [ ] Review `CONTRIBUTING.md`.
- [ ] Review `examples/PROJECT_MAP.example.md`.
- [ ] Confirm `PROJECT_MAP.md` generated reports are ignored by git.

## 3. Tests

- [ ] Run `python -m pytest`.
- [ ] Confirm no test requires network access.
- [ ] Confirm no test requires a real `OPENAI_API_KEY`.

## 4. Install Check

- [ ] Create a clean virtual environment.
- [ ] Run `python -m pip install -e ".[dev]"`.
- [ ] Run `repolens --help`.
- [ ] Run `repolens analyze --help`.

## 5. Mock Provider Smoke Test

- [ ] Run RepoLens against a small public GitHub repository:

```bash
repolens analyze https://github.com/pallets/markupsafe --provider mock
```

- [ ] Confirm `PROJECT_MAP.md` is generated.
- [ ] Confirm report includes limitations and inference labels.

## 6. Optional OpenAI Smoke Test

- [ ] Install OpenAI optional dependency:

```bash
python -m pip install -e ".[dev,openai]"
```

- [ ] Set `OPENAI_API_KEY`.
- [ ] Run:

```bash
repolens analyze https://github.com/pallets/markupsafe --provider openai --model gpt-4.1-mini
```

- [ ] Confirm API key is not printed.
- [ ] Confirm `PROJECT_MAP.md` is generated.

## 7. Git Release

- [ ] Ensure the working tree contains only intended changes.
- [ ] Commit release changes.
- [ ] Create an annotated tag:

```bash
git tag -a v0.1.2 -m "RepoLens v0.1.2"
```

- [ ] Push commits and tag.

Do not publish to PyPI until the project maintainer explicitly decides to do so.
