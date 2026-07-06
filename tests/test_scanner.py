"""Tests for the safe repository scanner."""

from pathlib import Path

import pytest

from repolens.scanner import RepositoryScanner, ScanLimits


def test_scanner_includes_normal_text_files(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    result = RepositoryScanner().scan(tmp_path)

    included_paths = {file.path for file in result.included_files}
    assert "src/app.py" in included_paths
    assert "README.md" in included_paths
    assert result.total_files_seen == 2
    assert result.language_counts["Python"] == 1
    assert result.language_counts["Markdown"] == 1


def test_scanner_skips_git_and_node_modules_directories(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("ignored\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.js").write_text("ignored\n", encoding="utf-8")

    result = RepositoryScanner().scan(tmp_path)

    skipped = {(file.path, file.reason) for file in result.skipped_files}
    assert (".git", "skipped_directory") in skipped
    assert ("node_modules", "skipped_directory") in skipped
    assert result.total_files_seen == 0
    assert result.included_files == []


def test_scanner_skips_binary_files(tmp_path: Path) -> None:
    (tmp_path / "data.bin").write_bytes(b"abc\x00def")

    result = RepositoryScanner().scan(tmp_path)

    assert result.included_files == []
    assert result.skipped_files[0].path == "data.bin"
    assert result.skipped_files[0].reason == "binary_file"
    assert result.skipped_files[0].is_text is False


def test_scanner_skips_env_and_private_key_files(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    (tmp_path / "id_rsa").write_text("PRIVATE KEY\n", encoding="utf-8")
    (tmp_path / "credentials.json").write_text('{"token":"secret"}\n', encoding="utf-8")

    result = RepositoryScanner().scan(tmp_path)

    skipped = {file.path: file.reason for file in result.skipped_files}
    assert skipped[".env"] == "secret_or_environment_file"
    assert skipped["id_rsa"] == "private_key_file"
    assert skipped["credentials.json"] == "credential_like_file"
    assert result.included_files == []


def test_scanner_does_not_follow_symlinks(tmp_path: Path) -> None:
    outside_file = tmp_path.parent / "outside-secret.py"
    outside_file.write_text("print('outside')\n", encoding="utf-8")
    link_path = tmp_path / "linked.py"

    try:
        link_path.symlink_to(outside_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not available in this environment.")

    result = RepositoryScanner().scan(tmp_path)

    assert result.included_files == []
    assert result.skipped_files[0].path == "linked.py"
    assert result.skipped_files[0].reason == "symlink_not_followed"


def test_scanner_respects_included_file_limit(tmp_path: Path) -> None:
    for index in range(3):
        (tmp_path / f"file_{index}.py").write_text("print('hello')\n", encoding="utf-8")

    result = RepositoryScanner(limits=ScanLimits(max_included_files=1)).scan(tmp_path)

    assert result.included_count == 1
    assert any(file.reason == "max_included_files_reached" for file in result.skipped_files)
    assert any("max_included_files=1" in limitation for limitation in result.limitations)


def test_scanner_respects_single_file_size_limit(tmp_path: Path) -> None:
    (tmp_path / "large.py").write_text("x" * 20, encoding="utf-8")

    result = RepositoryScanner(limits=ScanLimits(max_single_file_size_bytes=10)).scan(tmp_path)

    assert result.included_files == []
    assert result.skipped_files[0].path == "large.py"
    assert result.skipped_files[0].reason == "file_too_large"


def test_scanner_respects_total_file_scan_limit(tmp_path: Path) -> None:
    for index in range(3):
        (tmp_path / f"file_{index}.py").write_text("print('hello')\n", encoding="utf-8")

    result = RepositoryScanner(limits=ScanLimits(max_total_files_scanned=2)).scan(tmp_path)

    assert result.total_files_seen == 2
    assert any("max_total_files_scanned=2" in limitation for limitation in result.limitations)


def test_scanner_produces_language_counts(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "index.js").write_text("console.log('hello')\n", encoding="utf-8")
    (tmp_path / "types.ts").write_text("const value: string = 'hello'\n", encoding="utf-8")

    result = RepositoryScanner().scan(tmp_path)

    assert result.language_counts == {
        "JavaScript": 1,
        "Python": 1,
        "TypeScript": 1,
    }


def test_scanner_includes_lock_files_as_metadata(tmp_path: Path) -> None:
    (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 3}\n', encoding="utf-8")

    result = RepositoryScanner().scan(tmp_path)

    assert result.included_files[0].path == "package-lock.json"
    assert result.included_files[0].analysis_mode == "metadata"
