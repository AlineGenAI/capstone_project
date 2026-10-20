"""Classify tickets from a text file and write their results to CSV."""

import argparse
import csv
import sys
from pathlib import Path
from typing import Callable

from src.classifier import classify_ticket
from src.llm import ContentPolicyViolationError
from src.schemas import ClassificationResult

OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "data" / "evaluation"


class EvaluationError(RuntimeError):
    """An input ticket could not be classified."""


def evaluate_file(
    input_file: Path,
    classifier: Callable[[str], ClassificationResult] = classify_ticket,
    output_directory: Path = OUTPUT_DIRECTORY,
) -> Path:
    """Classify input lines, recording content-policy blocks as CSV error rows."""
    tickets = input_file.read_text(encoding="utf-8").splitlines()
    results = []
    for line_number, ticket in enumerate(tickets, start=1):
        try:
            result = classifier(ticket)
        except ContentPolicyViolationError as error:
            results.append(
                (ticket, "", "", f"ERROR on line {line_number}: {error}")
            )
        except Exception as error:
            raise EvaluationError(
                f"Could not classify ticket on line {line_number}: {error}"
            ) from error
        else:
            results.append(
                (
                    ticket,
                    result.category.value,
                    result.urgency.value,
                    result.rationale,
                )
            )

    output_directory.mkdir(parents=True, exist_ok=True)
    output_file = output_directory / f"{input_file.name}.output.csv"
    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(("ticket", "category", "urgency", "evidence"))
        writer.writerows(results)
    return output_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify one ticket per line and save results as CSV."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="UTF-8 text file containing one ticket per line",
    )
    args = parser.parse_args(argv)

    try:
        output_file = evaluate_file(args.input_file)
    except (EvaluationError, OSError, UnicodeError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 1

    print(f"Evaluation results written to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
