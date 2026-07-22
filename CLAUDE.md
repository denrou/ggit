#CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ggit is a Python TUI that scans directories for git repositories and displays an interactive overview of their status (branch, dirty/clean, PRs, last commit). Published on PyPI. Uses `uv` as package manager.

## Commands

```bash
# Install/sync dependencies
uv sync

# Run the TUI locally
uv run ggit [path]

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_cli.py::test_function_name -v
```

## Architecture

Five modules under `ggit/`:

- **`cli.py`** — Textual TUI app with two screens: `MainScreen` (DataTable with repo list, keybindings for sort/filter) and `DetailScreen` (single repo details, pushed on Enter). `GgitApp` manages state and two-phase background loading (scan + PR counts). Entry point: `main()`, which also dispatches the non-interactive `--json` mode (`run_json_report()`).
- **`repo_info.py`** — Repository data extraction using GitPython. `get_summary()` returns short status (modified/staged/untracked/ahead counts), `get_details()` returns full info (authors, branches), `fetch_repo()` and `prune_repo()` run git fetch/prune and return result dicts. Also handles GitHub URL parsing and PR count fetching via `gh` CLI.
- **`report.py`** — Non-interactive cleanup reports. `get_report()` builds a `RepoReport` (working-tree state, stashes, merged/gone branches, merged remote branches, worktrees, ahead/behind, default branch), `build_reports()` runs it in parallel over many repos, `needs_attention()` filters for `--dirty`, `reports_to_json()` serializes for stdout.
- **`config.py`** — Optional TOML config from `~/.config/ggit/config.toml` (`paths`, `github_prs`). `load_config()` returns a `Config` dataclass; raises `ValueError` on a broken file.
- **`scanner.py`** — `find_repos(path)` walks directory trees to discover `.git` folders, skipping hidden directories and pruning nested repos. Progress renders to stderr so stdout stays clean for `--json`.
- **`app.css`** — Textual CSS for screen layouts.

## Key Details

- Entry point: `ggit.cli:main`
- Runtime deps: `textual`, `GitPython`, `rich`, `tomli` (Python < 3.11 only)
- Dev deps: `pytest`, `pytest-asyncio`, `textual-dev`
- Build backend: `hatchling`
- Python >=3.9
- GitHub PR counts use the `gh` CLI (subprocess), not the GitHub API directly

## Keybindings

| Key    | Action                                  |
| ------ | --------------------------------------- |
| j / k  | Move cursor down / up                   |
| Enter  | Show details for selected repo          |
| Space  | Toggle select current row               |
| x      | Toggle select all visible rows          |
| f      | Fetch selected repos (or cursor row)    |
| p      | Prune selected repos (or cursor row)    |
| s      | Cycle sort: Name → Branch → Last Commit |
| r      | Toggle reverse sort                     |
| d      | Filter dirty repos only                 |
| c      | Filter clean repos only                 |
| a      | Show all repos (clear filter)           |
| q      | Quit                                    |
| Escape | Back (on detail screen)                 |
