"""Public GitHub repository acquisition placeholders."""

from pathlib import Path


def validate_github_url(github_url: str) -> None:
    """Validate a public GitHub URL in a future milestone."""
    del github_url
    raise NotImplementedError("GitHub URL validation is not implemented yet.")


def clone_repository(github_url: str, destination: Path) -> Path:
    """Clone a public GitHub repository in a future milestone."""
    del github_url, destination
    raise NotImplementedError("Repository cloning is not implemented yet.")

