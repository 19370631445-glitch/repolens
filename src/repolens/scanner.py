"""Safe repository scanner and file filters.

Milestone 2A keeps this module deterministic and beginner-friendly:
- walk a cloned repository directory;
- collect file metadata;
- skip risky, generated, binary, or oversized files;
- never execute repository code;
- never follow symlinks.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import os
from pathlib import Path

from repolens.errors import RepositoryScanError


@dataclass(frozen=True)
class ScanLimits:
    """Conservative limits for safe local repository scanning."""

    max_total_files_scanned: int = 5_000
    max_included_files: int = 500
    max_single_file_size_bytes: int = 1_000_000
    max_total_text_bytes: int = 5_000_000
    binary_probe_bytes: int = 1_024


@dataclass(frozen=True)
class ScannedFile:
    """Metadata for a file included in the scan result."""

    path: str
    size_bytes: int
    extension: str
    is_text: bool
    language: str
    analysis_mode: str = "source"


@dataclass(frozen=True)
class SkippedFile:
    """Metadata for a file or directory skipped by the scanner."""

    path: str
    reason: str
    size_bytes: int | None = None
    extension: str = ""
    is_text: bool | None = None
    language: str = "Unknown"


@dataclass(frozen=True)
class ScanResult:
    """Summary of a safe repository scan."""

    root_path: Path
    total_files_seen: int
    included_files: list[ScannedFile]
    skipped_files: list[SkippedFile]
    language_counts: dict[str, int]
    limitations: list[str] = field(default_factory=list)

    @property
    def included_count(self) -> int:
        return len(self.included_files)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_files)


class RepositoryScanner:
    """Scan a cloned repository directory without executing repository code."""

    def __init__(self, limits: ScanLimits | None = None) -> None:
        self.limits = limits or ScanLimits()

    def scan(self, repository_path: Path) -> ScanResult:
        root = repository_path.resolve()
        if not root.exists() or not root.is_dir():
            raise RepositoryScanError(
                f"Repository path does not exist or is not a directory: {repository_path}"
            )

        included_files: list[ScannedFile] = []
        skipped_files: list[SkippedFile] = []
        limitations: list[str] = []
        language_counter: Counter[str] = Counter()
        total_files_seen = 0
        total_text_bytes = 0
        stop_scanning = False

        for current_dir, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current_dir)

            safe_dir_names: list[str] = []
            for dir_name in dir_names:
                directory = current_path / dir_name
                relative_path = _relative_path(directory, root)

                if directory.is_symlink():
                    skipped_files.append(
                        SkippedFile(path=relative_path, reason="symlink_not_followed")
                    )
                    continue

                if not _is_inside_root(directory, root):
                    skipped_files.append(
                        SkippedFile(path=relative_path, reason="path_outside_repository")
                    )
                    continue

                if _should_skip_directory(dir_name):
                    skipped_files.append(
                        SkippedFile(path=relative_path, reason="skipped_directory")
                    )
                    continue

                safe_dir_names.append(dir_name)

            dir_names[:] = safe_dir_names

            for file_name in file_names:
                file_path = current_path / file_name
                relative_path = _relative_path(file_path, root)
                extension = _extension_for(file_path)
                language = guess_language(extension, file_path.name)

                if total_files_seen >= self.limits.max_total_files_scanned:
                    limitations.append(
                        f"Reached max_total_files_scanned="
                        f"{self.limits.max_total_files_scanned}; remaining files were not scanned."
                    )
                    stop_scanning = True
                    break

                total_files_seen += 1

                if file_path.is_symlink():
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason="symlink_not_followed",
                            extension=extension,
                            language=language,
                        )
                    )
                    continue

                if not _is_inside_root(file_path, root):
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason="path_outside_repository",
                            extension=extension,
                            language=language,
                        )
                    )
                    continue

                size_bytes = _safe_file_size(file_path)
                if size_bytes is None:
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason="unreadable_file_metadata",
                            extension=extension,
                            language=language,
                        )
                    )
                    continue

                skip_reason = _skip_reason_for_file(file_path)
                if skip_reason is not None:
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason=skip_reason,
                            size_bytes=size_bytes,
                            extension=extension,
                            is_text=None,
                            language=language,
                        )
                    )
                    continue

                if size_bytes > self.limits.max_single_file_size_bytes:
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason="file_too_large",
                            size_bytes=size_bytes,
                            extension=extension,
                            is_text=None,
                            language=language,
                        )
                    )
                    continue

                is_text = _is_likely_text(file_path, self.limits.binary_probe_bytes)
                if not is_text:
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason="binary_file",
                            size_bytes=size_bytes,
                            extension=extension,
                            is_text=False,
                            language=language,
                        )
                    )
                    continue

                if len(included_files) >= self.limits.max_included_files:
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason="max_included_files_reached",
                            size_bytes=size_bytes,
                            extension=extension,
                            is_text=True,
                            language=language,
                        )
                    )
                    _add_once(
                        limitations,
                        f"Reached max_included_files={self.limits.max_included_files}; "
                        "additional text files were skipped.",
                    )
                    continue

                analysis_mode = "metadata" if _is_lock_file(file_path.name) else "source"
                bytes_for_limit = 0 if analysis_mode == "metadata" else size_bytes
                if total_text_bytes + bytes_for_limit > self.limits.max_total_text_bytes:
                    skipped_files.append(
                        SkippedFile(
                            path=relative_path,
                            reason="max_total_text_bytes_reached",
                            size_bytes=size_bytes,
                            extension=extension,
                            is_text=True,
                            language=language,
                        )
                    )
                    _add_once(
                        limitations,
                        f"Reached max_total_text_bytes="
                        f"{self.limits.max_total_text_bytes}; additional source files were skipped.",
                    )
                    continue

                included = ScannedFile(
                    path=relative_path,
                    size_bytes=size_bytes,
                    extension=extension,
                    is_text=True,
                    language=language,
                    analysis_mode=analysis_mode,
                )
                included_files.append(included)
                language_counter[language] += 1
                total_text_bytes += bytes_for_limit

            if stop_scanning:
                break

        return ScanResult(
            root_path=root,
            total_files_seen=total_files_seen,
            included_files=included_files,
            skipped_files=skipped_files,
            language_counts=dict(sorted(language_counter.items())),
            limitations=limitations,
        )


def scan_files(repository_path: Path) -> ScanResult:
    """Convenience wrapper for the default repository scanner."""
    return RepositoryScanner().scan(repository_path)


def guess_language(extension: str, file_name: str = "") -> str:
    """Guess a simple language label from a file extension or known filename."""
    normalized_name = file_name.lower()
    if normalized_name in {"dockerfile"}:
        return "Dockerfile"
    if normalized_name in {"makefile"}:
        return "Makefile"

    return _LANGUAGE_BY_EXTENSION.get(extension.lower(), "Unknown")


def _should_skip_directory(directory_name: str) -> bool:
    return directory_name in _SKIPPED_DIRECTORIES


def _skip_reason_for_file(file_path: Path) -> str | None:
    name = file_path.name
    lower_name = name.lower()
    extension = _extension_for(file_path)

    if lower_name == ".env" or lower_name.startswith(".env."):
        return "secret_or_environment_file"

    if _looks_like_private_key(lower_name):
        return "private_key_file"

    if _looks_like_credential_file(lower_name):
        return "credential_like_file"

    if lower_name.endswith(".min.js") or lower_name.endswith(".min.css"):
        return "minified_file"

    if extension in _BINARY_OR_MEDIA_EXTENSIONS:
        return "binary_or_media_file"

    if extension in _ARCHIVE_EXTENSIONS:
        return "archive_file"

    return None


def _is_likely_text(file_path: Path, probe_bytes: int) -> bool:
    try:
        with file_path.open("rb") as file:
            chunk = file.read(probe_bytes)
    except OSError:
        return False

    if b"\x00" in chunk:
        return False

    return True


def _is_inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except (OSError, ValueError):
        return False
    return True


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _safe_file_size(file_path: Path) -> int | None:
    try:
        return file_path.stat().st_size
    except OSError:
        return None


def _extension_for(file_path: Path) -> str:
    suffixes = [suffix.lower() for suffix in file_path.suffixes]
    if len(suffixes) >= 2 and suffixes[-2:] in ([".tar", ".gz"], [".tar", ".bz2"], [".tar", ".xz"]):
        return "".join(suffixes[-2:])
    return file_path.suffix.lower()


def _is_lock_file(file_name: str) -> bool:
    lower_name = file_name.lower()
    return lower_name in _LOCK_FILE_NAMES or lower_name.endswith(".lock")


def _looks_like_private_key(lower_name: str) -> bool:
    return lower_name in _PRIVATE_KEY_FILE_NAMES or lower_name.endswith(
        (".pem", ".key", ".p12", ".pfx")
    )


def _looks_like_credential_file(lower_name: str) -> bool:
    credential_words = ("credential", "credentials", "secret", "secrets", "token", "password")
    if lower_name in _CREDENTIAL_FILE_NAMES:
        return True
    return any(word in lower_name for word in credential_words)


def _add_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


_SKIPPED_DIRECTORIES = {
    ".git",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

_LOCK_FILE_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile.lock",
    "cargo.lock",
    "gemfile.lock",
    "composer.lock",
}

_PRIVATE_KEY_FILE_NAMES = {
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

_CREDENTIAL_FILE_NAMES = {
    ".npmrc",
    ".pypirc",
    ".netrc",
}

_BINARY_OR_MEDIA_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".class",
    ".dll",
    ".doc",
    ".docx",
    ".dylib",
    ".eot",
    ".exe",
    ".gif",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".o",
    ".obj",
    ".otf",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".sqlite",
    ".ttf",
    ".wasm",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
}

_ARCHIVE_EXTENSIONS = {
    ".7z",
    ".bz2",
    ".gz",
    ".rar",
    ".tar",
    ".tar.bz2",
    ".tar.gz",
    ".tar.xz",
    ".tgz",
    ".xz",
    ".zip",
}

_LANGUAGE_BY_EXTENSION = {
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "JavaScript",
    ".md": "Markdown",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".sh": "Shell",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".txt": "Text",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
}
