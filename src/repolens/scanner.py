"""Safe repository scanning placeholders."""

from pathlib import Path


def scan_files(repository_path: Path) -> list[Path]:
    """Scan and filter repository files in a future milestone."""
    del repository_path
    raise NotImplementedError("Repository scanning is not implemented yet.")

