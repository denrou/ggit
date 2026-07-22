import json
import os
import subprocess
from pathlib import Path

import pytest

from ggit.report import (
    RepoReport,
    build_reports,
    get_report,
    needs_attention,
    reports_to_json,
)

ENV = {**os.environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t.com",
       "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t.com"}


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=ENV)


@pytest.fixture()
def simple_repo(tmp_path: Path) -> Path:
    """A clean repository with a single commit on main and no remote."""
    repo = tmp_path / "simple"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("hello")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    return repo


@pytest.fixture()
def messy_repo(tmp_path: Path) -> Path:
    """A repository exhibiting every cleanup signal: stash, merged branch,
    gone branch, branch without upstream, extra worktree, untracked file."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "--bare", "-b", "main")

    repo = tmp_path / "messy"
    _git(tmp_path, "clone", str(origin), "messy")
    (repo / "README.md").write_text("hello")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "remote", "set-head", "origin", "--auto")

    # A branch merged into main, also present on the remote
    _git(repo, "checkout", "-b", "merged-feature")
    (repo / "feature.txt").write_text("done")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feature")
    _git(repo, "push", "-u", "origin", "merged-feature")
    _git(repo, "checkout", "main")
    _git(repo, "merge", "merged-feature")
    _git(repo, "push", "origin", "main")

    # A branch whose upstream was deleted (gone)
    _git(repo, "checkout", "-b", "gone-branch")
    _git(repo, "push", "-u", "origin", "gone-branch")
    _git(repo, "push", "origin", "--delete", "gone-branch")
    _git(repo, "fetch", "--prune")
    _git(repo, "checkout", "main")

    # A branch with no upstream
    _git(repo, "branch", "local-only")

    # A stash
    (repo / "README.md").write_text("work in progress")
    _git(repo, "stash", "push", "-m", "wip stuff")

    # An extra worktree
    _git(repo, "worktree", "add", str(tmp_path / "messy-wt"), "-b", "wt-branch")

    # An untracked file
    (repo / "scratch.txt").write_text("notes")
    return repo


def test_simple_repo_report(simple_repo: Path):
    report = get_report(simple_repo)
    assert isinstance(report, RepoReport)
    assert report.name == "simple"
    assert report.branch == "main"
    assert report.default_branch == "main"
    assert report.origin is None
    assert report.dirty is False
    assert report.stashes == []
    assert report.merged_remote_branches == []
    assert len(report.worktrees) == 1
    assert report.worktrees[0].is_main is True
    assert needs_attention(report) is False


def test_messy_repo_stashes(messy_repo: Path):
    report = get_report(messy_repo)
    assert len(report.stashes) == 1
    assert report.stashes[0].index == 0
    assert "wip stuff" in report.stashes[0].message


def test_messy_repo_branches(messy_repo: Path):
    report = get_report(messy_repo)
    branches = {b.name: b for b in report.local_branches}

    assert branches["main"].is_current is True
    assert branches["main"].merged is False  # default branch is never flagged

    assert branches["merged-feature"].merged is True
    assert branches["gone-branch"].gone is True
    assert branches["local-only"].upstream is None
    assert branches["local-only"].gone is False


def test_messy_repo_merged_remote_branches(messy_repo: Path):
    report = get_report(messy_repo)
    assert "origin/merged-feature" in report.merged_remote_branches
    assert "origin/main" not in report.merged_remote_branches
    assert "origin/HEAD" not in report.merged_remote_branches
    assert "origin" not in report.merged_remote_branches  # short name of the origin/HEAD symref


def test_messy_repo_worktrees(messy_repo: Path):
    report = get_report(messy_repo)
    assert len(report.worktrees) == 2
    main_wt = next(w for w in report.worktrees if w.is_main)
    extra_wt = next(w for w in report.worktrees if not w.is_main)
    assert main_wt.path == str(messy_repo)
    assert extra_wt.branch == "wt-branch"
    assert extra_wt.dirty is False


def test_messy_repo_status(messy_repo: Path):
    report = get_report(messy_repo)
    assert report.dirty is True
    assert report.untracked == 1
    assert any("scratch.txt" in line for line in report.status_lines)
    assert needs_attention(report) is True


def test_get_report_invalid_path():
    with pytest.raises(ValueError, match="Cannot open repository"):
        get_report(Path("/nonexistent/repo"))


def test_build_reports_skips_unreadable(simple_repo: Path):
    reports = build_reports([simple_repo, Path("/nonexistent/repo")], include_prs=False)
    assert len(reports) == 1
    assert reports[0].name == "simple"


def test_reports_to_json_roundtrip(messy_repo: Path):
    reports = build_reports([messy_repo], include_prs=False)
    payload = json.loads(reports_to_json(reports, [messy_repo]))
    assert payload["repo_count"] == 1
    assert payload["scanned_paths"] == [str(messy_repo)]
    repo = payload["repos"][0]
    assert repo["name"] == "messy"
    assert repo["open_prs"] is None
    assert isinstance(repo["stashes"], list)
    assert isinstance(repo["local_branches"], list)
    assert isinstance(repo["worktrees"], list)
