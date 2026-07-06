"""Tests for GitHub URL validation and shallow clone behavior."""

from pathlib import Path
import subprocess

import pytest

from repolens.errors import (
    GitNotFoundError,
    InvalidRepositoryUrlError,
    RepositoryCloneError,
)
from repolens.git_source import clone_repository, validate_github_url


@pytest.mark.parametrize(
    ("url", "owner", "repo", "clone_url"),
    [
        (
            "https://github.com/owner/repo",
            "owner",
            "repo",
            "https://github.com/owner/repo.git",
        ),
        (
            "https://github.com/owner/repo.git",
            "owner",
            "repo",
            "https://github.com/owner/repo.git",
        ),
        (
            "https://github.com/owner/repo/",
            "owner",
            "repo",
            "https://github.com/owner/repo.git",
        ),
    ],
)
def test_validate_github_url_accepts_supported_https_repository_urls(
    url: str,
    owner: str,
    repo: str,
    clone_url: str,
) -> None:
    repository = validate_github_url(url)

    assert repository.owner == owner
    assert repository.repo == repo
    assert repository.clone_url == clone_url


@pytest.mark.parametrize(
    "url",
    [
        "git@github.com:owner/repo.git",
        "ssh://git@github.com/owner/repo.git",
        "../owner/repo",
        r"C:\Users\owner\repo",
        "https://gitlab.com/owner/repo",
        "http://github.com/owner/repo",
        "https://github.com/owner",
        "https://github.com/owner/repo/issues",
        "https://github.com/owner/repo?tab=readme",
        "not a url",
        "",
    ],
)
def test_validate_github_url_rejects_unsupported_urls(url: str) -> None:
    with pytest.raises(InvalidRepositoryUrlError):
        validate_github_url(url)


def test_validate_github_url_normalizes_trailing_slash_and_git_suffix() -> None:
    repository = validate_github_url("  https://github.com/OwnerName/repo-name.git/  ")

    assert repository.owner == "OwnerName"
    assert repository.repo == "repo-name"
    assert repository.clone_url == "https://github.com/OwnerName/repo-name.git"


def test_clone_repository_uses_shallow_clone_and_cleans_temporary_workspace(
    monkeypatch,
) -> None:
    calls: list[tuple[list[str], Path | None]] = []

    def fake_run(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool,
        text: bool,
        capture_output: bool,
        shell: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((args, cwd))
        assert check is True
        assert text is True
        assert capture_output is True
        assert shell is False

        if args[:4] == ["git", "clone", "--depth", "1"]:
            Path(args[-1]).mkdir(parents=True)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        if args == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout="abc123\n",
                stderr="",
            )

        raise AssertionError(f"Unexpected git command: {args}")

    monkeypatch.setattr("repolens.git_source.subprocess.run", fake_run)

    with clone_repository("https://github.com/owner/repo") as repository:
        local_path = repository.local_path
        assert repository.owner == "owner"
        assert repository.repo == "repo"
        assert repository.clone_url == "https://github.com/owner/repo.git"
        assert repository.commit_sha == "abc123"
        assert local_path.exists()

    assert calls[0][0] == [
        "git",
        "clone",
        "--depth",
        "1",
        "https://github.com/owner/repo.git",
        str(local_path),
    ]
    assert calls[1][0] == ["git", "rev-parse", "HEAD"]
    assert calls[1][1] == local_path
    assert not local_path.exists()


def test_clone_repository_reports_missing_git(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("repolens.git_source.subprocess.run", fake_run)

    with pytest.raises(GitNotFoundError):
        with clone_repository("https://github.com/owner/repo"):
            pass


def test_clone_repository_reports_clone_failure(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=128,
            cmd=args[0],
            stderr="repository not found",
        )

    monkeypatch.setattr("repolens.git_source.subprocess.run", fake_run)

    with pytest.raises(RepositoryCloneError, match="repository not found"):
        with clone_repository("https://github.com/owner/repo"):
            pass
