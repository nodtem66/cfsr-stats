import json
import os
import sys

import dotenv
import requests

# Load .env to environment
dotenv.load_dotenv(".env", override=True)

# Required config
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
if not GITHUB_API_TOKEN:
    print("Please define GITHUB_API_TOKEN in .env")
    sys.exit(1)

# Optional config
def load_env_or_default(key: str, default_value: str):
    _val = os.getenv(key)
    return _val if _val else default_value

API_URL = load_env_or_default("API_URL", "https://api.github.com")
GRAPHQL_URL = load_env_or_default("GRAPHQL_URL", "https://api.github.com/graphql")
CURSOR_FILE = load_env_or_default("CURSOR_FILE", "cursor.json")
CSV_FILE = load_env_or_default("CSV_FILE", "pr_data.csv")
_LANG_LABELS = load_env_or_default("LANG_LABELS", "R,java,julia,ruby,nodejs,python,c-cpp,perl,rust,python-c,go")
TIME_TO_MERGE_JSON = load_env_or_default("TIME_TO_MERGE_JSON", "./stats/time_to_merge_days.json")
NUMBER_PR_BY_LANG = load_env_or_default("NUMBER_PR_BY_LANG", "./stats/number_pr_by_lang.json")
SUBMISSION_RATE_JSON = load_env_or_default("SUBMISSION_RATE_JSON", "./stats/rate.json")
TOP_REVIEWER_ALL_TIME_JSON = load_env_or_default("TOP_REVIEWER_ALL_TIME_JSON", "./stats/top_reviewer_all_time.json")
TOP_REVIEWER_6MONTH_JSON = load_env_or_default("TOP_REVIEWER_6MONTH_JSON", "./stats/top_reviewer_6month.json")
_FORMAT_DECIMAL_POINT = load_env_or_default("FORMAT_DECIMAL_POINT", "2")

headers = {
    "Authorization": f"Bearer {GITHUB_API_TOKEN}",
    "Content-Type": "application/vnd.github+json",
}

try:
    LANG_LABELS: set[str] = {l.strip() for l in _LANG_LABELS.split(",")}
except AttributeError:
    print(f"Error: LANG_LABELS expected a string, got {type(_LANG_LABELS).__name__}")
    sys.exit(1)

try:
    FORMAT_DECIMAL_POINT: int = int(_FORMAT_DECIMAL_POINT)
except ValueError:
    print(f"Error: FORMAT_DECIMAL_POINT must be an integer, got '{_FORMAT_DECIMAL_POINT}'")
    sys.exit(1)

def print_config():
    print(
        f"Cursor file: {CURSOR_FILE}\n"
        f"API URL: {API_URL}\n"
        f"GraphQL URL: {GRAPHQL_URL}\n"
        f"GitHub API Token: **********{GITHUB_API_TOKEN[-4:]}" if GITHUB_API_TOKEN else "GitHub API Token: Not Set"
    )

def print_rate_limit():
    response = requests.get(API_URL + "/rate_limit", headers=headers)
    response.raise_for_status()

    resources = response.json()["resources"]
    graphql = resources["graphql"]
    remaining = graphql["remaining"]
    limit = graphql["limit"]
    print(f"GitHub GraphQL Rate Limit remaining: {remaining}/{limit}")

def load_cursor_json() -> dict[int, str]:
    cursors: dict[int, str] = {}
    try:
        with open(CURSOR_FILE, "r", encoding="utf-8") as f:
            cursors = { int(k): str(v) for k,v in json.load(f).items() }
    except FileNotFoundError:
        print(f"Error file not found: {CURSOR_FILE}")
    except json.JSONDecodeError as e:
        print(e)
    return cursors