"""
GitHub GraphQL requires cursor to query the pull requests
cursor.json maps the latest PR number to its cursor.
Define GITHUB_API_TOKEN in .env before running this script

Run this script to create or update `cursor.json`
Used by github action bot
"""
import json

import requests

import config


def get_latest_cursor() -> dict[str, str]:
    """Fetch only the latest PR number and its cursor from GitHub."""
    query = """
    query {
      repository(owner: "conda-forge", name: "staged-recipes") {
        pullRequests(first: 1, orderBy: { field: CREATED_AT, direction: DESC }) {
          edges {
            cursor
            node { number }
          }
        }
      }
    }
    """

    payload = {"query": query}
    response = requests.post(config.GRAPHQL_URL, json=payload, headers=config.headers)
    response.raise_for_status()
    json_res = response.json()

    if json_res.get("errors"):
        raise KeyError(json_res["errors"])

    edges = json_res["data"]["repository"]["pullRequests"]["edges"]
    if not edges:
        return {}

    edge = edges[0]
    number = edge["node"]["number"]
    cursor = edge["cursor"]
    print(f"Latest PR: #{number}")
    return {str(number): cursor}


if __name__ == "__main__":
    config.print_config()
    config.print_rate_limit()

    cursors = get_latest_cursor()
    if cursors:
        with open(config.CURSOR_FILE, "w") as f:
            json.dump(cursors, f, indent=0)
        print(f"Saved cursor for latest PR to {config.CURSOR_FILE}")
