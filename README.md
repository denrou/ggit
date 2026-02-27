# ggit

A CLI to scan directories for git repositories and get a quick overview of their status.

## Install

```bash
uv tool install ggit
```

## Usage

### List repositories

Scan the current directory for git repos:

```bash
ggit list
```

Scan a specific directory:

```bash
ggit list ~/code
```

Example output:

```
┌──────────┬─────────────────────┬────────┬──────────┬────────────┬─────────────┐
│ Name     │ Path                │ Branch │ Branches │ Status     │ Last Commit │
├──────────┼─────────────────────┼────────┼──────────┼────────────┼─────────────┤
│ my-app   │ /home/user/my-app   │ main   │ 3/5      │ ● 2M 1?   │ 2026-02-25  │
│ dotfiles │ /home/user/dotfiles │ master │ 1/1      │ ✓          │ 2026-02-20  │
│ api      │ /home/user/api      │ feat   │ 4/8      │ ● 1+ ↑2   │ 2026-02-27  │
└──────────┴─────────────────────┴────────┴──────────┴────────────┴─────────────┘
Found 3 repositories
```

Status symbols: `✓` clean, `M` modified, `+` staged, `?` untracked, `↑` ahead of remote.

### Filter dirty or clean repos

```bash
# Only repos with uncommitted or unpushed changes
ggit list ~/code --dirty

# Only clean repos
ggit list ~/code --clean
```

### Filter by branch count

```bash
# Repos with at least 5 local branches (time to clean up?)
ggit list ~/code --min-local-branches 5
```

### Sort and reverse

```bash
ggit list ~/code --sort date --reverse
```

Sort by `name` (default), `branch`, or `date`.

### Output as JSON

```bash
ggit list ~/code --json
```

### Quiet mode

Output only repository paths, useful for piping:

```bash
ggit list ~/code --dirty --quiet | xargs -I{} git -C {} status
```

### Get detailed info on a single repo

```bash
ggit info ./my-project
```

```
Repository: my-project
Current branch: main
Local branches: main, feat/auth, fix/typo
Remote branches: origin/main, origin/feat/auth
Last commit: 2026-02-27
Last fetch: 2026-02-26
Authors: Alice, Bob
```

## License

MIT
