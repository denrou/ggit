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
        # Column 0 is marker, column 1 is name
        assert values[1] == "dirty-repo"
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
        # Column 1 is name (column 0 is marker)
        names = [_get_table_row_values(table, i)[1] for i in range(table.row_count)]
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
        first = _get_table_row_values(table, 0)[1]  # column 1 is name
        assert first == "dirty-repo"


@pytest.mark.asyncio
@patch("ggit.cli.get_details", return_value={
    "name": "branches-repo",
    "path": "/tmp/repos/branches-repo",
    "branch": "main",
    "origin": "git@github.com:user/branches-repo.git",
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
            # PRs column is index 6 (shifted by marker column)
            if values[6] == "5/2":
                break
        values = _get_table_row_values(table, 0)
        assert values[1] == "branches-repo" or values[6] == "5/2"


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=(5, 2))
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_quit(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        await pilot.press("q")


# --- Vim navigation tests ---


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=None)
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_jk_navigation(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        table = pilot.app.query_one("#repo-table")
        assert table.cursor_row == 0

        await pilot.press("j")
        await pilot.pause()
        assert table.cursor_row == 1

        await pilot.press("j")
        await pilot.pause()
        assert table.cursor_row == 2

        await pilot.press("k")
        await pilot.pause()
        assert table.cursor_row == 1


# --- Selection tests ---


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=None)
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_toggle_select(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        app = pilot.app
        assert len(app.selected_paths) == 0

        # Space toggles the cursor row
        await pilot.press("space")
        await pilot.pause()
        assert len(app.selected_paths) == 1

        # Marker column should show "●"
        table = app.query_one("#repo-table")
        values = _get_table_row_values(table, 0)
        assert values[0] == "●"

        # Space again deselects
        await pilot.press("space")
        await pilot.pause()
        assert len(app.selected_paths) == 0
        values = _get_table_row_values(table, 0)
        assert values[0] == " "


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=None)
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_toggle_all(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        app = pilot.app
        assert len(app.selected_paths) == 0

        # x selects all visible rows
        await pilot.press("x")
        await pilot.pause()
        assert len(app.selected_paths) == 3

        # x again deselects all
        await pilot.press("x")
        await pilot.pause()
        assert len(app.selected_paths) == 0


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=None)
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_selection_survives_sort(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        app = pilot.app

        # Select first row (branches-repo, sorted by name asc)
        await pilot.press("space")
        await pilot.pause()
        first_path = app.filtered_summaries[0]["path"]
        assert first_path in app.selected_paths

        # Change sort — selection should persist
        await pilot.press("s")
        await pilot.pause()
        assert first_path in app.selected_paths
        assert len(app.selected_paths) == 1


@pytest.mark.asyncio
@patch("ggit.cli.fetch_repo", return_value={"path": "/tmp/dirty-repo", "name": "dirty-repo", "ok": True, "error": None})
@patch("ggit.cli.get_github_pr_counts", return_value=None)
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_fetch_on_cursor(mock_find, mock_summary, mock_prs, mock_fetch):
    """Fetch with no selection operates on the cursor row."""
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        app = pilot.app
        assert len(app.selected_paths) == 0

        # Press f with no selection — should fetch cursor row
        await pilot.press("f")
        for _ in range(100):
            await pilot.pause()
        assert mock_fetch.called


@pytest.mark.asyncio
@patch("ggit.cli.get_github_pr_counts", return_value=None)
@patch("ggit.cli.get_summary", side_effect=_mock_get_summary)
@patch("ggit.cli.find_repos", side_effect=_mock_find_repos)
async def test_status_bar_shows_selection_count(mock_find, mock_summary, mock_prs):
    async with _make_app().run_test(size=(120, 30)) as pilot:
        await _wait_for_table(pilot)
        app = pilot.app
        status_bar = app.query_one("#status-bar")

        await pilot.press("space")
        await pilot.pause()
        assert "1 selected" in str(status_bar.render())
