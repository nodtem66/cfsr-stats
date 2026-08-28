"""Fetch GraphQL cursors for all PRs (entry point)."""

from cfsr_stats import config
from cfsr_stats.fetch_cursors import get_latest_cursor, save_cursors

if __name__ == "__main__":
    config.print_config()
    config.print_rate_limit()

    cursors = get_latest_cursor()
    if cursors:
        save_cursors(cursors, config.CURSOR_FILE)
        print(f"Saved cursor for latest PR to {config.CURSOR_FILE}")