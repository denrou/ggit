import json as _json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

from git import Repo


@dataclass
class RepoSummary:
    name: str
    path: str
    branch: str
    last_commit: str
    local_branches: int
    remote_branches: int
    modified: int
    staged: int
    untracked: int
    ahead: int
    origin: Optional[str]
    github_repo: Optional[str] = None
    open_prs: Optional[int] = None
    my_prs: Optional[int] = None


@dataclass
class RepoDetails:
    name: str
    path: str
    branch: str
    origin: Optional[str]
    local_branches: list = field(default_factory=list)
    remote_branches: list = field(default_factory=list)
    last_commit: str = ""
    last_fetch: Optional[str] = None
    authors: list = field(default_factory=list)


@dataclass
class FetchResult:
    path: str
    name: str
    ok: bool
    error: Optional[str]


@dataclass
class PruneResult:
    path: str
    name: str
    ok: bool
    pruned: Optional[list]
    error: Optional[str]


def get_summary(path: Path) -> RepoSummary:
    """Return a short summary for a repository: name, branch, last commit date, branch counts, and status."""
    try:
        repo = Repo(path)
    except Exception as e:
        raise ValueError(f"Cannot open repository at {path}: {e}") from e

    try:
        branch = repo.active_branch.name if not repo.head.is_detached else "HEAD"
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot determine branch for {path}: {e}") from e

    try:
        last_commit = repo.head.commit.committed_datetime.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Cannot read commits for {path}: {e}") from e

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

    return RepoSummary(
        name=path.name,
        path=str(path),
        branch=branch,
        last_commit=last_commit,
        local_branches=local_branches,
        remote_branches=remote_branches,
        modified=modified,
        staged=staged,
        untracked=untracked,
        ahead=ahead,
        origin=origin,
    )


def is_dirty(summary: RepoSummary) -> bool:
    """Return True if the repo has modifications, staged changes, untracked files, or unpushed commits."""
    return bool(summary.modified or summary.staged or summary.untracked or summary.ahead)


def format_status(summary: RepoSummary) -> str:
    """Build a compact status string from summary fields."""
    if not is_dirty(summary):
        return "✓"
    m, s, u, a = summary.modified, summary.staged, summary.untracked, summary.ahead
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


def fetch_repo(path: Path) -> FetchResult:
    """Fetch from origin."""
    name = path.name
    try:
        repo = Repo(path)
        if not repo.remotes:
            return FetchResult(path=str(path), name=name, ok=False, error="no remotes")
        repo.remotes.origin.fetch()
        return FetchResult(path=str(path), name=name, ok=True, error=None)
    except Exception as e:
        return FetchResult(path=str(path), name=name, ok=False, error=str(e))


def prune_repo(path: Path) -> PruneResult:
    """Prune stale remote-tracking branches."""
    name = path.name
    try:
        repo = Repo(path)
        if not repo.remotes:
            return PruneResult(path=str(path), name=name, ok=False, pruned=None, error="no remotes")
        output = repo.git.remote("prune", "origin")
        pruned = [line.strip() for line in output.splitlines() if line.strip()] if output else []
        return PruneResult(path=str(path), name=name, ok=True, pruned=pruned, error=None)
    except Exception as e:
        return PruneResult(path=str(path), name=name, ok=False, pruned=None, error=str(e))


def get_details(path: Path) -> dict:
    """Return detailed information about a repository."""
    try:
        repo = Repo(path)
    except Exception as e:
        raise ValueError(f"Cannot open repository at {path}: {e}") from e

    try:
        branch = repo.active_branch.name if not repo.head.is_detached else "HEAD"
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot determine branch for {path}: {e}") from e
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

    return RepoDetails(
        name=path.name,
        path=str(path),
        branch=branch,
        origin=origin,
        local_branches=local_branches,
        remote_branches=remote_branches,
        last_commit=last_commit,
        last_fetch=last_fetch,
        authors=authors,
    )


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
