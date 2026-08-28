"""Update PR data incrementally (entry point)."""

import pandas as pd

from cfsr_stats import config
from cfsr_stats.pull_request import fetch_pr_as_dataframe

if __name__ == "__main__":
    config.print_config()
    config.print_rate_limit()

    # Load cursor database
    cursors = config.load_cursor_json()

    if len(cursors) == 0:
        print("No cursors found in cursor.json.\nPlease run fetch_cursors to fetch the cursors first.")
        sys.exit(0)

    last_pr = max(cursors.keys())
    last_cursor = cursors[last_pr]
    print(f"Fetching PRs starting from cursor for PR #{last_pr}")

    # Load csv
    df = pd.read_csv(config.CSV_FILE, index_col="number")
    last_pr_from_csv = df.index.max()

    # Add missing PRs
    if last_pr > last_pr_from_csv:
        n_missing = last_pr - last_pr_from_csv
        print(f"Missing {n_missing} PRs")
        new_df = fetch_pr_as_dataframe(limit=n_missing)
        df = df.combine_first(new_df)

    # Update merged only previous 1000 PRs
    new_df = fetch_pr_as_dataframe(limit=1000, sort_by="UPDATED_AT")
    df = df.combine_first(new_df)
    df.to_csv(config.CSV_FILE)