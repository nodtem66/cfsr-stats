"""
Run this script once for creating pr_data.csv
"""

import config
from pull_request import PullRequest, fetch_pr

if __name__ == "__main__":
    config.print_config()
    config.print_rate_limit()

    pr_list = fetch_pr()

    print(f"Fetched {len(pr_list)} PRs")
    with open(config.CSV_FILE, "w", encoding="utf-8") as f:
        f.write(",".join(PullRequest.fields()) + "\n")
        f.writelines(
            pr.to_csv()
            for pr in pr_list
        )