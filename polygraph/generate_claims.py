"""Generate exactly 1,000 claims from the labelled practice facts."""

import csv
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from polygraph.forge import generate
from polygraph.kb import KB
from polygraph.lexicon import Lexicon
from polygraph.model import Row
from polygraph.validate import normalize_text, validate


BASE = os.path.dirname(os.path.dirname(__file__))
PRACTICE = os.path.join(BASE, "data", "practice.csv")
LEXICON = os.path.join(BASE, "data", "lexicon.json")
OUTPUT = os.path.join(BASE, "output", "claims_output.csv")


def load_practice():
    rows = []
    forms = {}
    with open(PRACTICE, encoding="utf-8-sig", newline="") as stream:
        for raw in csv.DictReader(stream):
            row = Row(raw["id"], raw["text"], raw["date"], raw["label"])
            rows.append(row)
            forms[row.id] = json.loads(raw["form"])
    return rows, forms


def main():
    rows, forms = load_practice()
    lexicon = Lexicon.load(LEXICON)
    kb = KB.from_gold(lexicon, rows, forms)
    input_texts = {normalize_text(row.text) for row in rows}
    claims = generate(kb, input_texts)

    problems = []
    for claim in claims:
        issues = validate(claim, lexicon, input_texts)
        if issues:
            problems.append((claim.id, issues))

    if len(claims) != 1000:
        problems.append(("count", [f"generated {len(claims)} claims, expected 1000"]))

    if problems:
        print(f"VALIDATION PROBLEMS ({len(problems)}):")
        for claim_id, issues in problems[:20]:
            print(f"  {claim_id}: {issues}")
        return 1

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["id", "type", "text", "form", "label", "confidence"]
        )
        writer.writeheader()
        for claim in claims:
            writer.writerow(
                {
                    "id": claim.id,
                    "type": claim.type,
                    "text": claim.text,
                    "form": json.dumps(claim.form, ensure_ascii=False),
                    "label": "true",
                    "confidence": claim.confidence,
                }
            )

    print(f"Written {len(claims)} true claims to {OUTPUT}")
    print("Type breakdown:", dict(Counter(claim.type for claim in claims)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

