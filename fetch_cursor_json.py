"""
Github GraphQL requires cursor to query the pull requests
cursor.json maps PR number to these cursors.
Define GITHUB_API_TOKEN in .env before running this script

Run this script to create or update `cursor.json`
Used by github action bot
"""
import json
import os

import requests

import config
from simple_progressbar import print_progress


def get_cursors(cursors: dict[str, str] | None) -> dict[str, str]:
    if cursors is None:
        _cursors: dict[str, str] = {}
    else:
        _cursors = cursors.copy()
    print(f"Fetching cursors for {len(_cursors)} PRs already in cursor.json")
    def build_query(after: str | None = None):
        query = """
      query($after: String) {
        repository(owner: "conda-forge", name: "staged-recipes") {
          pullRequests(
            first: 100,
            after: $after,
            orderBy: { field: CREATED_AT, direction: DESC}
          ) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              cursor
              node { number }
            }
          }
        }
      }
      """

        payload = {"query": query, "variables": {"after": after}}
        return payload

    nextPage = True
    after = None
    count = 0

    while nextPage:
        payload = build_query(after)
        response = requests.post(config.GRAPHQL_URL, json=payload, headers=config.headers)
        response.raise_for_status()
        json_res = response.json()

        if not json_res or json_res.get("errors", None):
            raise KeyError(json_res["errors"])

        prs = json_res["data"]["repository"]["pullRequests"]
        nextPage = prs["pageInfo"]["hasNextPage"]
        after = prs["pageInfo"]["endCursor"]

        for edge in prs["edges"]:
            cursor = edge["cursor"]
            number = edge["node"]["number"]
            if str(number) in _cursors:
                # If we already have a cursor for this PR number,
                # we can stop fetching more pages
                nextPage = False
                break
            _cursors[str(number)] = cursor
        print_progress(count)
        count += 1
    return _cursors


if __name__ == "__main__":
    config.print_config()
    config.print_rate_limit()
    cursors: dict[str, str] = {}
    if os.path.exists(config.CURSOR_FILE):
        with open(config.CURSOR_FILE, "r") as f:
            cursors = json.load(f)
    cursors = get_cursors(cursors)
    if len(cursors) > 0:
        sorted_cursors = dict(sorted(cursors.items(), key=lambda x: int(x[0]), reverse=True))
        with open(config.CURSOR_FILE, "w") as f:
            json.dump(sorted_cursors, f, indent=0)
