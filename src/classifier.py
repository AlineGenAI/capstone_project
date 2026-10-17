"""Ticket classification using the configured LLM API."""

import json
import re

from . import llm
from .schemas import Category, ClassificationResult, Urgency

SYSTEM_PROMPT = """You classify internal IT service requests and incidents.
Return only a JSON object with exactly these fields:
{"category":"account_access|bug_report|feature_request|other",
 "urgency":"low|medium|high",
 "rationale":"brief evidence from the ticket supporting both labels"}

Choose account_access for sign-in, permissions, or account problems; bug_report
for something that is broken or not behaving as expected; feature_request for
a requested new capability; and other when none of those fit.
Determine urgency strictly from the impact on the customer's ability to work.
Do not use the words "urgent" or "ASAP", exclamation marks, or similar wording
as urgency evidence by themselves:
- high only when the customer is blocked from working or totally out of the
  system;
- medium when the customer is partially blocked from working, for example
  when an application is out of service;
- low when there is no impact on the customer's ability to work.
If a ticket contains multiple requests, assess each one and use the highest
urgency supported by any of them. Do not invent details that the ticket does
not provide."""


def classify_ticket(ticket: str) -> ClassificationResult:
    """Classify a non-empty ticket, rejecting malformed model output."""
    if not ticket.strip():
        raise ValueError("Ticket description cannot be empty.")

    response = llm.ask(
        f"Classify this ticket:\n\n{ticket.strip()}",
        system=SYSTEM_PROMPT,
    )
    if not isinstance(response, str):
        raise ValueError("The LLM API returned an empty or non-text response.")

    content = response.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("The LLM API returned invalid JSON.") from error

    try:
        result = ClassificationResult.from_mapping(payload)
    except ValueError as error:
        raise ValueError(f"Invalid classification response: {error}") from error

    if isinstance(payload, dict):
        unexpected = set(payload) - {"category", "urgency", "rationale"}
        if unexpected:
            raise ValueError(
                "Invalid classification response: unexpected fields "
                + ", ".join(sorted(unexpected))
            )
    return result
