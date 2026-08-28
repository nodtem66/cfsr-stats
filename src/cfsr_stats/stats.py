"""Compute statistics from PR data and save to JSON files in stats/."""
import json
from collections import Counter
from collections.abc import Iterable

import pandas as pd

from cfsr_stats import config

SECONDS_IN_DAY = 60 * 60 * 24
DAYS_IN_MONTH = 30
DAYS_IN_SIX_MONTH = 6 * DAYS_IN_MONTH


def _label_matches(labels_col, lang):
    """Check if lang is one of the semicolon-separated labels."""
    return labels_col.str.split(";").map(
        lambda labels: isinstance(labels, list) and lang in labels
    )


def number_pr_by_lang(df: pd.DataFrame, langs: Iterable) -> dict:
    count = {}
    for lang in langs:
        mask = _label_matches(df["labels"], lang)
        total = df[mask].shape[0]
        closed = df[mask & df["merged"]].shape[0]
        count[lang] = {
            "total": total,
            "closed": closed
        }
    return count


def time_to_merge(df: pd.DataFrame, langs: Iterable) -> dict:
    ttm = {}
    duration = (df["merged_at"] - df["created_at"]).dt.total_seconds() / SECONDS_IN_DAY
    for lang in langs:
        mask = _label_matches(df["labels"], lang)
        ds = duration[mask & df["merged"]].dropna()
        if ds.empty:
            ttm[lang] = {}
        else:
            ttm[lang] = {
                "min": round(ds.min(), config.FORMAT_DECIMAL_POINT),
                "median": round(ds.median(), config.FORMAT_DECIMAL_POINT),
                "p95": round(ds.quantile(0.95), config.FORMAT_DECIMAL_POINT)
            }
    return ttm


def submission_and_acceptance_rate(df: pd.DataFrame) -> dict:
    df_year = df["created_at"].dt.year.dropna().astype(int)
    if df_year.empty:
        return {}
    rate = {}
    for year in range(df_year.min(), df_year.max() + 1):
        _df = df[df_year == year]
        total_prs = len(_df)
        closed_prs = _df["merged"].sum()
        duration = _df["created_at"].max() - _df["created_at"].min()
        duration_days = max(duration.total_seconds() / SECONDS_IN_DAY, 1)
        rate[year] = {
            "submission": total_prs,
            "submission_rate": round(total_prs / duration_days, config.FORMAT_DECIMAL_POINT),
            "acceptance": int(closed_prs),
            "acceptance_rate": round(closed_prs / duration_days, config.FORMAT_DECIMAL_POINT)
        }
    return rate


def top_reviewer(df: pd.DataFrame, langs: Iterable) -> dict:
    merged_by = df["merged_by"].dropna()
    merged_by = merged_by[merged_by != ""]
    reviewers_counter = Counter(merged_by.to_list())
    result = {}
    # Cache lang mask
    lang_mask: dict = {}
    for lang in langs:
        lang_mask[lang] = _label_matches(df["labels"], lang)

    for user, total in reviewers_counter.most_common(10):
        user_mask = df["merged_by"] == user
        count = {lang: int((lang_mask[lang] & user_mask).sum()) for lang in langs}
        count["total"] = total
        result[user] = count
    return result


def save_to_json(data: dict, path: str):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)