"""Validated types used by the ticket classifier."""

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    ACCOUNT_ACCESS = "account_access"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ClassificationResult:
    category: Category
    urgency: Urgency
    rationale: str = ""

    @classmethod
    def from_mapping(cls, value: object) -> "ClassificationResult":
        if not isinstance(value, dict):
            raise ValueError("The model response must be a JSON object.")

        category_value = value.get("category")
        urgency_value = value.get("urgency")
        rationale = value.get("rationale", "")
        if not isinstance(category_value, str):
            raise ValueError("The model response must include a string category.")
        if not isinstance(urgency_value, str):
            raise ValueError("The model response must include a string urgency.")
        if not isinstance(rationale, str):
            raise ValueError("The model response rationale must be a string.")

        try:
            category = Category(category_value)
        except ValueError as error:
            raise ValueError(f"Unknown category: {category_value}") from error
        try:
            urgency = Urgency(urgency_value)
        except ValueError as error:
            raise ValueError(f"Unknown urgency: {urgency_value}") from error

        return cls(category=category, urgency=urgency, rationale=rationale)
