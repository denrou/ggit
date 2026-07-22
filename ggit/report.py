"""Non-interactive repository reports for cleanup workflows.

Collects everything a cleanup session needs to know about a repository:
working-tree state, stashes, merged/gone branches, worktrees, and PR counts.
Designed to be serialized to JSON (``ggit --json``) and consumed by scripts
or LLM agents.
"""

import dataclasses
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from git import Repo

from ggit.repo_info import get_github_pr_counts, get_summary, parse_github_repo


@dataclass
class StashEntry:
    index: int
    message: str
    date: str


@dataclass
class LocalBranch:
    name: str
    is_current: bool
    upstream: Optional[str]
    gone: bool
    merged: bool
    last_commit: str


@dataclass
class WorktreeEntry:
    path: str
    branch: Optional[str]
    is_main: bool
    prunable: bool
    dirty: Optional[bool]


@dataclass
class RepoReport:
    name: str
    path: str
    branch: str
    default_branch: Optional[str]
    origin: Optional[str]
    github_repo: Optional[str]
    last_commit: str
    modified: int
    staged: int
    untracked: int
    ahead: int
    behind: int
    dirty: bool
    status_lines: list = field(default_factory=list)
    stashes: list = field(default_factory=list)
    local_branches: list = field(default_factory=list)
    remote_branches: list = field(default_factory=list)
    merged_remote_branches: list = field(default_factory=list)
    worktrees: list = field(default_factory=list)
    open_prs: Optional[int] = None
    my_prs: Optional[int] = None


def _get_default_branch(repo: Repo) -> Optional[str]:
    """Detect the default branch: origin/HEAD if set, else main/master if present."""
    try:
        ref = repo.git.symbolic_ref("refs/remotes/origin/HEAD")
        return ref.rsplit("/", 1)[-1]
    except Exception:
        pass
    local = {b.name for b in repo.branches}
    for candidate in ("main", "master"):
        if candidate in local:
            return candidate
    return None


def _merge_base_ref(repo: Repo, default_branch: Optional[str]) -> Optional[str]:
    """Return the ref to test merges against: the local default branch, or its remote."""
    if default_branch is None:
        return None
    if default_branch in {b.name for b in repo.branches}:
        return default_branch
    remote = f"origin/{default_branch}"
    if remote in {r.name for r in repo.refs if r.is_remote()}:
        return remote
    return None


def _get_behind(repo: Repo) -> int:
    try:
        tracking = repo.active_branch.tracking_branch()
        if tracking:
            return int(repo.git.rev_list("--count", f"HEAD..{tracking}"))
    except (TypeError, ValueError):
        pass
    return 0


def _get_stashes(repo: Repo) -> list:
    try:
        output = repo.git.stash("list", "--format=%gd%x09%cs%x09%gs")
    except Exception:
        return []
    stashes = []
    for line in output.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        ref, date, message = parts
        try:
            index = int(ref[ref.index("{") + 1 : ref.index("}")])
        except ValueError:
            continue
        stashes.append(StashEntry(index=index, message=message, date=date))
    return stashes


def _get_local_branches(repo: Repo, merge_base: Optional[str], current: str) -> list:
    merged_names: set = set()
    if merge_base:
        try:
            output = repo.git.branch("--merged", merge_base, "--format=%(refname:short)")
            merged_names = {line.strip() for line in output.splitlines() if line.strip()}
        except Exception:
            merged_names = set()
    default_name = merge_base.rsplit("/", 1)[-1] if merge_base else None

    try:
        output = repo.git.for_each_ref(
            "refs/heads",
            "--format=%(refname:short)%09%(upstream:short)%09%(upstream:track)%09%(committerdate:short)",
        )
    except Exception:
        return []

    branches = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 4:
            continue
        name, upstream, track, date = parts
        branches.append(
            LocalBranch(
                name=name,
                is_current=(name == current),
                upstream=upstream or None,
                gone=(track == "[gone]"),
                merged=(name in merged_names and name != default_name),
                last_commit=date,
            )
        )
    return branches


def _get_merged_remote_branches(repo: Repo, merge_base: Optional[str], default_branch: Optional[str]) -> list:
    if merge_base is None or default_branch is None:
        return []
    try:
        output = repo.git.branch("-r", "--merged", merge_base, "--format=%(refname:short)")
    except Exception:
        return []
    # "origin" is the short name of the origin/HEAD symref
    skip = {f"origin/{default_branch}", "origin/HEAD", "origin"}
    return [line.strip() for line in output.splitlines() if line.strip() and line.strip() not in skip]


def _get_worktrees(repo: Repo) -> list:
    try:
        output = repo.git.worktree("list", "--porcelain")
    except Exception:
        return []

    worktrees = []
    current: dict = {}
    blocks = [b for b in output.split("\n\n") if b.strip()]
    for i, block in enumerate(blocks):
        current = {"is_main": i == 0, "prunable": False, "branch": None}
        for line in block.splitlines():
            if line.startswith("worktree "):
                current["path"] = line[len("worktree ") :]
            elif line.startswith("branch "):
                ref = line[len("branch ") :]
                current["branch"] = ref[len("refs/heads/") :] if ref.startswith("refs/heads/") else ref
            elif line.startswith("prunable"):
                current["prunable"] = True
        if "path" not in current:
            continue
        dirty: Optional[bool] = None
        if not current["prunable"]:
            try:
                dirty = Repo(current["path"]).is_dirty(untracked_files=True)
            except Exception:
                dirty = None
        worktrees.append(
            WorktreeEntry(
                path=current["path"],
                branch=current["branch"],
                is_main=current["is_main"],
                prunable=current["prunable"],
                dirty=dirty,
            )
        )
    return worktrees


def get_report(path: Path) -> RepoReport:
    """Build a full cleanup report for a single repository.

    Raises ValueError if the repository cannot be read (same contract as get_summary).
    """
    summary = get_summary(path)
    repo = Repo(path)

    default_branch = _get_default_branch(repo)
    merge_base = _merge_base_ref(repo, default_branch)
    behind = _get_behind(repo)

    try:
        status_raw = repo.git.status("--short")
    except Exception:
        status_raw = ""
    status_lines = [line for line in status_raw.splitlines() if line.strip()]

    local_branches = _get_local_branches(repo, merge_base, summary.branch)
    remote_branches = [r.name for r in repo.refs if r.is_remote() and r.name != "origin/HEAD"]

    return RepoReport(
        name=summary.name,
        path=summary.path,
        branch=summary.branch,
        default_branch=default_branch,
        origin=summary.origin,
        github_repo=parse_github_repo(summary.origin) if summary.origin else None,
        last_commit=summary.last_commit,
        modified=summary.modified,
        staged=summary.staged,
        untracked=summary.untracked,
        ahead=summary.ahead,
        behind=behind,
        dirty=bool(summary.modified or summary.staged or summary.untracked or summary.ahead),
        status_lines=status_lines,
        stashes=_get_stashes(repo),
        local_branches=local_branches,
        remote_branches=remote_branches,
        merged_remote_branches=_get_merged_remote_branches(repo, merge_base, default_branch),
        worktrees=_get_worktrees(repo),
    )


def needs_attention(report: RepoReport) -> bool:
    """True if the repo has anything a cleanup session should look at."""
    if report.dirty or report.stashes:
        return True
    if any(b.gone or b.merged for b in report.local_branches):
        return True
    if report.merged_remote_branches:
        return True
    if any(not w.is_main and (w.prunable or w.dirty) for w in report.worktrees):
        return True
    return False


def build_reports(repo_paths: list, include_prs: bool = True, max_workers: int = 8) -> list:
    """Build reports for many repositories in parallel, skipping unreadable ones."""

    def _safe_report(repo_path: Path) -> Optional[RepoReport]:
        try:
            return get_report(repo_path)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_safe_report, repo_paths))
    reports = [r for r in results if r is not None]

    if include_prs:
        github_repos = {r.github_repo for r in reports if r.github_repo}
        if github_repos:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                counts = dict(zip(github_repos, executor.map(get_github_pr_counts, github_repos)))
            for r in reports:
                pr_counts = counts.get(r.github_repo) if r.github_repo else None
                if pr_counts:
                    r.open_prs, r.my_prs = pr_counts

    return reports


def reports_to_json(reports: list, scanned_paths: list) -> str:
    """Serialize reports to a pretty-printed JSON document."""
    payload = {
        "scanned_paths": [str(p) for p in scanned_paths],
        "repo_count": len(reports),
        "repos": [dataclasses.asdict(r) for r in reports],
    }
    return json.dumps(payload, indent=2)
