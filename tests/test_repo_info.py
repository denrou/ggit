import os
import subprocess
from pathlib import Path

import pytest

from unittest.mock import patch

from ggit.repo_info import (
    RepoSummary,
    fetch_repo,
    format_status,
    get_details,
    get_github_pr_counts,
    get_summary,
    is_dirty,
    parse_github_repo,
    prune_repo,
)


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
    assert isinstance(result, RepoSummary)
    assert result.name == "test-repo"
    assert result.branch == "main"
    assert len(result.last_commit) == 10  # YYYY-MM-DD
    assert isinstance(result.local_branches, int)
    assert isinstance(result.remote_branches, int)
    assert isinstance(result.modified, int)
    assert isinstance(result.staged, int)
    assert isinstance(result.untracked, int)
    assert isinstance(result.ahead, int)
    assert result.origin is None  # no remote in fresh repo


def _make_summary(**overrides):
    defaults = dict(
        name="test", path="/tmp/test", branch="main", last_commit="2025-01-01",
        local_branches=1, remote_branches=0, modified=0, staged=0, untracked=0,
        ahead=0, origin=None,
    )
    defaults.update(overrides)
    return RepoSummary(**defaults)


def test_is_dirty_clean():
    assert is_dirty(_make_summary()) is False


def test_is_dirty_modified():
    assert is_dirty(_make_summary(modified=1)) is True


def test_is_dirty_staged():
    assert is_dirty(_make_summary(staged=2)) is True


def test_is_dirty_untracked():
    assert is_dirty(_make_summary(untracked=3)) is True


def test_is_dirty_ahead():
    assert is_dirty(_make_summary(ahead=1)) is True


def test_format_status_clean():
    assert format_status(_make_summary()) == "✓"


def test_format_status_dirty():
    assert format_status(_make_summary(modified=3, staged=1, untracked=2, ahead=4)) == "● 3M 1+ 2? ↑4"


def test_get_details(tmp_repo: Path):
    result = get_details(tmp_repo)
    assert result.name == "test-repo"
    assert result.branch == "main"
    assert "main" in result.local_branches
    assert result.last_fetch is None  # no FETCH_HEAD in fresh repo
    assert "Test" in result.authors


def test_parse_github_repo_https():
    assert parse_github_repo("https://github.com/acme/myrepo.git") == "acme/myrepo"


def test_parse_github_repo_https_no_git_suffix():
    assert parse_github_repo("https://github.com/acme/myrepo") == "acme/myrepo"


def test_parse_github_repo_ssh():
    assert parse_github_repo("git@github.com:acme/myrepo.git") == "acme/myrepo"


def test_parse_github_repo_ssh_no_git_suffix():
    assert parse_github_repo("git@github.com:acme/myrepo") == "acme/myrepo"


def test_parse_github_repo_ssh_protocol():
    assert parse_github_repo("ssh://git@github.com/acme/myrepo.git") == "acme/myrepo"


def test_parse_github_repo_not_github():
    assert parse_github_repo("https://gitlab.com/acme/myrepo.git") is None


def test_parse_github_repo_non_url():
    assert parse_github_repo("/local/path/to/repo") is None


def test_fetch_repo_no_origin(tmp_repo: Path):
    """fetch_repo returns ok=False when there are no remotes."""
    result = fetch_repo(tmp_repo)
    assert result.ok is False
    assert result.error == "no remotes"
    assert result.name == "test-repo"


def test_prune_repo_no_origin(tmp_repo: Path):
    """prune_repo returns ok=False when there are no remotes."""
    result = prune_repo(tmp_repo)
    assert result.ok is False
    assert result.error == "no remotes"
    assert result.name == "test-repo"
    assert result.pruned is None


def test_fetch_repo_invalid_path():
    result = fetch_repo(Path("/nonexistent/repo"))
    assert result.ok is False
    assert result.error is not None


def test_prune_repo_invalid_path():
    result = prune_repo(Path("/nonexistent/repo"))
    assert result.ok is False
    assert result.error is not None


@patch("ggit.repo_info.subprocess.run")
def test_get_github_pr_counts_success(mock_run):
    mock_run.side_effect = [
        type("Result", (), {"returncode": 0, "stdout": '[{"number":1},{"number":2},{"number":3}]'})(),
        type("Result", (), {"returncode": 0, "stdout": '[{"number":1}]'})(),
    ]
    result = get_github_pr_counts("acme/myrepo")
    assert result == (3, 1)


@patch("ggit.repo_info.subprocess.run")
def test_get_github_pr_counts_gh_not_found(mock_run):
    mock_run.side_effect = FileNotFoundError
    result = get_github_pr_counts("acme/myrepo")
    assert result is None


@patch("ggit.repo_info.subprocess.run")
def test_get_github_pr_counts_failure(mock_run):
    mock_run.return_value = type("Result", (), {"returncode": 1, "stdout": ""})()
    result = get_github_pr_counts("acme/myrepo")
    assert result is None


def test_get_summary_invalid_path():
    """get_summary raises ValueError for a nonexistent path."""
    with pytest.raises(ValueError, match="Cannot open repository"):
        get_summary(Path("/nonexistent/repo"))


def test_get_details_invalid_path():
    """get_details raises ValueError for a nonexistent path."""
    with pytest.raises(ValueError, match="Cannot open repository"):
        get_details(Path("/nonexistent/repo"))


def test_get_summary_detached_head(tmp_repo: Path):
    """get_summary returns HEAD as branch for detached HEAD state."""
    env = {**os.environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t.com",
           "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t.com"}
    # Create a second commit and detach HEAD at it
    (tmp_repo / "file2.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=tmp_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "second"], cwd=tmp_repo, check=True, capture_output=True, env=env)
    commit_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    subprocess.run(["git", "checkout", commit_hash], cwd=tmp_repo, check=True, capture_output=True)
    result = get_summary(tmp_repo)
    assert result.branch == "HEAD"


def test_get_details_detached_head(tmp_repo: Path):
    """get_details returns HEAD as branch for detached HEAD state."""
    env = {**os.environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t.com",
           "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t.com"}
    (tmp_repo / "file2.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=tmp_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "second"], cwd=tmp_repo, check=True, capture_output=True, env=env)
    commit_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    subprocess.run(["git", "checkout", commit_hash], cwd=tmp_repo, check=True, capture_output=True)
    result = get_details(tmp_repo)
    assert result.branch == "HEAD"


def test_fetch_result_has_pruned_field():
    """FetchResult has a pruned field (defaults to None) for structural parity with PruneResult."""
    result = fetch_repo(Path("/nonexistent/repo"))
    assert hasattr(result, "pruned")
    assert result.pruned is None
