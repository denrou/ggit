import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, LoadingIndicator, Static

from ggit.repo_info import (
    format_status,
    get_details,
    get_github_pr_counts,
    get_summary,
    is_dirty,
    parse_github_repo,
)
from ggit.scanner import find_repos

COLUMNS = ["Name", "Branch", "Status", "Local", "Remote", "Open PRs", "My PRs", "Last Commit"]
SORT_KEYS = ["name", "branch", "last_commit"]
SORT_LABELS = ["Name", "Branch", "Last Commit"]


class DetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, summary: dict) -> None:
        super().__init__()
        self.summary = summary

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Loading details...", id="detail-content")
        yield Footer()

    def on_mount(self) -> None:
        self.load_details()

    @work(thread=True)
    def load_details(self) -> None:
        path = Path(self.summary["path"])
        try:
            details = get_details(path)
        except Exception:
            self.app.call_from_thread(self._show_error)
            return
        self.app.call_from_thread(self._show_details, details)

    def _show_error(self) -> None:
        label = self.query_one("#detail-content", Label)
        label.update(f"Error loading details for {self.summary['name']}")

    def _show_details(self, details: dict) -> None:
        label = self.query_one("#detail-content", Label)
        lines = [
            f"Repository: {details['name']}",
            f"Path: {details['path']}",
            f"Current branch: {details['branch']}",
            f"Origin: {details['origin'] or 'N/A'}",
            f"Local branches: {', '.join(details['local_branches'])}",
            f"Remote branches: {', '.join(details['remote_branches'])}",
            f"Last commit: {details['last_commit']}",
            f"Last fetch: {details['last_fetch'] or 'N/A'}",
            f"Authors: {', '.join(details['authors'])}",
        ]
        self.detail_text = "\n".join(lines)
        label.update(self.detail_text)

    def action_go_back(self) -> None:
        self.app.pop_screen()


class GgitApp(App):
    CSS_PATH = "app.css"
    TITLE = "ggit"

    BINDINGS = [
        Binding("s", "cycle_sort", "Sort", show=True),
        Binding("r", "toggle_reverse", "Reverse", show=True),
        Binding("d", "filter_dirty", "Dirty", show=True),
        Binding("c", "filter_clean", "Clean", show=True),
        Binding("a", "filter_all", "All", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, path: str = ".") -> None:
        super().__init__()
        self.scan_path = path
        self.summaries: list[dict] = []
        self.filtered_summaries: list[dict] = []
        self.sort_column = "name"
        self.sort_reverse = False
        self.filter_mode = "all"

    def compose(self) -> ComposeResult:
        yield Header()
        yield LoadingIndicator(id="loading")
        table = DataTable(id="repo-table", cursor_type="row")
        for col in COLUMNS:
            table.add_column(col, key=col.lower().replace(" ", "_"))
        yield table
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#repo-table", DataTable).display = False
        self.load_repos()

    @work(thread=True)
    def load_repos(self) -> None:
        # Phase 1: scan and get summaries
        repos = find_repos(self.scan_path)
        summaries = []
        for repo_path in repos:
            try:
                summaries.append(get_summary(repo_path))
            except Exception:
                pass
        self.summaries = summaries
        self.call_from_thread(self._phase1_done)

        # Phase 2: fetch GitHub PR counts
        github_repos: dict = {}
        for s in summaries:
            origin = s.get("origin")
            if origin:
                gh_repo = parse_github_repo(origin)
                if gh_repo and gh_repo not in github_repos:
                    github_repos[gh_repo] = None

        if github_repos:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {repo: executor.submit(get_github_pr_counts, repo) for repo in github_repos}
                for repo, future in futures.items():
                    github_repos[repo] = future.result()

        for s in summaries:
            origin = s.get("origin")
            gh_repo = parse_github_repo(origin) if origin else None
            s["github_repo"] = gh_repo
            if gh_repo:
                pr_counts = github_repos.get(gh_repo)
                s["open_prs"] = pr_counts[0] if pr_counts else None
                s["my_prs"] = pr_counts[1] if pr_counts else None
            else:
                s["open_prs"] = None
                s["my_prs"] = None

        self.call_from_thread(self.refresh_table)

    def _phase1_done(self) -> None:
        for s in self.summaries:
            if "github_repo" not in s:
                origin = s.get("origin")
                gh_repo = parse_github_repo(origin) if origin else None
                s["github_repo"] = gh_repo
                s["open_prs"] = None
                s["my_prs"] = None
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = False
        table = self.query_one("#repo-table", DataTable)
        table.display = True
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one("#repo-table", DataTable)
        status_bar = self.query_one("#status-bar", Static)

        # Filter
        if self.filter_mode == "dirty":
            filtered = [s for s in self.summaries if is_dirty(s)]
        elif self.filter_mode == "clean":
            filtered = [s for s in self.summaries if not is_dirty(s)]
        else:
            filtered = list(self.summaries)

        # Sort
        filtered.sort(key=lambda s: s[self.sort_column], reverse=self.sort_reverse)
        self.filtered_summaries = filtered

        # Rebuild table
        table.clear()
        for s in filtered:
            status = format_status(s)
            open_prs = str(s["open_prs"]) if s.get("open_prs") is not None else ""
            my_prs = str(s["my_prs"]) if s.get("my_prs") is not None else ""
            table.add_row(
                s["name"], s["branch"], status,
                str(s["local_branches"]), str(s["remote_branches"]),
                open_prs, my_prs, s["last_commit"],
            )

        # Status bar
        sort_label = SORT_LABELS[SORT_KEYS.index(self.sort_column)]
        direction = "desc" if self.sort_reverse else "asc"
        filter_text = f" | Filter: {self.filter_mode}" if self.filter_mode != "all" else ""
        status_bar.update(
            f" {len(filtered)} repos | Sort: {sort_label} ({direction}){filter_text}"
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#repo-table", DataTable)
        idx = table.get_row_index(event.row_key)
        if 0 <= idx < len(self.filtered_summaries):
            self.push_screen(DetailScreen(self.filtered_summaries[idx]))

    def action_cycle_sort(self) -> None:
        current = SORT_KEYS.index(self.sort_column)
        self.sort_column = SORT_KEYS[(current + 1) % len(SORT_KEYS)]
        self.refresh_table()

    def action_toggle_reverse(self) -> None:
        self.sort_reverse = not self.sort_reverse
        self.refresh_table()

    def action_filter_dirty(self) -> None:
        self.filter_mode = "dirty"
        self.refresh_table()

    def action_filter_clean(self) -> None:
        self.filter_mode = "clean"
        self.refresh_table()

    def action_filter_all(self) -> None:
        self.filter_mode = "all"
        self.refresh_table()


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    app = GgitApp(path)
    app.run()
