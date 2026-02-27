import os
from pathlib import Path

from rich.progress import Progress


def find_repos(path: str = ".") -> list[Path]:
    """Find git repositories in a directory.

    Walks the directory tree, skipping hidden directories.
    When a `.git` folder is found, the parent is recorded and its subtree is pruned.
    """
    repos: list[Path] = []
    with Progress(transient=True) as progress:
        progress.add_task("Scanning for git repos…", total=None)
        for dirpath, dirnames, _ in os.walk(path):
            if ".git" in dirnames:
                repos.append(Path(dirpath).resolve())
                dirnames.clear()
            else:
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
    return repos
