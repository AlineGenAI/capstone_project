"""Tkinter desktop application for classifying internal IT tickets."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from .classifier import ClassificationResult, classify_ticket


class TicketTriageApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Internal IT Ticket Triage")
        self.root.minsize(560, 420)

        container = ttk.Frame(root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Describe your IT issue or request",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(anchor=tk.W)

        self.ticket_text = tk.Text(container, height=8, wrap=tk.WORD)
        self.ticket_text.pack(fill=tk.BOTH, expand=True, pady=(8, 12))

        self.go_button = ttk.Button(
            container, text="GO", command=self.submit_ticket
        )
        self.go_button.pack(anchor=tk.E)

        ttk.Label(
            container, text="Classification", font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(16, 4))
        self.result_label = ttk.Label(
            container, text="Your category and urgency will appear here.", wraplength=520
        )
        self.result_label.pack(anchor=tk.W, fill=tk.X)

    def submit_ticket(self) -> None:
        ticket = self.ticket_text.get("1.0", "end-1c").strip()
        if not ticket:
            self.result_label.configure(text="Enter a ticket description before selecting GO.")
            return

        self.go_button.configure(state=tk.DISABLED)
        self.result_label.configure(text="Classifying ticket...")
        threading.Thread(
            target=self._classify_in_background, args=(ticket,), daemon=True
        ).start()

    def _classify_in_background(self, ticket: str) -> None:
        try:
            result = classify_ticket(ticket)
        except Exception as error:
            self.root.after(0, self._show_error, str(error))
        else:
            self.root.after(0, self._show_result, result)

    def _show_result(self, result: ClassificationResult) -> None:
        text = (
            f"Category: {result.category.value}\n"
            f"Urgency: {result.urgency.value}"
        )
        if result.rationale:
            text += f"\nRationale: {result.rationale}"
        self.result_label.configure(text=text)
        self.go_button.configure(state=tk.NORMAL)

    def _show_error(self, message: str) -> None:
        self.result_label.configure(text=f"Classification failed: {message}")
        self.go_button.configure(state=tk.NORMAL)


def main() -> None:
    root = tk.Tk()
    TicketTriageApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
