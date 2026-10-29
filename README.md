# ggit

An interactive TUI to scan directories for git repositories and get a quick overview of their status.

## Install

### Homebrew

```bash
brew tap denrou/tap
brew trust denrou/tap
brew install denrou/tap/ggit
```

### pip / uv

```bash
uv tool install ggit
```

## Usage

Launch the TUI scanning the current directory:

```bash
ggit
```

Scan a specific directory:

```bash
ggit ~/code
```

The TUI displays a table of all discovered repositories with their branch, status, origin, PR counts, and last commit date. Use the keyboard to navigate, sort, filter, and view details.

### JSON mode (non-interactive)

Print a machine-readable report to stdout instead of launching the TUI — handy for scripts, cron jobs, or LLM agents:

```bash
ggit --json ~/code
ggit --json --dirty          # only repos that need attention
ggit --json --no-prs         # skip GitHub PR lookups (faster, offline)
```

The report includes, per repository:

- working-tree state (modified/staged/untracked counts, `git status --short` lines)
- ahead/behind counts against the tracking branch
- stashes (index, date, message)
- local branches, flagged when merged into the default branch or when their upstream is gone
- remote branches already merged into the default branch
- worktrees (path, branch, dirty, prunable)
- origin, detected default branch, and open PR counts (via the `gh` CLI)

`--dirty` keeps only repositories with something to clean up: a dirty working tree, stashes, merged or gone branches, or stale worktrees.

### Configuration

ggit reads an optional config file from `~/.config/ggit/config.toml` (or `$XDG_CONFIG_HOME/ggit/config.toml`):

```toml
# Directories scanned when no path argument is given (default: current directory)
paths = ["~/code"]

# Look up open PR counts via the gh CLI (default: true)
github_prs = true
```

With `paths` set, running `ggit` (or `ggit --json`) from anywhere scans your usual code directories. Command-line paths always take precedence, and `--config FILE` points at an alternative file.

### Keybindings

| Key    | Action                                  |
| ------ | --------------------------------------- |
| j / k  | Move cursor down / up                   |
| Enter  | Show detailed info for selected repo    |
| Space  | Toggle select current row               |
| x      | Toggle select all visible rows          |
| f      | Fetch selected repos (or cursor row)    |
| p      | Prune selected repos (or cursor row)    |
| s      | Cycle sort: Name → Branch → Last Commit |
| r      | Toggle reverse sort                     |
| d      | Filter: dirty repos only                |
| c      | Filter: clean repos only                |
| a      | Show all repos (clear filter)           |
| q      | Quit                                    |
| Escape | Back (from detail screen)               |

### Status symbols

- `✓` clean
- `M` modified
- `+` staged
- `?` untracked
- `↑` ahead of remote

### Detail screen

Press Enter on any repo to see detailed info: branches, last fetch, and authors. Press Escape to go back.

## License

MIT
