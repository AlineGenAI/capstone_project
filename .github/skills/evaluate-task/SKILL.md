---
name: evaluate-task
description: "Use when evaluating ticket-classifier changes, prompt or model updates, golden-set quality, or running the project's unit and AI evaluation tests."
---

# Evaluate Ticket Classifier Tasks

Run the project checks for changes to ticket classification, prompts, response
validation, or evaluation behavior. The golden set is the synthetic dataset at
`evaluation/cases.jsonl`; its metrics runner is `evaluation/run_eval.py`.
`evaluate.py` is the batch trace/export CLI for a supplied one-ticket-per-line
input file and writes one classification row per ticket to CSV.

## Procedure

1. From the repository root, run the offline unit tests:

   ```bash
   python -m unittest discover -s tests -v
   ```

2. Run Python syntax compilation:

   ```bash
   python -m compileall -q src evaluation tests evaluate.py
   ```

3. For classifier, prompt, or model changes, run the live golden-set evaluation
   when the configured `LLM_API_KEY` is available:

   ```bash
   python -m evaluation.run_eval
   ```

   This makes API calls for the synthetic cases in `evaluation/cases.jsonl`.
   Do not include real internal ticket text in the evaluation dataset. If the
   API key is missing or the service is unavailable, report that evaluation as
   blocked; do not skip silently or claim the live evaluation passed.

4. When asked to batch-classify a supplied golden set, run the file through
   `evaluate.py` without launching the desktop app:

   ```bash
   python evaluate.py <input-file>
   ```

   The input is UTF-8, one ticket per line. The output is
   `data/evaluation/<input-file>.output.csv` with columns `ticket`, `category`,
   `urgency`, and `evidence`. It makes live API calls. Content-policy blocks
   produce an error row with blank category and urgency and processing continues.
   Other classification failures identify the input line and stop the run.
   Treat any supplied tickets as sensitive; do not commit the input or generated
   output.

5. Report offline tests, metrics evaluation, and batch output separately.
   Include category and urgency accuracy, macro-F1, and invalid/failed response
   count from the metrics runner. Compare results to a previous baseline when
   available, and call out regressions rather than relying on aggregate
   accuracy alone.
