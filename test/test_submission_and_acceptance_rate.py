"""Tests for submission_and_acceptance_rate."""

import unittest
from io import StringIO

import pandas as pd

from cfsr_stats.stats import submission_and_acceptance_rate


def _sample_df() -> pd.DataFrame:
    """Build a mock DataFrame with PRs across multiple years."""
    return pd.DataFrame(
        {
            "number": [1, 2, 3, 4, 5, 6, 7],
            "created_at": pd.to_datetime([
                "2024-01-01",
                "2024-06-15",
                "2025-01-01",
                "2025-03-01",
                "2025-06-01",
                "2026-01-01",
                "2026-06-01",
            ]),
            "merged": [True, False, True, True, False, True, True],
        }
    ).set_index("number")


_REALISTIC_CSV = """\
number,merged,merged_by,created_at
34640,True,reviewer1,2026-08-26 11:53:09+00:00
34641,True,reviewer2,2026-08-26 16:00:41+00:00
34642,False,,2026-08-26 16:39:24+00:00
34643,True,reviewer2,2026-08-26 16:43:04+00:00
34644,True,reviewer3,2026-08-26 17:02:00+00:00
34645,False,reviewer4,2026-08-26 17:03:49+00:00
34646,True,reviewer2,2026-08-26 17:39:46+00:00
34647,True,reviewer2,2026-08-26 18:07:54+00:00
34648,True,reviewer2,2026-08-26 18:51:09+00:00
34649,True,reviewer5,2026-08-26 21:14:00+00:00
34650,True,reviewer1,2026-08-26 23:28:26+00:00
34651,True,reviewer6,2026-08-27 04:19:16+00:00
34652,False,reviewer7,2026-08-27 05:20:40+00:00
34653,False,,2026-08-27 06:33:21+00:00
34654,False,,2026-08-27 07:30:02+00:00
34655,False,,2026-08-27 12:23:43+00:00
34656,False,,2026-08-27 13:57:26+00:00
34657,False,reviewer8,2026-08-27 14:07:09+00:00
34658,False,,2026-08-27 14:10:34+00:00
34659,False,,2026-08-27 18:34:01+00:00
34660,False,,2026-08-27 19:22:38+00:00
34661,False,,2026-08-27 20:28:32+00:00
34662,True,reviewer1,2026-08-27 22:50:13+00:00
34663,False,,2026-08-28 08:31:15+00:00
34664,False,,2026-08-28 08:49:06+00:00
"""


class TestSubmissionAndAcceptanceRate(unittest.TestCase):
    def setUp(self):
        self.df = _sample_df()
        self.realistic_df = (
            pd.read_csv(StringIO(_REALISTIC_CSV), parse_dates=["created_at"])
            .set_index("number")
        )

    def test_basic_counts(self):
        result = submission_and_acceptance_rate(self.df)

        # 2024: 2 PRs (index 1,2), merged=1
        self.assertEqual(result[2024]["submission"], 2)
        self.assertEqual(result[2024]["acceptance"], 1)

        # 2025: 3 PRs (index 3,4,5), merged=2
        self.assertEqual(result[2025]["submission"], 3)
        self.assertEqual(result[2025]["acceptance"], 2)

        # 2026: 2 PRs (index 6,7), merged=2
        self.assertEqual(result[2026]["submission"], 2)
        self.assertEqual(result[2026]["acceptance"], 2)

    def test_submission_rate_is_per_day(self):
        """Submission rate = total_prs / (max_date - min_date) in days."""
        result = submission_and_acceptance_rate(self.df)
        # 2024: span = June 15 - Jan 1 = 166 days
        self.assertEqual(result[2024]["submission_rate"], round(2 / 166, 2))
        # 2025: span = June 1 - Jan 1 = 151 days
        self.assertEqual(result[2025]["submission_rate"], round(3 / 151, 2))

    def test_acceptance_rate_is_per_day(self):
        result = submission_and_acceptance_rate(self.df)
        # 2024: 1 / 166
        self.assertEqual(result[2024]["acceptance_rate"], round(1 / 166, 2))
        # 2025: 2 / 151
        self.assertEqual(result[2025]["acceptance_rate"], round(2 / 151, 2))

    def test_all_years_present(self):
        result = submission_and_acceptance_rate(self.df)
        self.assertIn(2024, result)
        self.assertIn(2025, result)
        self.assertIn(2026, result)
        self.assertEqual(len(result), 3)

    def test_single_pr_in_year_uses_one_day(self):
        """A year with a single PR has zero date span; function falls back to 1 day."""
        df = pd.DataFrame(
            {
                "number": [1],
                "created_at": pd.to_datetime(["2024-05-01"]),
                "merged": [True],
            }
        ).set_index("number")
        result = submission_and_acceptance_rate(df)
        self.assertEqual(result[2024]["submission"], 1)
        self.assertEqual(result[2024]["submission_rate"], 1.0)
        self.assertEqual(result[2024]["acceptance"], 1)
        self.assertEqual(result[2024]["acceptance_rate"], 1.0)

    def test_empty_dataframe(self):
        df = pd.DataFrame(
            {"number": [], "created_at": pd.Series([], dtype="datetime64[ns]"), "merged": []}
        ).set_index("number")
        result = submission_and_acceptance_rate(df)
        self.assertEqual(result, {})

    def test_all_prs_unmerged(self):
        df = pd.DataFrame(
            {
                "number": [1, 2],
                "created_at": pd.to_datetime(["2024-01-01", "2024-06-01"]),
                "merged": [False, False],
            }
        ).set_index("number")
        result = submission_and_acceptance_rate(df)
        self.assertEqual(result[2024]["submission"], 2)
        self.assertEqual(result[2024]["acceptance"], 0)
        self.assertEqual(result[2024]["acceptance_rate"], 0.0)

    def test_realistic_data_counts(self):
        """Verify counts against the mock CSV data."""
        result = submission_and_acceptance_rate(self.realistic_df)

        # All rows are in 2026
        self.assertIn(2026, result)
        self.assertEqual(len(result), 1)

        # merged=True: 34640, 34641, 34643, 34644, 34646, 34647, 34648, 34649, 34650, 34651, 34662 = 11
        # merged=False: 34642, 34645, 34652, 34653, 34654, 34655, 34656, 34657, 34658, 34659, 34660, 34661, 34663, 34664 = 14
        # Total = 25
        self.assertEqual(result[2026]["submission"], 25)
        self.assertEqual(result[2026]["acceptance"], 11)

    def test_realistic_data_rate(self):
        """Verify rate calculation against the mock CSV data.

        Span: 2026-08-26 11:53:09 → 2026-08-28 08:49:06 ≈ 1.87... days
        """
        result = submission_and_acceptance_rate(self.realistic_df)
        self.assertAlmostEqual(result[2026]["submission_rate"], 25 / 1.87, places=0)
        self.assertAlmostEqual(result[2026]["acceptance_rate"], 11 / 1.87, places=0)