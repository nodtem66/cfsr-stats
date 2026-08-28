"""Fetch GraphQL cursors from GitHub."""
import json

import requests

from cfsr_stats.config import GRAPHQL_URL, headers


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
    response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
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


def save_cursors(cursors: dict[str, str], path: str):
    with open(path, "w") as f:
        json.dump(cursors, f, indent=0)