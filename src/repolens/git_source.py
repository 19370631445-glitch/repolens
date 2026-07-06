"""Public GitHub repository acquisition.

This module is intentionally small for v0.1:
- validate a public GitHub HTTPS repository URL;
- clone the repository with `git clone --depth 1`;
- keep the clone inside a temporary workspace owned by RepoLens.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from repolens.errors import (
    GitNotFoundError,
    InvalidRepositoryUrlError,
    RepositoryCloneError,
)

_GITHUB_HOST = "github.com"
_REPOSITORY_PART_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class GitHubRepository:
    """Normalized metadata for a public GitHub repository URL."""

    owner: str
    repo: str
    clone_url: str


@dataclass(frozen=True)
class ClonedRepository:
    """Metadata for a repository cloned into a temporary local workspace."""

    owner: str
    repo: str
    clone_url: str
    local_path: Path
    commit_sha: str | None = None


def validate_github_url(github_url: str) -> GitHubRepository:
    """Validate and normalize a public GitHub HTTPS repository URL.

    Supported examples:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/
    """
    raw_url = github_url.strip()
    parsed = urlparse(raw_url)

    if parsed.scheme != "https":
        raise InvalidRepositoryUrlError(
            "Only public GitHub HTTPS repository URLs are supported. "
            "Example: https://github.com/owner/repo"
        )

    if parsed.hostname is None or parsed.hostname.lower() != _GITHUB_HOST:
        raise InvalidRepositoryUrlError(
            "Only github.com repository URLs are supported in v0.1."
        )

    if parsed.username or parsed.password or parsed.port is not None:
        raise InvalidRepositoryUrlError(
            "GitHub repository URLs should not include credentials or ports."
        )

    if parsed.params or parsed.query or parsed.fragment:
        raise InvalidRepositoryUrlError(
            "GitHub repository URLs should point directly to the repository, "
            "without query strings or fragments."
        )

    path_parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(path_parts) != 2:
        raise InvalidRepositoryUrlError(
            "Expected a GitHub repository URL in the form "
            "https://github.com/owner/repo"
        )

    owner, repo = path_parts
    if repo.endswith(".git"):
        repo = repo.removesuffix(".git")

    if not owner or not repo:
        raise InvalidRepositoryUrlError("GitHub owner and repository name are required.")

    if not _is_safe_github_path_part(owner) or not _is_safe_github_path_part(repo):
        raise InvalidRepositoryUrlError(
            "GitHub owner and repository name may only contain letters, numbers, "
            "dots, hyphens, and underscores."
        )

    clone_url = f"https://github.com/{owner}/{repo}.git"
    return GitHubRepository(owner=owner, repo=repo, clone_url=clone_url)


@contextmanager
def clone_repository(github_url: str) -> Iterator[ClonedRepository]:
    """Shallow clone a public GitHub repository into a safe temporary workspace.

    The temporary workspace is created by RepoLens and automatically removed
    when the caller exits the context manager.
    """
    repository = validate_github_url(github_url)

    with TemporaryDirectory(prefix="repolens-") as workspace:
        local_path = Path(workspace) / repository.repo
        _run_git_command(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repository.clone_url,
                str(local_path),
            ],
            error_message=(
                "Could not clone the repository. Please check that the URL is public, "
                "the repository exists, and your network connection can reach GitHub."
            ),
        )

        commit_sha = _read_commit_sha(local_path)
        yield ClonedRepository(
            owner=repository.owner,
            repo=repository.repo,
            clone_url=repository.clone_url,
            local_path=local_path,
            commit_sha=commit_sha,
        )


def _is_safe_github_path_part(value: str) -> bool:
    return bool(_REPOSITORY_PART_PATTERN.fullmatch(value))


def _run_git_command(
    args: list[str],
    *,
    cwd: Path | None = None,
    error_message: str,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise GitNotFoundError(
            "Git is not installed or is not available on PATH. "
            "Please install Git, then run RepoLens again."
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        if detail:
            raise RepositoryCloneError(f"{error_message}\nGit output: {detail}") from exc
        raise RepositoryCloneError(error_message) from exc


def _read_commit_sha(local_path: Path) -> str | None:
    try:
        result = _run_git_command(
            ["git", "rev-parse", "HEAD"],
            cwd=local_path,
            error_message="Could not read the cloned repository commit SHA.",
        )
    except RepositoryCloneError:
        return None

    commit_sha = result.stdout.strip()
    return commit_sha or None
