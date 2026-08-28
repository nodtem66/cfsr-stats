"""Pull Request data model and GitHub GraphQL fetching logic."""
import traceback
from datetime import datetime

import pandas as pd
import requests
from pydantic import BaseModel

from cfsr_stats.config import GRAPHQL_URL, headers
from cfsr_stats.simple_progressbar import print_progress

# Github GraphQL limit 100 nodes per request
PR_PER_REQUEST = 100


class PullRequest(BaseModel):
    number: int
    title: str
    merged: bool
    labels: list[str]
    author: str | None
    merged_by: str | None
    merged_at: datetime | None
    created_at: datetime | None
    closed_at: datetime | None

    @classmethod
    def from_graph(cls, node: dict):
        return cls(
            number=node["number"],
            title=node["title"],
            author=get_user_login(node["author"]),
            merged=node["merged"],
            labels=[n["name"] for n in node["labels"]["nodes"]],
            merged_by=get_user_login(node["mergedBy"]),
            merged_at=node["mergedAt"],
            closed_at=node["closedAt"],
            created_at=node["createdAt"],
        )

    @staticmethod
    def fields() -> list[str]:
        return ["number", "title", "author", "merged", "labels", "merged_by", "merged_at", "created_at", "closed_at"]

    def to_csv(self) -> str:
        return f"{self.number},{self.title.replace(',', '')},{self.author},{self.merged},{';'.join(self.labels)},{self.merged_by},{self.merged_at},{self.created_at},{self.closed_at}\n"

    def to_list(self) -> list:
        return [self.number, self.title.replace(",", ""), self.author, self.merged, ';'.join(self.labels), self.merged_by, self.merged_at, self.created_at, self.closed_at]


def get_user_login(node: dict) -> str | None:
    if node and node["login"]:
        return node["login"]
    return None


class FetchPRsError(Exception):
    pass


def fetch_prs_graphql(after: str | None = None, sort_by: str = "CREATED_AT"):
    query = f"""
    query($after: String) {{
      repository(owner: "conda-forge", name: "staged-recipes") {{
        pullRequests(
          first: {PR_PER_REQUEST},
          after: $after,
          orderBy: {{ field: { sort_by }, direction: DESC }}
        ) {{
          pageInfo {{
            hasNextPage
            endCursor
          }}
          nodes {{
            number
            title
            author {{ login }}
            closedAt
            createdAt
            merged
            mergedAt
            mergedBy {{ login }}
            labels(first:10) {{
              nodes {{ name }}
            }}
          }}
        }}
      }}
    }}
    """

    payload = {
        "query": query,
        "variables": {"after": after}
    }

    response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_pr(cursor: str | None = None, limit: int | None = None, sort_by: str = "CREATED_AT") -> list[PullRequest]:
    pr_list = []
    count = 0
    _cursor = cursor
    firstQuery = True
    # Loop until there is no data (_cursor = None)
    while _cursor or firstQuery:
        if firstQuery:
            firstQuery = False
        try:
            response = fetch_prs_graphql(_cursor, sort_by)
            if response.get("errors"):
                raise FetchPRsError(response["errors"])
            prs = response['data']['repository']['pullRequests']
            for node in prs['nodes']:
                pr = PullRequest.from_graph(node)
                pr_list.append(pr)
            _cursor = prs['pageInfo']['endCursor'] if prs['pageInfo']['hasNextPage'] else None
            print_progress(count)
            count += 1
            if limit and limit > 0 and count * PR_PER_REQUEST > limit:
                break
        except FetchPRsError as e:
            print(f"Error fetching PRs: {e}")
        except (requests.RequestException, KeyError, TypeError, ValueError) as e:
            print(f"Unexpected error: {_cursor}")
            traceback.print_exception(type(e), e, e.__traceback__)
    return pr_list


def fetch_pr_as_dataframe(cursor: str | None = None, limit: int | None = None, sort_by: str = "CREATED_AT") -> pd.DataFrame:
    _prs = fetch_pr(cursor, limit, sort_by)
    _data = [pr.to_list() for pr in _prs]
    return pd.DataFrame(_data, columns=PullRequest.fields()).set_index("number")