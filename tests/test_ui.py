import unittest
from unittest.mock import Mock, patch

from src.app import TicketTriageApp


class TicketTriageAppTests(unittest.TestCase):
    def setUp(self):
        self.app = TicketTriageApp.__new__(TicketTriageApp)
        self.app.ticket_text = Mock()
        self.app.result_label = Mock()
        self.app.go_button = Mock()

    def test_blank_ticket_shows_validation_message(self):
        self.app.ticket_text.get.return_value = " \n "

        self.app.submit_ticket()

        self.app.result_label.configure.assert_called_once_with(
            text="Enter a ticket description before selecting GO."
        )
        self.app.go_button.configure.assert_not_called()

    @patch("src.app.threading.Thread")
    def test_go_starts_background_classification(self, thread):
        self.app.ticket_text.get.return_value = "The app is not loading"

        self.app.submit_ticket()

        self.app.go_button.configure.assert_called_once_with(state="disabled")
        self.app.result_label.configure.assert_called_once_with(
            text="Classifying ticket..."
        )
        thread.return_value.start.assert_called_once()
        self.assertEqual(
            thread.call_args.kwargs["args"], ("The app is not loading",)
        )


if __name__ == "__main__":
    unittest.main()
