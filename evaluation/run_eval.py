"""Run the live LLM classifier against labeled synthetic cases."""

import json
from pathlib import Path
from typing import Callable

from src.classifier import classify_ticket
from src.schemas import ClassificationResult

CASES_PATH = Path(__file__).with_name("cases.jsonl")


def macro_f1(expected: list[str], predicted: list[str], labels: list[str]) -> float:
    scores = []
    for label in labels:
        true_positive = sum(
            actual == label and guess == label
            for actual, guess in zip(expected, predicted)
        )
        false_positive = sum(
            actual != label and guess == label
            for actual, guess in zip(expected, predicted)
        )
        false_negative = sum(
            actual == label and guess != label
            for actual, guess in zip(expected, predicted)
        )
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(2 * true_positive / denominator if denominator else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def evaluate(
    classifier: Callable[[str], ClassificationResult] = classify_ticket,
) -> dict[str, object]:
    cases = [
        json.loads(line)
        for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    category_labels = ["account_access", "bug_report", "feature_request", "other"]
    urgency_labels = ["low", "medium", "high"]
    category_expected = []
    category_predicted = []
    urgency_expected = []
    urgency_predicted = []
    failures = []

    for index, case in enumerate(cases, start=1):
        try:
            result = classifier(case["ticket"])
        except Exception as error:
            failures.append({"case": index, "error": str(error)})
            category_predicted.append("")
            urgency_predicted.append("")
        else:
            category_predicted.append(result.category.value)
            urgency_predicted.append(result.urgency.value)
        category_expected.append(case["category"])
        urgency_expected.append(case["urgency"])

    count = len(cases)
    return {
        "cases": count,
        "category_accuracy": (
            sum(a == p for a, p in zip(category_expected, category_predicted)) / count
            if count
            else 0.0
        ),
        "category_macro_f1": macro_f1(
            category_expected, category_predicted, category_labels
        ),
        "urgency_accuracy": (
            sum(a == p for a, p in zip(urgency_expected, urgency_predicted)) / count
            if count
            else 0.0
        ),
        "urgency_macro_f1": macro_f1(
            urgency_expected, urgency_predicted, urgency_labels
        ),
        "invalid_or_failed_responses": len(failures),
        "failures": failures,
    }


def main() -> None:
    print(json.dumps(evaluate(), indent=2))


if __name__ == "__main__":
    main()
