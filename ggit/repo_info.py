import json as _json
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from git import Repo


def get_summary(path: Path) -> dict:
    """Return a short summary for a repository: name, branch, last commit date, branch counts, and status."""
    repo = Repo(path)
    branch = repo.active_branch.name if not repo.head.is_detached else "HEAD"
    last_commit = repo.head.commit.committed_datetime.strftime("%Y-%m-%d")

    local_branches = len(repo.branches)
    remote_branches = len([r for r in repo.refs if r.is_remote()])
    modified = len(repo.index.diff(None))
    staged = len(repo.index.diff("HEAD"))
    untracked = len(repo.untracked_files)

    try:
        tracking = repo.active_branch.tracking_branch()
        if tracking:
            ahead = int(repo.git.rev_list("--count", f"{tracking}..HEAD"))
        else:
            ahead = 0
    except (TypeError, ValueError):
        ahead = 0

    try:
        origin = repo.remotes.origin.url
    except (AttributeError, ValueError):
        origin = None

    return {
        "name": path.name,
        "path": str(path),
        "branch": branch,
        "last_commit": last_commit,
        "local_branches": local_branches,
        "remote_branches": remote_branches,
        "modified": modified,
        "staged": staged,
        "untracked": untracked,
        "ahead": ahead,
        "origin": origin,
    }


def is_dirty(summary: dict) -> bool:
    """Return True if the repo has modifications, staged changes, untracked files, or unpushed commits."""
    return bool(summary["modified"] or summary["staged"] or summary["untracked"] or summary["ahead"])


def format_status(summary: dict) -> str:
    """Build a compact status string from summary fields."""
    if not is_dirty(summary):
        return "✓"
    m, s, u, a = summary["modified"], summary["staged"], summary["untracked"], summary["ahead"]
    parts = ["●"]
    if m:
        parts.append(f"{m}M")
    if s:
        parts.append(f"{s}+")
    if u:
        parts.append(f"{u}?")
    if a:
        parts.append(f"↑{a}")
    return " ".join(parts)


def get_details(path: Path) -> dict:
    """Return detailed information about a repository."""
    repo = Repo(path)
    branch = repo.active_branch.name if not repo.head.is_detached else "HEAD"
    local_branches = [b.name for b in repo.branches]
    remote_branches = [r.name for r in repo.refs if r.is_remote()]
    last_commit = repo.head.commit.committed_datetime.strftime("%Y-%m-%d")

    # last fetch time from FETCH_HEAD
    fetch_head = Path(repo.git_dir) / "FETCH_HEAD"
    if fetch_head.exists():
        from datetime import datetime, timezone

        mtime = fetch_head.stat().st_mtime
        last_fetch = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    else:
        last_fetch = None

    # unique authors
    authors: list[str] = []
    for line in repo.git.shortlog("-s", "-n", "--all").splitlines():
        line = line.strip()
        if line:
            # format: "  123\tAuthor Name"
            parts = line.split("\t", 1)
            if len(parts) == 2:
                authors.append(parts[1])

    try:
        origin = repo.remotes.origin.url
    except (AttributeError, ValueError):
        origin = None

    return {
        "name": path.name,
        "path": str(path),
        "branch": branch,
        "origin": origin,
        "local_branches": local_branches,
        "remote_branches": remote_branches,
        "last_commit": last_commit,
        "last_fetch": last_fetch,
        "authors": authors,
    }


def parse_github_repo(url: str) -> Optional[str]:
    """Extract 'owner/repo' from a GitHub URL, or None if not a GitHub URL."""
    patterns = [
        r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$",
        r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?/?$",
        r"ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?/?$",
    ]
    for pattern in patterns:
        m = re.match(pattern, url)
        if m:
            return m.group(1)
    return None


def get_github_pr_counts(owner_repo: str) -> Optional[Tuple[int, int]]:
    """Return (total_open_prs, assigned_to_me_prs) for a GitHub repo, or None on failure."""
    try:
        total_result = subprocess.run(
            ["gh", "pr", "list", "--repo", owner_repo, "--state", "open", "--json", "number", "--limit", "1000"],
            capture_output=True, text=True, timeout=15,
        )
        if total_result.returncode != 0:
            return None
        total = len(_json.loads(total_result.stdout))

        mine_result = subprocess.run(
            ["gh", "pr", "list", "--repo", owner_repo, "--state", "open", "--assignee", "@me", "--json", "number", "--limit", "1000"],
            capture_output=True, text=True, timeout=15,
        )
        if mine_result.returncode != 0:
            return None
        mine = len(_json.loads(mine_result.stdout))

        return (total, mine)
    except (subprocess.TimeoutExpired, FileNotFoundError, _json.JSONDecodeError):
        return None
