# ggit

An interactive TUI to scan directories for git repositories and get a quick overview of their status.

## Install

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

### Keybindings

| Key | Action |
|-----|--------|
| Enter | Show detailed info for selected repo |
| s | Cycle sort: Name → Branch → Last Commit |
| r | Toggle reverse sort |
| d | Filter: dirty repos only |
| c | Filter: clean repos only |
| a | Show all repos (clear filter) |
| q | Quit |
| Escape | Back (from detail screen) |

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
