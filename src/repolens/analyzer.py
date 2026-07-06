"""Deterministic technology detection and importance ranking.

Milestone 2B intentionally stays lightweight:
- detect technologies from manifest/config evidence;
- rank scanned files with explainable path-based rules;
- do not execute repository code;
- do not build a full AST or extract relationships yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import tomllib

from repolens.scanner import ScanResult, ScannedFile


@dataclass(frozen=True)
class TechnologyFinding:
    """A deterministic technology finding with traceable evidence."""

    name: str
    category: str
    confidence: str
    evidence_paths: list[str]
    reason: str


@dataclass(frozen=True)
class RankedFile:
    """A scanned file ranked by explainable importance rules."""

    path: str
    score: int
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisResult:
    """Output of deterministic analysis before relationship extraction or LLM use."""

    technologies: list[TechnologyFinding]
    ranked_files: list[RankedFile]


class RepositoryAnalyzer:
    """Analyze scanned repository metadata deterministically."""

    def analyze(self, scan_result: ScanResult) -> AnalysisResult:
        return AnalysisResult(
            technologies=detect_technologies(scan_result),
            ranked_files=rank_files(scan_result),
        )


def analyze_repository(scan_result: ScanResult) -> AnalysisResult:
    """Convenience wrapper for deterministic repository analysis."""
    return RepositoryAnalyzer().analyze(scan_result)


def analyze_structure(scan_result: ScanResult) -> AnalysisResult:
    """Backward-compatible wrapper for the current flat module layout."""
    return analyze_repository(scan_result)


def detect_technologies(scan_result: ScanResult) -> list[TechnologyFinding]:
    """Detect common technologies from included manifest/config files."""
    index = _ScanIndex(scan_result)
    findings: list[TechnologyFinding] = []

    _detect_python(index, findings)
    _detect_javascript_typescript(index, findings)
    _detect_node_frameworks(index, findings)
    _detect_python_frameworks(index, findings)
    _detect_ci_and_config(index, findings)

    return sorted(findings, key=lambda finding: (finding.category, finding.name))


def rank_files(scan_result: ScanResult) -> list[RankedFile]:
    """Rank included files with deterministic, explainable rules."""
    ranked_files: list[RankedFile] = []

    for scanned_file in scan_result.included_files:
        score = 0
        reasons: list[str] = []
        path = scanned_file.path
        lower_path = path.lower()
        file_name = Path(path).name.lower()

        if _is_readme(file_name):
            score += 100
            reasons.append("README/documentation overview")
        elif _is_documentation_path(lower_path):
            score += 55
            reasons.append("documentation file")

        if _is_manifest_or_config(path):
            score += 85
            reasons.append("manifest or configuration file")

        if _is_common_entry_point(path):
            score += 80
            reasons.append("common application entry point")

        if lower_path.startswith(("src/", "app/")):
            score += 45
            reasons.append("source file under src/ or app/")

        if lower_path.startswith(("tests/", "test/", "examples/", "example/")):
            score += 30
            reasons.append("test or example file")

        if scanned_file.analysis_mode == "metadata":
            score -= 35
            reasons.append("metadata-only lock file")

        if scanned_file.size_bytes > 750_000:
            score -= 30
            reasons.append("large file kept below top priority")

        if not reasons:
            score += 10
            reasons.append("included source file")

        ranked_files.append(RankedFile(path=path, score=max(score, 0), reasons=reasons))

    return sorted(ranked_files, key=lambda file: (-file.score, file.path))


class _ScanIndex:
    """Small helper around ScanResult paths and safe manifest reads."""

    def __init__(self, scan_result: ScanResult) -> None:
        self.root_path = scan_result.root_path.resolve()
        self.files_by_path = {file.path: file for file in scan_result.included_files}
        self.paths = set(self.files_by_path)

    def has(self, path: str) -> bool:
        return path in self.paths

    def matching(self, pattern: str) -> list[str]:
        return sorted(path for path in self.paths if _matches_pattern(path, pattern))

    def first_existing(self, candidates: list[str]) -> str | None:
        for candidate in candidates:
            if self.has(candidate):
                return candidate
        return None

    def read_text(self, relative_path: str, max_bytes: int = 200_000) -> str:
        if relative_path not in self.paths:
            return ""

        full_path = (self.root_path / relative_path).resolve()
        try:
            full_path.relative_to(self.root_path)
        except ValueError:
            return ""

        try:
            data = full_path.read_bytes()[:max_bytes]
        except OSError:
            return ""

        return data.decode("utf-8", errors="ignore")


def _detect_python(index: _ScanIndex, findings: list[TechnologyFinding]) -> None:
    evidence = _existing_paths(
        index,
        ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
    )
    if evidence:
        findings.append(
            TechnologyFinding(
                name="Python",
                category="language",
                confidence="high",
                evidence_paths=evidence,
                reason="Python packaging or dependency files are present.",
            )
        )


def _detect_javascript_typescript(
    index: _ScanIndex,
    findings: list[TechnologyFinding],
) -> None:
    js_evidence = _existing_paths(
        index,
        ["package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"],
    )
    if js_evidence:
        findings.append(
            TechnologyFinding(
                name="JavaScript/Node.js",
                category="runtime",
                confidence="high",
                evidence_paths=js_evidence,
                reason="Node.js package manifest or lock file is present.",
            )
        )

    ts_evidence = _existing_paths(index, ["tsconfig.json"])
    if ts_evidence:
        findings.append(
            TechnologyFinding(
                name="TypeScript",
                category="language",
                confidence="high",
                evidence_paths=ts_evidence,
                reason="TypeScript configuration file is present.",
            )
        )


def _detect_node_frameworks(index: _ScanIndex, findings: list[TechnologyFinding]) -> None:
    package_json_path = "package.json"
    dependencies = _read_package_json_dependencies(index, package_json_path)
    if not dependencies:
        return

    dependency_rules = {
        "react": ("React", "framework", "React is listed in package.json dependencies."),
        "next": ("Next.js", "framework", "Next.js is listed in package.json dependencies."),
        "vite": ("Vite", "framework", "Vite is listed in package.json dependencies."),
        "express": ("Express", "framework", "Express is listed in package.json dependencies."),
    }

    for dependency_name, (name, category, reason) in dependency_rules.items():
        if dependency_name in dependencies:
            findings.append(
                TechnologyFinding(
                    name=name,
                    category=category,
                    confidence="high",
                    evidence_paths=[package_json_path],
                    reason=reason,
                )
            )


def _detect_python_frameworks(index: _ScanIndex, findings: list[TechnologyFinding]) -> None:
    dependency_evidence = _read_python_dependency_evidence(index)
    dependency_rules = {
        "fastapi": ("FastAPI", "framework"),
        "flask": ("Flask", "framework"),
        "django": ("Django", "framework"),
        "typer": ("Typer", "framework"),
        "pydantic": ("Pydantic", "library"),
        "pytest": ("pytest", "testing"),
    }

    for dependency_name, (name, category) in dependency_rules.items():
        evidence_paths = dependency_evidence.get(dependency_name, [])
        if evidence_paths:
            findings.append(
                TechnologyFinding(
                    name=name,
                    category=category,
                    confidence="high",
                    evidence_paths=sorted(evidence_paths),
                    reason=f"{name} appears in Python dependency configuration.",
                )
            )


def _detect_ci_and_config(index: _ScanIndex, findings: list[TechnologyFinding]) -> None:
    workflow_paths = index.matching(".github/workflows/*.yml") + index.matching(
        ".github/workflows/*.yaml"
    )
    if workflow_paths:
        findings.append(
            TechnologyFinding(
                name="GitHub Actions",
                category="ci",
                confidence="high",
                evidence_paths=workflow_paths,
                reason="GitHub Actions workflow files are present.",
            )
        )

    if index.has("Dockerfile"):
        findings.append(
            TechnologyFinding(
                name="Docker",
                category="container",
                confidence="high",
                evidence_paths=["Dockerfile"],
                reason="Dockerfile is present.",
            )
        )

    docker_compose_paths = _existing_paths(
        index,
        ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"],
    )
    if docker_compose_paths:
        findings.append(
            TechnologyFinding(
                name="Docker Compose",
                category="container",
                confidence="high",
                evidence_paths=docker_compose_paths,
                reason="Docker Compose configuration file is present.",
            )
        )

    ruff_evidence = _ruff_evidence(index)
    if ruff_evidence:
        findings.append(
            TechnologyFinding(
                name="Ruff",
                category="tooling",
                confidence="high",
                evidence_paths=ruff_evidence,
                reason="Ruff configuration or dependency evidence is present.",
            )
        )

    mypy_evidence = _mypy_evidence(index)
    if mypy_evidence:
        findings.append(
            TechnologyFinding(
                name="mypy",
                category="tooling",
                confidence="high",
                evidence_paths=mypy_evidence,
                reason="mypy configuration or dependency evidence is present.",
            )
        )

    pytest_evidence = _pytest_config_evidence(index)
    if pytest_evidence:
        findings.append(
            TechnologyFinding(
                name="pytest config",
                category="testing",
                confidence="high",
                evidence_paths=pytest_evidence,
                reason="pytest configuration file is present.",
            )
        )


def _read_package_json_dependencies(index: _ScanIndex, package_json_path: str) -> set[str]:
    text = index.read_text(package_json_path)
    if not text:
        return set()

    try:
        package_data = json.loads(text)
    except json.JSONDecodeError:
        return set()

    dependencies: set[str] = set()
    for dependency_section in (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ):
        values = package_data.get(dependency_section, {})
        if isinstance(values, dict):
            dependencies.update(str(name).lower() for name in values)

    return dependencies


def _read_python_dependency_evidence(index: _ScanIndex) -> dict[str, set[str]]:
    dependency_names = {"fastapi", "flask", "django", "typer", "pydantic", "pytest", "ruff", "mypy"}
    evidence: dict[str, set[str]] = {name: set() for name in dependency_names}

    for path in ("requirements.txt", "pyproject.toml", "setup.cfg", "setup.py"):
        if not index.has(path):
            continue

        text = _dependency_text_for_path(path, index.read_text(path)).lower()
        for dependency_name in dependency_names:
            if re.search(rf"(^|[^a-z0-9_-]){re.escape(dependency_name)}([^a-z0-9_-]|$)", text):
                evidence[dependency_name].add(path)

    return evidence


def _dependency_text_for_path(path: str, text: str) -> str:
    if path != "pyproject.toml":
        return text

    try:
        pyproject_data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return text

    dependency_values: list[str] = []

    project_data = pyproject_data.get("project", {})
    if isinstance(project_data, dict):
        dependency_values.extend(_string_values(project_data.get("dependencies")))
        optional_dependencies = project_data.get("optional-dependencies", {})
        if isinstance(optional_dependencies, dict):
            for values in optional_dependencies.values():
                dependency_values.extend(_string_values(values))

    tool_data = pyproject_data.get("tool", {})
    if isinstance(tool_data, dict):
        poetry_data = tool_data.get("poetry", {})
        if isinstance(poetry_data, dict):
            dependency_values.extend(_keys(poetry_data.get("dependencies")))
            group_data = poetry_data.get("group", {})
            if isinstance(group_data, dict):
                for group in group_data.values():
                    if isinstance(group, dict):
                        dependency_values.extend(_keys(group.get("dependencies")))

    dependency_groups = pyproject_data.get("dependency-groups", {})
    if isinstance(dependency_groups, dict):
        for values in dependency_groups.values():
            dependency_values.extend(_string_values(values))

    return "\n".join(dependency_values)


def _string_values(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _keys(value: object) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key in value]
    return []


def _ruff_evidence(index: _ScanIndex) -> list[str]:
    evidence = _existing_paths(index, ["ruff.toml", ".ruff.toml"])
    pyproject_text = index.read_text("pyproject.toml").lower()
    if "[tool.ruff" in pyproject_text:
        evidence.append("pyproject.toml")

    dependency_evidence = _read_python_dependency_evidence(index)
    evidence.extend(dependency_evidence.get("ruff", []))
    return sorted(set(evidence))


def _mypy_evidence(index: _ScanIndex) -> list[str]:
    evidence = _existing_paths(index, ["mypy.ini", ".mypy.ini"])
    pyproject_text = index.read_text("pyproject.toml").lower()
    setup_cfg_text = index.read_text("setup.cfg").lower()
    if "[tool.mypy" in pyproject_text:
        evidence.append("pyproject.toml")
    if "[mypy" in setup_cfg_text:
        evidence.append("setup.cfg")

    dependency_evidence = _read_python_dependency_evidence(index)
    evidence.extend(dependency_evidence.get("mypy", []))
    return sorted(set(evidence))


def _pytest_config_evidence(index: _ScanIndex) -> list[str]:
    evidence = _existing_paths(index, ["pytest.ini"])
    pyproject_text = index.read_text("pyproject.toml").lower()
    setup_cfg_text = index.read_text("setup.cfg").lower()
    if "[tool.pytest" in pyproject_text:
        evidence.append("pyproject.toml")
    if "[tool:pytest" in setup_cfg_text:
        evidence.append("setup.cfg")
    return sorted(set(evidence))


def _existing_paths(index: _ScanIndex, paths: list[str]) -> list[str]:
    return [path for path in paths if index.has(path)]


def _matches_pattern(path: str, pattern: str) -> bool:
    return Path(path).match(pattern)


def _is_readme(file_name: str) -> bool:
    return file_name in {"readme", "readme.md", "readme.rst", "readme.txt"}


def _is_documentation_path(lower_path: str) -> bool:
    return lower_path.startswith(("docs/", "doc/")) or lower_path.endswith(
        (".md", ".rst")
    )


def _is_manifest_or_config(path: str) -> bool:
    lower_path = path.lower()
    file_name = Path(lower_path).name
    return (
        file_name in _HIGH_PRIORITY_MANIFESTS_AND_CONFIGS
        or lower_path.startswith(".github/workflows/")
        or file_name.startswith("docker-compose.")
        or file_name.startswith("compose.")
    )


def _is_common_entry_point(path: str) -> bool:
    lower_path = path.lower()
    file_name = Path(lower_path).name

    if file_name in _COMMON_ENTRY_POINT_NAMES:
        return True

    return lower_path in {
        "src/main.py",
        "src/app.py",
        "src/index.js",
        "src/index.ts",
        "src/main.js",
        "src/main.ts",
        "app/main.py",
        "app/app.py",
        "app/index.js",
        "app/index.ts",
    }


_HIGH_PRIORITY_MANIFESTS_AND_CONFIGS = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "tsconfig.json",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "ruff.toml",
    ".ruff.toml",
    "mypy.ini",
    ".mypy.ini",
    "pytest.ini",
}

_COMMON_ENTRY_POINT_NAMES = {
    "__main__.py",
    "main.py",
    "app.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "index.js",
    "index.ts",
    "server.js",
    "server.ts",
    "main.js",
    "main.ts",
}
