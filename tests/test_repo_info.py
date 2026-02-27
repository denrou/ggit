import os
import subprocess
from pathlib import Path

import pytest

from ggit.repo_info import format_status, get_details, get_summary, is_dirty


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """Create a minimal git repository in a temp directory."""
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t.com",
           "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t.com"}
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
    (repo_dir / "README.md").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True, env=env)
    return repo_dir


def test_get_summary(tmp_repo: Path):
    result = get_summary(tmp_repo)
    assert result["name"] == "test-repo"
    assert result["branch"] == "main"
    assert len(result["last_commit"]) == 10  # YYYY-MM-DD
    assert isinstance(result["local_branches"], int)
    assert isinstance(result["remote_branches"], int)
    assert isinstance(result["modified"], int)
    assert isinstance(result["staged"], int)
    assert isinstance(result["untracked"], int)
    assert isinstance(result["ahead"], int)


def test_is_dirty_clean():
    summary = {"modified": 0, "staged": 0, "untracked": 0, "ahead": 0}
    assert is_dirty(summary) is False


def test_is_dirty_modified():
    summary = {"modified": 1, "staged": 0, "untracked": 0, "ahead": 0}
    assert is_dirty(summary) is True


def test_is_dirty_staged():
    summary = {"modified": 0, "staged": 2, "untracked": 0, "ahead": 0}
    assert is_dirty(summary) is True


def test_is_dirty_untracked():
    summary = {"modified": 0, "staged": 0, "untracked": 3, "ahead": 0}
    assert is_dirty(summary) is True


def test_is_dirty_ahead():
    summary = {"modified": 0, "staged": 0, "untracked": 0, "ahead": 1}
    assert is_dirty(summary) is True


def test_format_status_clean():
    summary = {"modified": 0, "staged": 0, "untracked": 0, "ahead": 0}
    assert format_status(summary) == "✓"


def test_format_status_dirty():
    summary = {"modified": 3, "staged": 1, "untracked": 2, "ahead": 4}
    assert format_status(summary) == "● 3M 1+ 2? ↑4"


def test_get_details(tmp_repo: Path):
    result = get_details(tmp_repo)
    assert result["name"] == "test-repo"
    assert result["branch"] == "main"
    assert "main" in result["local_branches"]
    assert result["last_fetch"] is None  # no FETCH_HEAD in fresh repo
    assert "Test" in result["authors"]
