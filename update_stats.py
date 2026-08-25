"""
Update all json file in stats/
"""
import json
from collections import Counter
from collections.abc import Iterable

import pandas as pd

import config

SECONDS_IN_DAY = 60 * 60 * 24
DAYS_IN_MONTH = 30
DAYS_IN_SIX_MONTH = 6 * DAYS_IN_MONTH

# Unused
def get_labels(df: pd.DataFrame) -> set:
    labels = []
    for label in df["labels"].to_list():
        if label:
            l = [l.strip() for l in label.split(';')]
            labels.extend(l)
    return set(labels)

def number_pr_by_lang(df: pd.DataFrame, langs: Iterable) -> dict:
    count = {}
    for lang in langs:
        mask = df["labels"].str.contains(lang)
        total = len(df[mask])
        closed = len(df[mask & df["merged"]])
        count[lang] = {
            "total": total,
            "closed": closed
        }
    return count

def time_to_merge(df: pd.DataFrame, langs: Iterable) -> dict:
    ttm = {}
    duration = df['merged_at'] - df['created_at']
    for lang in langs:
        mask = df["labels"].str.contains(lang).dropna()
        ds = duration[mask].dropna().dt.total_seconds() / SECONDS_IN_DAY
        ttm[lang] = {
            "min": ds.min(),
            "median": ds.median(),
            "p95": ds.quantile(0.95)
        }
    return ttm

def submission_and_acceptance_rate(df: pd.DataFrame) -> dict:
    df_year = df["created_at"].dt.year
    rate = {}
    for year in range(df_year.min(), df_year.max()+1):
        mask = (df_year == year)
        _df = df[mask]
        total_prs = _df.shape[0]
        closed_prs = _df[_df["merged"]].shape[0]
        duration = _df["created_at"].max() - _df["created_at"].min()
        rate[year] = {
            "submission": total_prs,
            "submission_rate": total_prs / duration.days,
            "acceptance": closed_prs,
            "acceptance_rate": closed_prs / duration.days
        }
    return rate


def top_reviewer(df: pd.DataFrame, langs: Iterable) -> dict:
    reviewers_counter = Counter(df[df["merged_by"].str.len() > 0].merged_by.to_list())
    result = {}
    # Cache lang mask
    lang_mask: dict = {}
    for lang in langs:
        lang_mask[lang] = df["labels"].str.contains(lang).dropna()

    for user, total in reviewers_counter.most_common(10):
        user_mask = df["merged_by"] == user
        count = {lang: len(df[lang_mask[lang] & user_mask]) for lang in langs}
        count["total"] = total
        result[user] = count
    return result

def save_to_json(data: dict, path: str):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    df = pd.read_csv(config.CSV_FILE, index_col="number", na_filter=False)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["merged_at"] = pd.to_datetime(df["merged_at"])
    df["closed_at"] = pd.to_datetime(df["closed_at"])
   
    d = number_pr_by_lang(df, config.LANG_LABELS)
    save_to_json(d, config.NUMBER_PR_BY_LANG)

    d = time_to_merge(df, config.LANG_LABELS)
    save_to_json(d, config.TIME_TO_MERGE_JSON)

    d = submission_and_acceptance_rate(df)
    save_to_json(d, config.SUBMISSION_RATE_JSON)

    d = top_reviewer(df, config.LANG_LABELS)
    save_to_json(d, config.TOP_REVIEWER_ALL_TIME_JSON)

    latest_date = df["closed_at"].max()
    df_duration = latest_date - df["created_at"]
    prev_six_month_mask = df_duration.dt.days < DAYS_IN_SIX_MONTH
    d = top_reviewer(df[prev_six_month_mask], config.LANG_LABELS)
    save_to_json(d, config.TOP_REVIEWER_6MONTH_JSON)