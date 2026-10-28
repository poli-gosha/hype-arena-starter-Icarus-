# Copilot instructions

## Repository workflow

This is the Python starter for the Hype Arena challenge. The authoritative data and output rules are in `README.md` and `contracts/README.md`; read the relevant contract before changing claim generation or output validation.

### Build, check, and development commands

- Run the official local check (requires Docker and Python 3):
  ```sh
  scripts/check.sh
  ```
  This builds the root `Dockerfile`, runs it offline as UID 10001, and validates `/output/output.csv`.
- Check an already-built image:
  ```sh
  scripts/check.sh my-image:tag
  ```
- Use a shorter local deadline while iterating:
  ```sh
  MINUTES=5 scripts/check.sh
  ```
- Generate and validate claims directly from the practice data:
  ```sh
  python3 polygraph/generate_claims.py
  ```
  This writes `output/claims_output.csv` and prints validation/type information.
- Create the hidden-label test input used by the checker:
  ```sh
  python3 scripts/input.py data/practice.csv /path/to/universe.csv
  ```
- Validate an output directory against the practice data:
  ```sh
  python3 scripts/check_output.py /path/to/output data/practice.csv /path/to/universe.csv
  ```

There is no checked-in package manifest, test runner configuration, or lint configuration in this starter. The validation scripts are the repository's executable checks; when adding tooling, keep it consistent with the Docker/offline contract.

## Architecture

The implemented path is:

1. `data/practice.csv` contains labelled sentences and structured `form` facts. `data/lexicon.json` defines valid subjects, aliases, attributes, and events.
2. `polygraph.kb.KnowledgeBase` loads only rows labelled `true`, extracts their structured facts, and groups each `(subject, attribute)` into a date-sorted `FactTimeline`. Timelines provide current/earliest values, distinct changes, and event dates.
3. `polygraph.forge` derives candidate `fact`, `compare`, `change`, `at_event`, and `relation` claims from those timelines. It renders text using `polygraph.render`, filters/ranks candidates, and targets exactly 1,000 claims.
4. `polygraph.validate.validate_claim` checks IDs, types, text size, labels, confidence, JSON forms, and type-specific text/form rules. The challenge referee applies stricter rules from `contracts/claim-forms.md` and `contracts/value-forms.md`, so those documents take precedence over local validation.
5. `polygraph/generate_claims.py` wires the knowledge base, forge, validator, and CSV writer for an offline generation run.
6. `scripts/check.sh` creates the judge-shaped input, runs the submitted Docker image with no network and a read-only root, then `scripts/check_output.py` checks the final CSV's format, hidden-row labels, and exactly 1,000 claims.

The intended submission runtime reads `/universe/universe.csv` and `/universe/lexicon.json` and writes `/output/output.csv`. The current checkout does not contain the fuller runtime/frontend files described in the planning brief, so do not assume modules such as `polygraph.run`, `server/app.py`, or a frontend exist unless they are added.

## Codebase-specific conventions

- Treat the fictional Hooly universe as the only source of truth. Do not enrich facts from the web or pretrained world knowledge.
- Use the structured `form` values from the dataset as the source for timelines and claims. `KnowledgeBase` deliberately ignores false/unsure practice rows when building trusted fact history.
- Values are dictionaries with a `kind` and kind-specific fields. Keep rendering centralized in `polygraph/render.py`; its money, quantity, date, duration, percent, version, boolean, and name forms must match the value contract.
- Claim forms use exactly the five types `{fact, compare, change, at_event, relation}`. Output labels for claims must be `true`, confidence must be in `[0.5, 1]`, and the final output must contain exactly 1,000 claim rows.
- Claim IDs must match `[A-Za-z0-9_.-]{1,64}`. Input-label rows are identified by an empty `type`; claim rows have a non-empty `type`.
- Compare text must not contain digits, number words, month names, or time words. Compare only compatible values; the contract allows unit conversion, while the current `_compare_values` implementation is conservative about matching units.
- Fact, event, and relation text must name the required subject/event/relation and state only the intended value in the sentence. Avoid extra dates, values, negations, approximations, or comparison wording unless that claim type explicitly requires them.
- Preserve deterministic generation: `polygraph.forge` seeds Python's random generator with `2026`. If changing candidate ordering or templates, keep output reproducible.
- Keep generated artifacts and run outputs under `output/`; do not treat them as source data. The official checker expects a regular UTF-8 CSV named `output.csv` with columns `id,type,text,form,label,confidence`.
- Docker submissions must follow the contract: build for `linux/amd64`, run offline, write to `/output/output.csv`, and end the image with a non-root `USER 10001`.
