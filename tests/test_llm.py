import unittest
from unittest.mock import Mock, patch

from openai import BadRequestError

from src.llm import ContentPolicyViolationError, ask


def bad_request(body):
    return BadRequestError(
        "Bad request",
        response=Mock(status_code=400, headers={}),
        body=body,
    )


class LlmContentPolicyTests(unittest.TestCase):
    @patch("src.llm.get_client")
    def test_translates_provider_content_filter_error(self, get_client):
        provider_error = bad_request(
            {
                "error": {
                    "code": "invalid_request_error",
                    "provider_specific_fields": {
                        "innererror": {"code": "ResponsibleAIPolicyViolation"},
                        "inner_error": {"code": "ResponsibleAIPolicyViolation"},
                        "azure_error": {"code": "content_filter"},
                    },
                }
            }
        )
        get_client.return_value.chat.completions.create.side_effect = provider_error

        with self.assertRaises(ContentPolicyViolationError) as caught:
            ask("Ticket text")

        self.assertIs(caught.exception.__cause__, provider_error)

    @patch("src.llm.get_client")
    def test_reraises_other_bad_request_errors(self, get_client):
        provider_error = bad_request({"error": {"code": "invalid_request_error"}})
        get_client.return_value.chat.completions.create.side_effect = provider_error

        with self.assertRaises(BadRequestError) as caught:
            ask("Ticket text")

        self.assertIs(caught.exception, provider_error)


if __name__ == "__main__":
    unittest.main()
