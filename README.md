# Project starter

## Add your API key locally

You will receive your group's API key by e-mail. They go in a local `.env` file, which Git ignores.

1. Copy the example file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and paste the key from the e-mail:

   ```
   LLM_API_KEY=...
   ```

   The proxy URL and model name are already built in; you do not need to set them.

3. Save the file. Do not rename it, and do not move the key anywhere else (code, notes, chat, issues).

4. Check that Git is not tracking it. This command must **not** list `.env`:

   ```bash
   git status
   ```

Never commit `.env` or paste the key into any file that is committed. If you think the key has leaked, e-mail the instructor straight away.

## Run the desktop app

Use Python 3.10 or newer. From the project root, run:

```bash
python -m src.app
```

Enter an internal IT ticket and select **GO**. The app calls the configured LLM
service and displays a category (`account_access`, `bug_report`,
`feature_request`, or `other`) and urgency (`low`, `medium`, or `high`).
Classification is not a substitute for human review. Ticket text is sent to the
configured LLM service and is not saved by this application.

## Tests and model evaluation

Run the offline unit tests from the project root:

```bash
python -m unittest discover -s tests
```

The live model evaluation uses only the synthetic examples in
`evaluation/cases.jsonl` and requires a working API key:

```bash
python -m evaluation.run_eval
```

It reports accuracy, macro-F1, and API/invalid-response failures for category
and urgency. Model evaluation makes live API calls; it is intentionally not part
of the offline unit test suite.

## Batch-evaluate a ticket file

To classify a UTF-8 text file with one ticket per line without opening the
desktop app, run:

```bash
python evaluate.py path\to\tickets.txt
```

The command makes one live API call per ticket and writes
`data/evaluation/tickets.txt.output.csv` with columns `ticket`, `category`,
`urgency`, and `evidence` (the classifier's rationale). Blank lines or
ordinary classification failures stop the run with the input line number.
Content-policy blocks are recorded in the evidence column as an error row
(category and urgency are left blank), and evaluation continues with subsequent
tickets. The output directory is created as needed. Do not commit inputs or
outputs containing internal ticket text.
