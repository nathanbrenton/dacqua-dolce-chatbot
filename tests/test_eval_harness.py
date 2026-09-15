"""Tests for the raw-model evaluation definition."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals/cases/raw-model-baseline.json"


class EvaluationDefinitionTests(unittest.TestCase):
    def test_cases_are_well_formed(self) -> None:
        cases = json.loads(
            CASES.read_text(encoding="utf-8")
        )

        self.assertGreater(len(cases), 0)

        ids = set()

        for case in cases:
            self.assertIsInstance(case["id"], str)
            self.assertTrue(case["id"])

            self.assertNotIn(case["id"], ids)
            ids.add(case["id"])

            self.assertIsInstance(
                case["category"],
                str,
            )
            self.assertTrue(case["category"])

            self.assertIsInstance(
                case["prompt"],
                str,
            )
            self.assertTrue(case["prompt"])

            self.assertIsInstance(
                case["review_criteria"],
                list,
            )
            self.assertGreater(
                len(case["review_criteria"]),
                0,
            )

    def test_baseline_covers_key_categories(self) -> None:
        cases = json.loads(
            CASES.read_text(encoding="utf-8")
        )

        categories = {
            case["category"]
            for case in cases
        }

        self.assertIn(
            "general_water_knowledge",
            categories,
        )
        self.assertIn(
            "authoritative_business_data",
            categories,
        )
        self.assertIn(
            "policy",
            categories,
        )


if __name__ == "__main__":
    unittest.main()
