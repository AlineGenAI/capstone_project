import unittest
from unittest.mock import patch

from src.classifier import classify_ticket
from src.schemas import Category, Urgency


class ClassifyTicketTests(unittest.TestCase):
    @patch("src.classifier.llm.ask")
    def test_returns_validated_classification(self, ask):
        ask.return_value = (
            '{"category":"account_access","urgency":"high",'
            '"rationale":"The employee cannot sign in."}'
        )

        result = classify_ticket("I cannot sign in to my work account.")

        self.assertEqual(result.category, Category.ACCOUNT_ACCESS)
        self.assertEqual(result.urgency, Urgency.HIGH)
        self.assertEqual(result.rationale, "The employee cannot sign in.")
        ask.assert_called_once()
        self.assertIn("I cannot sign in", ask.call_args.args[0])

    @patch("src.classifier.llm.ask")
    def test_prompt_uses_business_impact_not_urgency_wording(self, ask):
        ask.return_value = (
            '{"category":"bug_report","urgency":"low",'
            '"rationale":"The issue does not prevent work."}'
        )

        result = classify_ticket(
            "ASAP!!! The logo is misaligned, but all functions work."
        )

        prompt = ask.call_args.kwargs["system"]
        self.assertEqual(result.urgency, Urgency.LOW)
        self.assertIn('"urgent" or "ASAP"', prompt)
        self.assertIn("exclamation marks", prompt)
        self.assertIn("high only when the customer is blocked from working", prompt)
        self.assertIn("no impact on the customer's ability to work", prompt)

    @patch("src.classifier.llm.ask")
    def test_prompt_uses_highest_urgency_for_multiple_requests(self, ask):
        ask.return_value = (
            '{"category":"bug_report","urgency":"high",'
            '"rationale":"The customer is blocked from working."}'
        )

        result = classify_ticket("Printer is slow; I am totally out of the system.")

        prompt = ask.call_args.kwargs["system"]
        self.assertEqual(result.urgency, Urgency.HIGH)
        self.assertIn("contains multiple requests", prompt)
        self.assertIn("urgency supported by any of them", prompt)

    @patch("src.classifier.llm.ask")
    def test_accepts_json_code_fence(self, ask):
        ask.return_value = '```json\n{"category":"other","urgency":"low"}\n```'

        result = classify_ticket("Question about the IT team's hours")

        self.assertEqual(result.category, Category.OTHER)
        self.assertEqual(result.urgency, Urgency.LOW)
        self.assertEqual(result.rationale, "")

    @patch("src.classifier.llm.ask")
    def test_rejects_unknown_category(self, ask):
        ask.return_value = '{"category":"password_reset","urgency":"low"}'

        with self.assertRaisesRegex(ValueError, "Unknown category"):
            classify_ticket("I need a password reset")

    @patch("src.classifier.llm.ask")
    def test_rejects_invalid_json(self, ask):
        ask.return_value = "not JSON"

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            classify_ticket("My laptop is broken")

    @patch("src.classifier.llm.ask")
    def test_rejects_unexpected_fields(self, ask):
        ask.return_value = (
            '{"category":"bug_report","urgency":"medium","priority":1}'
        )

        with self.assertRaisesRegex(ValueError, "unexpected fields"):
            classify_ticket("The app crashes")

    @patch("src.classifier.llm.ask")
    def test_does_not_call_api_for_blank_ticket(self, ask):
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            classify_ticket(" \n ")

        ask.assert_not_called()

    @patch("src.classifier.llm.ask")
    def test_surfaces_api_errors(self, ask):
        ask.side_effect = RuntimeError("service unavailable")

        with self.assertRaisesRegex(RuntimeError, "service unavailable"):
            classify_ticket("I cannot access the system")


if __name__ == "__main__":
    unittest.main()
