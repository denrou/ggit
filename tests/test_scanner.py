from pathlib import Path
from unittest.mock import patch

from ggit.scanner import find_repos


def test_find_repos_discovers_git_dirs():
    fake_tree = [
        ("/root", ["project-a", ".hidden", "project-b"], []),
        ("/root/project-a", [".git", "src"], []),
        ("/root/project-b", ["sub"], []),
        ("/root/project-b/sub", [".git"], []),
    ]

    with patch("ggit.scanner.os.walk") as mock_walk:
        mock_walk.return_value = iter(fake_tree)
        repos = find_repos("/root")

    assert repos == [Path("/root/project-a").resolve(), Path("/root/project-b/sub").resolve()]


def test_find_repos_empty_dir():
    with patch("ggit.scanner.os.walk") as mock_walk:
        mock_walk.return_value = iter([("/empty", [], [])])
        repos = find_repos("/empty")

    assert repos == []
