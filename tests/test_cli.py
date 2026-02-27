from unittest.mock import patch

from typer.testing import CliRunner

from ggit.cli import app

runner = CliRunner()

CLEAN_REPO = {
    "name": "clean-repo",
    "path": "/tmp/clean-repo",
    "branch": "main",
    "last_commit": "2025-01-01",
    "local_branches": 1,
    "remote_branches": 1,
    "modified": 0,
    "staged": 0,
    "untracked": 0,
    "ahead": 0,
}

DIRTY_REPO = {
    "name": "dirty-repo",
    "path": "/tmp/dirty-repo",
    "branch": "dev",
    "last_commit": "2025-06-15",
    "local_branches": 5,
    "remote_branches": 3,
    "modified": 2,
    "staged": 1,
    "untracked": 0,
    "ahead": 0,
}

MANY_BRANCHES_REPO = {
    "name": "branches-repo",
    "path": "/tmp/branches-repo",
    "branch": "main",
    "last_commit": "2025-03-10",
    "local_branches": 10,
    "remote_branches": 8,
    "modified": 0,
    "staged": 0,
    "untracked": 0,
    "ahead": 0,
}

ALL_SUMMARIES = [CLEAN_REPO, DIRTY_REPO, MANY_BRANCHES_REPO]


def _mock_find_repos(path):
    return [s["path"] for s in ALL_SUMMARIES]


def _mock_get_summary(path):
    for s in ALL_SUMMARIES:
        if s["path"] == str(path):
            return dict(s)
    raise ValueError(f"Unknown path: {path}")


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_no_filter(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp"])
    assert result.exit_code == 0
    assert "clean-repo" in result.output
    assert "dirty-repo" in result.output
    assert "branches-repo" in result.output
    assert "3 repositories" in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_dirty(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--dirty"])
    assert result.exit_code == 0
    assert "dirty-repo" in result.output
    assert "clean-repo" not in result.output
    assert "branches-repo" not in result.output
    assert "1 repositories" in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_clean(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--clean"])
    assert result.exit_code == 0
    assert "clean-repo" in result.output
    assert "branches-repo" in result.output
    assert "dirty-repo" not in result.output
    assert "2 repositories" in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_dirty_and_clean_exclusive(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--dirty", "--clean"])
    assert result.exit_code != 0


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_min_local_branches(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--min-local-branches", "5"])
    assert result.exit_code == 0
    assert "dirty-repo" in result.output
    assert "branches-repo" in result.output
    assert "clean-repo" not in result.output
    assert "2 repositories" in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_min_remote_branches(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--min-remote-branches", "5"])
    assert result.exit_code == 0
    assert "branches-repo" in result.output
    assert "clean-repo" not in result.output
    assert "dirty-repo" not in result.output
    assert "1 repositories" in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_combined_filters(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--dirty", "--min-local-branches", "3"])
    assert result.exit_code == 0
    assert "dirty-repo" in result.output
    assert "clean-repo" not in result.output
    assert "branches-repo" not in result.output
    assert "1 repositories" in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_json_with_filter(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--dirty", "--json"])
    assert result.exit_code == 0
    assert "dirty-repo" in result.output
    assert "clean-repo" not in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_quiet(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "-q"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines == ["/tmp/branches-repo", "/tmp/clean-repo", "/tmp/dirty-repo"]
    # No table header or "Found N repositories" footer
    assert "Name" not in result.output
    assert "repositories" not in result.output


@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
def test_list_quiet_with_filter(mock_find, mock_summary):
    result = runner.invoke(app, ["list", "/tmp", "--quiet", "--dirty"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines == ["/tmp/dirty-repo"]
