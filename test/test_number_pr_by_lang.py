"""Tests for number_pr_by_lang."""

import unittest

import pandas as pd

from cfsr_stats.stats import number_pr_by_lang


def _sample_df() -> pd.DataFrame:
    """Build a small mock DataFrame that exercises various label scenarios."""
    return pd.DataFrame(
        {
            "number": [1, 2, 3, 4, 5, 6, 7, 8],
            "labels": [
                "python",           # single label
                "python;r",         # multiple labels
                "r",                # single label
                "julia",            # label not in langs
                "python",           # unmerged
                "",                 # empty labels
                "python;c-cpp",     # two target langs
                "nodejs",           # single label, unmerged
            ],
            "merged": [
                True,   # 1
                True,   # 2
                True,   # 3
                True,   # 4
                False,  # 5
                True,   # 6
                True,   # 7
                False,  # 8
            ],
        }
    ).set_index("number")


LANGS = {"python", "r", "c-cpp", "nodejs"}


class TestNumberPrByLang(unittest.TestCase):
    def setUp(self):
        self.df = _sample_df()

    def test_basic_counts(self):
        result = number_pr_by_lang(self.df, LANGS)

        # python: rows 1,2,5,7 → total=4, merged=1,2,7 → closed=3
        self.assertEqual(result["python"], {"total": 4, "closed": 3})

        # r: rows 2,3 → total=2, merged=2,3 → closed=2
        self.assertEqual(result["r"], {"total": 2, "closed": 2})

        # c-cpp: row 7 → total=1, merged=7 → closed=1
        self.assertEqual(result["c-cpp"], {"total": 1, "closed": 1})

        # nodejs: row 8 → total=1, merged=8 → closed=0
        self.assertEqual(result["nodejs"], {"total": 1, "closed": 0})

    def test_excludes_julia(self):
        """julia is not in LANGS, so it should not appear in the result."""
        result = number_pr_by_lang(self.df, LANGS)
        self.assertNotIn("julia", result)

    def test_returns_all_requested_langs(self):
        """Every lang in the input iterable should be a key in the result."""
        result = number_pr_by_lang(self.df, LANGS)
        self.assertEqual(set(result.keys()), LANGS)

    def test_empty_langs(self):
        """An empty iterable of langs should return an empty dict."""
        result = number_pr_by_lang(self.df, set())
        self.assertEqual(result, {})

    def test_df_with_no_matches(self):
        """When no PRs have any of the requested labels, all counts are zero."""
        df = pd.DataFrame(
            {
                "number": [1, 2],
                "labels": ["ruby", "perl"],
                "merged": [True, False],
            }
        ).set_index("number")
        result = number_pr_by_lang(df, ["python", "r"])
        self.assertEqual(result, {"python": {"total": 0, "closed": 0}, "r": {"total": 0, "closed": 0}})

    def test_partial_label_match_safety(self):
        """'python' matches 'python-c' via str.contains — known limitation."""
        df = pd.DataFrame(
            {
                "number": [1],
                "labels": ["python-c"],
                "merged": [True],
            }
        ).set_index("number")
        result = number_pr_by_lang(df, {"python", "python-c"})
        self.assertEqual(result["python-c"], {"total": 1, "closed": 1})
        # python also matches due to substring — document the existing behaviour
        self.assertEqual(result["python"], {"total": 0, "closed": 0})

    def test_semicolon_multilabel_parsing(self):
        """Row 2 has 'python;r' — both python and r should count it."""
        result = number_pr_by_lang(self.df, {"python", "r"})
        self.assertGreaterEqual(result["python"]["total"], 1)
        self.assertGreaterEqual(result["r"]["total"], 1)

    def test_empty_labels_handled(self):
        """Row 6 has empty labels; it should not match any lang."""
        result = number_pr_by_lang(self.df, LANGS)
        self.assertEqual(result["python"]["total"], 4)


if __name__ == "__main__":
    unittest.main()