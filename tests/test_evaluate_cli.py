import csv
import tempfile
import unittest
from pathlib import Path

from evaluate import EvaluationError, evaluate_file
from src.llm import ContentPolicyViolationError
from src.schemas import Category, ClassificationResult, Urgency


class EvaluateFileTests(unittest.TestCase):
    def test_writes_ticket_classification_and_evidence_to_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_file = root / "tickets.txt"
            output_directory = root / "results"
            input_file.write_text(
                'Need access, please\nThe "checkout" app is down',
                encoding="utf-8",
            )
            calls = []

            def classifier(ticket):
                calls.append(ticket)
                if ticket.startswith("Need access"):
                    return ClassificationResult(
                        Category.ACCOUNT_ACCESS,
                        Urgency.HIGH,
                        "Cannot sign in before shift",
                    )
                return ClassificationResult(
                    Category.BUG_REPORT,
                    Urgency.MEDIUM,
                    "Checkout application is down",
                )

            output_file = evaluate_file(
                input_file, classifier=classifier, output_directory=output_directory
            )

            self.assertEqual(output_file.name, "tickets.txt.output.csv")
            self.assertEqual(calls, ["Need access, please", 'The "checkout" app is down'])
            with output_file.open(encoding="utf-8", newline="") as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(
            rows,
            [
                ["ticket", "category", "urgency", "evidence"],
                [
                    "Need access, please",
                    "account_access",
                    "high",
                    "Cannot sign in before shift",
                ],
                [
                    'The "checkout" app is down',
                    "bug_report",
                    "medium",
                    "Checkout application is down",
                ],
            ],
        )

    def test_classification_failure_reports_line_and_writes_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_file = root / "tickets.txt"
            output_directory = root / "results"
            input_file.write_text("First ticket\nSecond ticket", encoding="utf-8")
            calls = []

            def classifier(ticket):
                calls.append(ticket)
                if ticket == "Second ticket":
                    raise ValueError("invalid model response")
                return ClassificationResult(Category.OTHER, Urgency.LOW)

            with self.assertRaisesRegex(
                EvaluationError, "line 2: invalid model response"
            ):
                evaluate_file(
                    input_file,
                    classifier=classifier,
                    output_directory=output_directory,
                )

            self.assertEqual(calls, ["First ticket", "Second ticket"])
            self.assertFalse(output_directory.exists())

    def test_blank_line_is_reported_as_a_ticket_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_file = root / "tickets.txt"
            input_file.write_text("Ticket one\n\nTicket three", encoding="utf-8")

            def classifier(ticket):
                if not ticket.strip():
                    raise ValueError("Ticket description cannot be empty.")
                return ClassificationResult(Category.OTHER, Urgency.LOW)

            with self.assertRaisesRegex(EvaluationError, "line 2"):
                evaluate_file(input_file, classifier, root / "results")

    def test_content_policy_block_writes_error_row_and_continues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_file = root / "tickets.txt"
            output_directory = root / "results"
            input_file.write_text(
                "Ticket before block\nBlocked ticket\nTicket after block",
                encoding="utf-8",
            )
            calls = []

            def classifier(ticket):
                calls.append(ticket)
                if ticket == "Blocked ticket":
                    raise ContentPolicyViolationError("blocked by content policy")
                return ClassificationResult(
                    Category.OTHER, Urgency.LOW, "Routine IT request"
                )

            output_file = evaluate_file(input_file, classifier, output_directory)
            with output_file.open(encoding="utf-8", newline="") as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(calls, [
            "Ticket before block",
            "Blocked ticket",
            "Ticket after block",
        ])
        self.assertEqual(
            rows,
            [
                ["ticket", "category", "urgency", "evidence"],
                ["Ticket before block", "other", "low", "Routine IT request"],
                [
                    "Blocked ticket",
                    "",
                    "",
                    "ERROR on line 2: blocked by content policy",
                ],
                ["Ticket after block", "other", "low", "Routine IT request"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
