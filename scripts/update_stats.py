"""Compute statistics and save to JSON files (entry point)."""

import pandas as pd

from cfsr_stats import config
from cfsr_stats.stats import (
    number_pr_by_lang,
    save_to_json,
    submission_and_acceptance_rate,
    time_to_merge,
    top_reviewer,
)

SECONDS_IN_DAY = 60 * 60 * 24
DAYS_IN_MONTH = 30
DAYS_IN_SIX_MONTH = 6 * DAYS_IN_MONTH

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