import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ggit.repo_info import format_status, get_details, get_summary, is_dirty
from ggit.scanner import find_repos

app = typer.Typer(help="Scan directories for git repositories and display an overview.")
console = Console()


def _dirty_clean_callback(ctx: typer.Context, param: typer.CallbackParam, value: bool) -> bool:
    """Ensure --dirty and --clean are mutually exclusive."""
    if value:
        other = "clean" if param.name == "dirty" else "dirty"
        if ctx.params.get(other):
            raise typer.BadParameter("--dirty and --clean are mutually exclusive.")
    return value


@app.command("list")
def list_repos(
    path: Optional[str] = typer.Argument(None, help="Directory to scan for git repos."),
    sort: str = typer.Option("name", "--sort", "-s", help="Sort by: name, branch, date."),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON."),
    reverse: bool = typer.Option(False, "--reverse", "-r", help="Reverse sort order."),
    dirty: bool = typer.Option(False, "--dirty", help="Show only repos with uncommitted or unpushed changes.", callback=_dirty_clean_callback),
    clean: bool = typer.Option(False, "--clean", help="Show only repos with a clean status.", callback=_dirty_clean_callback),
    min_local_branches: Optional[int] = typer.Option(None, "--min-local-branches", help="Show repos with at least N local branches."),
    min_remote_branches: Optional[int] = typer.Option(None, "--min-remote-branches", help="Show repos with at least N remote branches."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only output repository paths, one per line."),
) -> None:
    """Scan a directory for git repositories and display an overview table."""
    scan_path = path or "."
    repos = find_repos(scan_path)

    summaries: list[dict] = []
    for repo_path in repos:
        try:
            summaries.append(get_summary(repo_path))
        except Exception:
            pass

    if dirty:
        summaries = [s for s in summaries if is_dirty(s)]
    elif clean:
        summaries = [s for s in summaries if not is_dirty(s)]

    if min_local_branches is not None:
        summaries = [s for s in summaries if s["local_branches"] >= min_local_branches]

    if min_remote_branches is not None:
        summaries = [s for s in summaries if s["remote_branches"] >= min_remote_branches]

    sort_key = {"name": "name", "branch": "branch", "date": "last_commit"}.get(sort, "name")
    summaries.sort(key=lambda s: s[sort_key], reverse=reverse)

    if quiet:
        for s in summaries:
            print(s["path"])
        return

    if output_json:
        console.print(json.dumps(summaries, indent=2))
        return

    table = Table()
    table.add_column("Name")
    table.add_column("Path")
    table.add_column("Branch")
    table.add_column("Branches")
    table.add_column("Status")
    table.add_column("Last Commit")
    for s in summaries:
        branches = f"{s['local_branches']}/{s['remote_branches']}"
        status = format_status(s)
        table.add_row(s["name"], s["path"], s["branch"], branches, status, s["last_commit"])
    console.print(table)
    console.print(f"Found {len(summaries)} repositories")


@app.command("info")
def info_repo(
    path: str = typer.Argument(..., help="Path to the git repository."),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON."),
) -> None:
    """Show detailed info about a single git repository."""
    repo_path = Path(path).resolve()
    details = get_details(repo_path)

    if output_json:
        console.print(json.dumps(details, indent=2))
        return

    console.print(f"Repository: {details['name']}")
    console.print(f"Current branch: {details['branch']}")
    console.print(f"Local branches: {', '.join(details['local_branches'])}")
    console.print(f"Remote branches: {', '.join(details['remote_branches'])}")
    console.print(f"Last commit: {details['last_commit']}")
    console.print(f"Last fetch: {details['last_fetch'] or 'N/A'}")
    console.print(f"Authors: {', '.join(details['authors'])}")
