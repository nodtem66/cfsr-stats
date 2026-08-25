# cfsr-stats — conda-forge/staged-recipes Review Statistics

[![Pixi](https://img.shields.io/badge/managed%20by-pixi-8A2BE2)](https://pixi.sh)

This project collects and analyzes statistics on the pull request review process for the [`conda-forge/staged-recipes`](https://github.com/conda-forge/staged-recipes) repository. It uses the GitHub GraphQL API to fetch PR metadata and computes a variety of metrics to help the conda-forge community understand the health and efficiency of the recipe submission and review workflow.

## Motivation

[conda-forge](https://conda-forge.org/) is a community-led conda channel that packages thousands of open-source projects. New recipes are submitted as pull requests to the [`staged-recipes`](https://github.com/conda-forge/staged-recipes) repository, where they are reviewed by a team of volunteer maintainers before being merged and made available to the community.

Understanding the dynamics of this review process is important for several reasons:

- **Reviewer workload awareness** — Knowing who the top reviewers are and how many PRs they handle helps the community recognize contributions and identify when a reviewer may be overburdened.
- **Time-to-merge transparency** — Tracking how long it takes for a recipe to go from submission to merge (broken down by language) helps set contributor expectations and highlights bottlenecks in the review pipeline.
- **Submission & acceptance trends** — Monitoring submission and acceptance rates over the years reveals how the project is growing and whether the review process is keeping pace with the influx of new recipes.
- **Language-specific insights** — Different language ecosystems (Python, R, Julia, Rust, etc.) have different community sizes and review requirements. Breaking down statistics by language label helps identify language-specific trends or issues.
- **Data-driven community decisions** — These statistics empower the conda-forge core team to make informed decisions about reviewer recruitment, process improvements, and automation priorities.

## Features

- **PR Data Collection** — Fetches all pull requests from `conda-forge/staged-recipes` via the GitHub GraphQL API, including metadata such as author, labels, merge status, and timestamps.
- **Cursor-based Incremental Updates** — Uses GraphQL cursor pagination to efficiently fetch only new or updated PRs, making daily updates fast and lightweight.
- **Language Breakdown** — Categorizes PRs by language labels (Python, R, Julia, Rust, Go, Java, Ruby, Node.js, C/C++, Perl, and Python-with-C-extensions).
- **Time-to-Merge Statistics** — Computes min, median, and 95th percentile time-to-merge (in days) for each language.
- **Submission & Acceptance Rates** — Calculates yearly submission and acceptance rates (PRs per day).
- **Top Reviewer Rankings** — Identifies the most active reviewers both all-time and in the last 6 months, broken down by language.
- **Jupyter Notebooks** — Includes notebooks for exploring and visualizing the collected data.

## Getting Started

### Prerequisites

- [Pixi](https://pixi.sh/latest/) (recommended) or a Python 3.13 environment
- A [GitHub personal access token](https://github.com/settings/tokens) with `repo` scope

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/cfsr-stats.git
   cd cfsr-stats
   ```

2. **Set up the environment with Pixi**

   ```bash
   pixi install
   ```

3. **Configure your GitHub token**

   Create a `.env` file in the project root:

   ```
   GITHUB_API_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
   ```

### Usage

#### 1. Fetch cursors (initial setup)

```bash
pixi run python fetch_cursor_json.py
```

This populates `cursor.json` with GraphQL cursors for all PRs.

#### 2. Fetch all PR data

```bash
pixi run python fetch_all_pr.py
```

This creates `pr_data.csv` with metadata for every PR.

#### 3. Update PR data (daily)

```bash
pixi run python update_pr.py
```

This incrementally adds new PRs and updates the status of recently opened ones.

#### 4. Compute statistics

```bash
pixi run python update_stats.py
```

This generates all JSON files in the `stats/` directory.

### Automated Updates with GitHub Actions

The repository includes a scheduled GitHub Actions workflow (`.github/workflows/update-stats.yml`) that runs daily at 06:00 UTC. The workflow:

1. Checks out the repository
2. Sets up the Pixi environment (with caching)
3. Runs `fetch_cursor_json.py` to update GraphQL cursors
4. Runs `update_pr.py` to fetch new and updated PRs
5. Runs `update_stats.py` to recompute all statistics
6. Commits and pushes any changes back to the repository

You can also trigger the workflow manually from the **Actions** tab in GitHub.

> **Note:** The workflow requires a `GH_API_TOKEN` repository secret. Create one in your repository settings under **Settings → Secrets and variables → Actions** with a [GitHub personal access token](https://github.com/settings/tokens) that has `repo` scope.

## Statistics Overview

### PR Counts by Language (`number_pr_by_lang.json`)

Total and merged PR counts for each language label, giving a quick view of which language ecosystems are most active.

### Time to Merge (`time_to_merge_days.json`)

Min, median, and 95th percentile time-to-merge (in days) by language. Python recipes typically merge fastest (median ~1.4 days), while Julia recipes tend to take longer (median ~67 days).

### Submission & Acceptance Rates (`rate.json`)

Yearly breakdown of how many PRs were submitted and accepted, along with daily rates. The project has grown from ~39 submissions in 2015 to thousands per year.

### Top Reviewers (`top_reviewer_all_time.json`, `top_reviewer_6month.json`)

Rankings of the most active reviewers, with per-language breakdowns. This highlights the individuals who contribute most significantly to the review process.

## License

This project is available under the terms of the [BSD-3-Clause license](LICENSE).