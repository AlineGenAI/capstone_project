import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation import run_eval
from src.schemas import Category, ClassificationResult, Urgency


class EvaluationTests(unittest.TestCase):
    def test_macro_f1_is_one_for_perfect_predictions(self):
        self.assertEqual(
            run_eval.macro_f1(["a", "b"], ["a", "b"], ["a", "b"]),
            1.0,
        )

    def test_evaluation_reports_metric_scores_and_failures(self):
        cases = [
            {"ticket": "access issue", "category": "account_access", "urgency": "high"},
            {"ticket": "broken app", "category": "bug_report", "urgency": "medium"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            cases_path = Path(directory) / "cases.jsonl"
            cases_path.write_text(
                "\n".join(json.dumps(case) for case in cases),
                encoding="utf-8",
            )

            def fake_classifier(ticket):
                if ticket == "broken app":
                    raise ValueError("invalid model output")
                return ClassificationResult(
                    category=Category.ACCOUNT_ACCESS, urgency=Urgency.HIGH
                )

            with patch.object(run_eval, "CASES_PATH", cases_path):
                report = run_eval.evaluate(fake_classifier)

        self.assertEqual(report["cases"], 2)
        self.assertEqual(report["category_accuracy"], 0.5)
        self.assertEqual(report["urgency_accuracy"], 0.5)
        self.assertEqual(report["invalid_or_failed_responses"], 1)


if __name__ == "__main__":
    unittest.main()
