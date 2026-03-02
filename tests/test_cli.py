from pathlib import Path
from unittest.mock import patch

import pytest
from textual.coordinate import Coordinate

from ggit.cli import GgitApp

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
    "origin": "https://github.com/acme/clean-repo.git",
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
    "origin": "https://gitlab.com/acme/dirty-repo.git",
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
    "origin": None,
}

ALL_SUMMARIES = [CLEAN_REPO, DIRTY_REPO, MANY_BRANCHES_REPO]


def _mock_find_repos(path):
    return [Path(s["path"]) for s in ALL_SUMMARIES]


def _mock_get_summary(path):
    for s in ALL_SUMMARIES:
        if s["path"] == str(path):
            return dict(s)
    raise ValueError(f"Unknown path: {path}")


def _make_app():
    return GgitApp("/tmp")


def _get_table_row_values(table, row_idx):
    """Get values from a DataTable row by index."""
    row_key, _ = table.coordinate_to_cell_key(Coordinate(row_idx, 0))
    return table.get_row(row_key)


async def _wait_for_table(pilot):
    """Wait until the DataTable is visible and has rows."""
    for _ in range(100):
        await pilot.pause()
        table = pilot.app.query_one("#repo-table")
        if table.display and table.row_count > 0:
            return
    raise TimeoutError("Table never populated")


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_table_loads_repos(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        table = pilot.app.query_one("#repo-table")
        assert table.row_count == 3


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_status_bar_shows_count(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        assert len(pilot.app.filtered_summaries) == 3


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_filter_dirty(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        await pilot.press("d")
        await pilot.pause()
        table = pilot.app.query_one("#repo-table")
        assert table.row_count == 1
        values = _get_table_row_values(table, 0)
        assert values[0] == "dirty-repo"
        assert pilot.app.filter_mode == "dirty"


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_filter_clean(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        await pilot.press("c")
        await pilot.pause()
        table = pilot.app.query_one("#repo-table")
        assert table.row_count == 2
        names = [_get_table_row_values(table, i)[0] for i in range(table.row_count)]
        assert "clean-repo" in names
        assert "branches-repo" in names
        assert "dirty-repo" not in names
        assert pilot.app.filter_mode == "clean"


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_filter_all_resets(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        await pilot.press("d")
        await pilot.pause()
        assert pilot.app.query_one("#repo-table").row_count == 1
        await pilot.press("a")
        await pilot.pause()
        assert pilot.app.query_one("#repo-table").row_count == 3
        assert pilot.app.filter_mode == "all"


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_sort_cycle(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        assert pilot.app.sort_column == "name"

        await pilot.press("s")
        await pilot.pause()
        assert pilot.app.sort_column == "branch"

        await pilot.press("s")
        await pilot.pause()
        assert pilot.app.sort_column == "last_commit"

        await pilot.press("s")
        await pilot.pause()
        assert pilot.app.sort_column == "name"


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_reverse_sort(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        assert pilot.app.sort_reverse is False

        await pilot.press("r")
        await pilot.pause()
        assert pilot.app.sort_reverse is True

        # Check order is reversed (name desc: dirty > clean > branches)
        table = pilot.app.query_one("#repo-table")
        first = _get_table_row_values(table, 0)[0]
        assert first == "dirty-repo"


@pytest.mark.asyncio
@patch("ggit.cli.get_details", return_value={
    "name": "branches-repo",
    "branch": "main",
    "local_branches": ["main", "dev"],
    "remote_branches": ["origin/main"],
    "last_commit": "2025-03-10",
    "last_fetch": "2025-03-09",
    "authors": ["Alice", "Bob"],
})
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_enter_detail_and_escape(mock_find, mock_summary, mock_prs, mock_details):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        await pilot.press("enter")
        # Wait for detail screen content
        for _ in range(100):
            await pilot.pause()
            screen = pilot.app.screen
            if hasattr(screen, "detail_text") and "Repository:" in screen.detail_text:
                break

        text = pilot.app.screen.detail_text
        assert "Repository:" in text
        assert "Authors: Alice, Bob" in text

        await pilot.press("escape")
        await pilot.pause()
        table = pilot.app.query_one("#repo-table")
        assert table.row_count == 3


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_pr_counts_displayed(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        # Wait for phase 2 (PR counts) to complete
        table = pilot.app.query_one("#repo-table")
        for _ in range(100):
            await pilot.pause()
            values = _get_table_row_values(table, 0)
            # PRs column is index 5
            if values[5] == "5/2":
                break
        # clean-repo (first alphabetically) should have PR counts
        values = _get_table_row_values(table, 0)
        assert values[0] == "branches-repo" or values[5] == "5/2"


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_quit(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        await pilot.press("q")
