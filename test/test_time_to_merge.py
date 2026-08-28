"""Tests for time_to_merge."""

import unittest
from io import StringIO

import pandas as pd

from cfsr_stats.stats import time_to_merge

SECONDS_IN_DAY = 60 * 60 * 24


def _sample_df() -> pd.DataFrame:
    """Build a mock DataFrame with known durations for testing."""
    # PR 1: 0 days (merged instantly)
    # PR 2: 2 days
    # PR 3: 30 days
    # PR 4: 0 days, unmerged (should be excluded)
    return pd.DataFrame(
        {
            "number": [1, 2, 3, 4],
            "labels": ["python", "python;r", "r", "python"],
            "merged": [True, True, True, False],
            "merged_at": pd.to_datetime([
                "2026-08-28 12:00:00+00:00",
                "2026-08-30 12:00:00+00:00",
                "2026-09-27 12:00:00+00:00",
                "2026-09-01 12:00:00+00:00",
            ]),
            "created_at": pd.to_datetime([
                "2026-08-28 12:00:00+00:00",
                "2026-08-28 12:00:00+00:00",
                "2026-08-28 12:00:00+00:00",
                "2026-09-01 12:00:00+00:00",
            ]),
        }
    ).set_index("number")


_REALISTIC_CSV = """\
number,labels,merged,merged_by,merged_at,created_at
34640,review-requested;python,True,reviewer1,2026-08-26 12:36:55+00:00,2026-08-26 11:53:09+00:00
34641,,True,reviewer2,2026-08-26 21:23:16+00:00,2026-08-26 16:00:41+00:00
34643,,True,reviewer2,2026-08-27 08:45:51+00:00,2026-08-26 16:43:04+00:00
34644,review-requested;python,True,reviewer3,2026-08-27 07:15:40+00:00,2026-08-26 17:02:00+00:00
34646,,True,reviewer2,2026-08-27 08:42:09+00:00,2026-08-26 17:39:46+00:00
34647,,True,reviewer2,2026-08-27 10:20:49+00:00,2026-08-26 18:07:54+00:00
34648,,True,reviewer2,2026-08-27 10:20:21+00:00,2026-08-26 18:51:09+00:00
34649,review-requested;python,True,reviewer5,2026-08-26 22:37:10+00:00,2026-08-26 21:14:00+00:00
34650,review-requested;python,True,reviewer1,2026-08-27 09:57:02+00:00,2026-08-26 23:28:26+00:00
34651,review-requested;rust,True,reviewer6,2026-08-27 06:47:22+00:00,2026-08-27 04:19:16+00:00
34662,review-requested;python,True,reviewer1,2026-08-27 22:59:17+00:00,2026-08-27 22:50:13+00:00
"""


class TestTimeToMerge(unittest.TestCase):
    def setUp(self):
        self.df = _sample_df()
        self.realistic_df = (
            pd.read_csv(StringIO(_REALISTIC_CSV), parse_dates=["merged_at", "created_at"])
            .set_index("number")
        )

    # --- Basic mock-data tests ---

    def test_single_lang(self):
        """python: rows 1 (0d), 2 (2d) → p95 should linearly approximate to 1.9."""
        result = time_to_merge(self.df, ["python"])
        self.assertAlmostEqual(result["python"]["min"], 0)
        self.assertAlmostEqual(result["python"]["median"], 1)
        self.assertAlmostEqual(result["python"]["p95"], 1.9)

    def test_multiple_langs(self):
        """r: row 2 (2d), row 3 (30d)."""
        result = time_to_merge(self.df, ["python", "r"])
        self.assertAlmostEqual(result["r"]["min"], 2)
        self.assertAlmostEqual(result["r"]["median"], 16)
        self.assertAlmostEqual(result["r"]["p95"], 28.6)

    def test_all_requested_langs_in_result(self):
        result = time_to_merge(self.df, {"python", "r", "c-cpp"})
        self.assertIn("python", result)
        self.assertIn("r", result)
        self.assertIn("c-cpp", result)

    def test_lang_with_no_prs_returns_empty(self):
        """A lang with no PRs at all should get {}."""
        result = time_to_merge(self.df, ["c-cpp"])
        self.assertEqual(result["c-cpp"], {})

    def test_lang_with_only_unmerged_prs_returns_empty(self):
        """All PRs for a lang are unmerged → no duration data → {}."""
        df = pd.DataFrame(
            {
                "number": [1],
                "labels": ["python"],
                "merged": [False],
                "merged_at": pd.to_datetime(["2026-08-30 12:00:00+00:00"]),
                "created_at": pd.to_datetime(["2026-08-28 12:00:00+00:00"]),
            }
        ).set_index("number")
        result = time_to_merge(df, ["python"])
        self.assertEqual(result["python"], {})

    def test_empty_langs(self):
        result = time_to_merge(self.df, set())
        self.assertEqual(result, {})

    def test_empty_dataframe(self):
        df = pd.DataFrame(
            {
                "number": [],
                "labels": pd.Series([], dtype="object"),
                "merged": pd.Series([], dtype="bool"),
                "merged_at": pd.Series([], dtype="datetime64[ns, UTC]"),
                "created_at": pd.Series([], dtype="datetime64[ns, UTC]"),
            }
        ).set_index("number")
        result = time_to_merge(df, {"python"})
        self.assertEqual(result["python"], {})

    def test_no_merged_prs_at_all(self):
        """All rows are unmerged → every lang gets {}."""
        df = pd.DataFrame(
            {
                "number": [1, 2],
                "labels": ["python", "r"],
                "merged": [False, False],
                "merged_at": pd.to_datetime(["2026-08-30 12:00:00+00:00", "2026-08-31 12:00:00+00:00"]),
                "created_at": pd.to_datetime(["2026-08-28 12:00:00+00:00", "2026-08-28 12:00:00+00:00"]),
            }
        ).set_index("number")
        result = time_to_merge(df, {"python", "r"})
        self.assertEqual(result["python"], {})
        self.assertEqual(result["r"], {})

    # --- Realistic data tests ---

    def test_realistic_python_time_to_merge(self):
        """Verify python durations against the mock CSV data.

        Merged python PRs and their duration in days:
          34640: 2026-08-26 12:36:55 - 11:53:09 = 0.0304
          34644: 2026-08-27 07:15:40 - 2026-08-26 17:02:00 = 0.5928
          34649: 2026-08-26 22:37:10 - 21:14:00 = 0.0577
          34650: 2026-08-27 09:57:02 - 2026-08-26 23:28:26 = 0.4365
          34662: 2026-08-27 22:59:17 - 22:50:13 = 0.0063
        """
        result = time_to_merge(self.realistic_df, {"python"})
        _df = self.realistic_df.loc[[34640, 34644, 34649, 34650, 34662]]
        _duration = (_df["merged_at"] - _df["created_at"]).dt.total_seconds() / SECONDS_IN_DAY
        self.assertAlmostEqual(result["python"]["min"], _duration.min(), places=1)
        self.assertAlmostEqual(result["python"]["median"], _duration.median(), places=1)
        self.assertAlmostEqual(result["python"]["p95"], _duration.quantile(0.95), places=1)

    def test_realistic_rust_time_to_merge(self):
        """Only 34651 has rust label and is merged."""
        result = time_to_merge(self.realistic_df, {"rust"})
        # 34651: 06:47:22 - 04:19:16 = 2.47 hours ≈ 0.1029 days
        self.assertAlmostEqual(result["rust"]["min"], 0.1029, places=1)
        self.assertAlmostEqual(result["rust"]["median"], 0.1029, places=1)
        self.assertAlmostEqual(result["rust"]["p95"], 0.1029, places=1)