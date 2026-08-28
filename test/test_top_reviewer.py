"""Tests for top_reviewer."""

import unittest
from io import StringIO

import pandas as pd

from cfsr_stats.stats import top_reviewer


def _sample_df() -> pd.DataFrame:
    """Build a mock DataFrame with known reviewer patterns."""
    return pd.DataFrame(
        {
            "number": [1, 2, 3, 4, 5, 6, 7, 8],
            "labels": [
                "python",
                "python;r",
                "r",
                "julia",
                "python",
                "",
                "python;c-cpp",
                "nodejs",
            ],
            "merged_by": [
                "alice", #1
                "bob",   #2
                "alice", #3
                "carol", #4
                "bob",   #5
                "alice", #6
                "bob",   #7
                "",      #8
            ],
        }
    ).set_index("number")


_LANGS = {"python", "r", "c-cpp", "nodejs"}

_REALISTIC_CSV = """\
number,labels,merged_by
34640,review-requested;python,reviewer1
34641,,reviewer2
34642,,
34643,,reviewer2
34644,review-requested;python,reviewer3
34645,,reviewer4
34646,,reviewer2
34647,,reviewer2
34648,,reviewer2
34649,review-requested;python,reviewer5
34650,review-requested;python,reviewer1
34651,review-requested;rust,reviewer6
34652,,reviewer7
34653,,
34654,review-requested;rust,
34655,,
34656,review-requested;c-cpp,
34657,review-requested;python,reviewer8
34658,,
34659,review-requested;python,
34660,,
34661,,
34662,review-requested;python,reviewer1
34663,,
34664,,
"""


class TestTopReviewer(unittest.TestCase):
    def setUp(self):
        self.df = _sample_df()
        self.realistic_df = (
            pd.read_csv(StringIO(_REALISTIC_CSV))
            .set_index("number")
        )

    # --- Basic mock-data tests ---

    def test_top_reviewer_counts(self):
        """Verify per-reviewer and per-language counts."""
        result = top_reviewer(self.df, _LANGS)

        # alice: merged python(#1), r(#3), no-label(#6) → python=1, r=1, total=3
        self.assertEqual(result["alice"]["python"], 1)
        self.assertEqual(result["alice"]["r"], 1)
        self.assertEqual(result["alice"]["c-cpp"], 0)
        self.assertEqual(result["alice"]["nodejs"], 0)
        self.assertEqual(result["alice"]["total"], 3)

        # bob: merged python;r(#2), python(#5), python;c-cpp(#7) → python=3, r=1, c-cpp=1
        self.assertEqual(result["bob"]["python"], 3)
        self.assertEqual(result["bob"]["r"], 1)
        self.assertEqual(result["bob"]["c-cpp"], 1)
        self.assertEqual(result["bob"]["nodejs"], 0)
        self.assertEqual(result["bob"]["total"], 3)

    def test_empty_merged_by_excluded(self):
        """Rows with empty merged_by should not appear in result."""
        result = top_reviewer(self.df, _LANGS)
        # row 8 has merged_by="" → should not be a key
        self.assertNotIn("", result)
        self.assertNotIn(None, result)

    def test_requested_langs_as_keys(self):
        """Every requested lang should appear in each reviewer's per-lang dict."""
        result = top_reviewer(self.df, _LANGS)
        for counts in result.values():
            self.assertEqual(set(counts.keys()), _LANGS | {"total"})

    def test_empty_langs(self):
        """An empty iterable of langs returns reviewers with just total."""
        result = top_reviewer(self.df, set())
        # alice should still appear, with only "total"
        self.assertIn("alice", result)
        self.assertEqual(result["alice"], {"total": 3})

    def test_empty_dataframe(self):
        df = pd.DataFrame(
            {
                "number": [],
                "labels": pd.Series([], dtype="object"),
                "merged_by": pd.Series([], dtype="object"),
            }
        ).set_index("number")
        result = top_reviewer(df, {"python"})
        self.assertEqual(result, {})

    def test_only_empty_merged_by(self):
        """No reviewer data at all → empty result."""
        df = pd.DataFrame(
            {
                "number": [1, 2],
                "labels": ["python", "r"],
                "merged_by": ["", ""],
            }
        ).set_index("number")
        result = top_reviewer(df, {"python", "r"})
        self.assertEqual(result, {})

    def test_top_n_limit(self):
        """Only the top 10 reviewers by total merged PRs should be returned."""
        reviewers = [f"user{i}" for i in range(12)]
        df = pd.DataFrame(
            {
                "number": list(range(12)),
                "labels": ["python"] * 12,
                "merged_by": reviewers,
            }
        ).set_index("number")
        result = top_reviewer(df, {"python"})
        self.assertEqual(len(result), 10)

    # --- Realistic data tests ---

    def test_realistic_top_reviewer_counts(self):
        """Verify counts from the mock CSV data."""
        result = top_reviewer(self.realistic_df, {"python", "rust", "c-cpp"})

        # reviewer1: merged python(#34640, #34650, #34662) → python=3
        self.assertEqual(result["reviewer1"]["python"], 3)
        self.assertEqual(result["reviewer1"]["total"], 3)

        # reviewer2: all no-label PRs (#34641, #34643, #34646, #34647, #34648) → no langs
        self.assertEqual(result["reviewer2"]["python"], 0)
        self.assertEqual(result["reviewer2"]["total"], 5)

        # reviewer6: rust(#34651) → rust=1
        self.assertEqual(result["reviewer6"]["rust"], 1)
        self.assertEqual(result["reviewer6"]["total"], 1)

    def test_realistic_reviewers_without_labels(self):
        """Reviewer2 merged 5 PRs but none have language labels."""
        result = top_reviewer(self.realistic_df, {"python"})
        self.assertEqual(result["reviewer2"]["python"], 0)
        self.assertEqual(result["reviewer2"]["total"], 5)

    def test_realistic_empty_merged_by_not_counted(self):
        """Rows 34642, 34653, 34655, 34658, 34660, 34661, 34663, 34664 have no merged_by."""
        result = top_reviewer(self.realistic_df, {"python"})
        # No empty key or None key
        self.assertNotIn("", result)
        self.assertNotIn(None, result)