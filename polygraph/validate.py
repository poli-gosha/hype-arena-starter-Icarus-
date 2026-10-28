"""Claim validator for Polygraph."""
import re
import json

ID_PATTERN = re.compile(r'^[A-Za-z0-9_.\-]{1,64}$')
VALID_TYPES = {"fact", "compare", "change", "at_event", "relation"}
NEGATION_WORDS = re.compile(r'\b(not|never|no|without|n\'t|neither|nor|cannot|can\'t)\b', re.IGNORECASE)
# Word numbers that count as numbers in compare claims
WORD_NUMBERS = re.compile(
    r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
    r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
    r'thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|'
    r'billion|a dozen|dozen|a few|a couple|several|many|numerous)\b',
    re.IGNORECASE
)
MONTH_NAMES = re.compile(
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
    re.IGNORECASE
)
TIME_WORDS = re.compile(
    r'\b(ago|yesterday|before|after|since|recently|previously|formerly|'
    r'used to|once|later|earlier|last|next|current|now|today|then|when)\b',
    re.IGNORECASE
)


def validate_claim(claim: dict) -> list:
    """Return list of problems. Empty list = valid."""
    problems = []

    # id
    cid = claim.get("id", "")
    if not ID_PATTERN.match(str(cid)):
        problems.append(f"id '{cid}' does not match pattern")

    # type
    ctype = claim.get("type", "")
    if ctype not in VALID_TYPES:
        problems.append(f"type '{ctype}' is not valid")

    # text
    text = claim.get("text", "")
    if not isinstance(text, str) or len(text) < 1 or len(text) > 300:
        problems.append(f"text length {len(text)} out of range 1-300")

    # label
    if claim.get("label") != "true":
        problems.append(f"label must be 'true', got '{claim.get('label')}'")

    # confidence
    try:
        conf = float(claim.get("confidence", 0))
        if not (0.5 <= conf <= 1.0):
            problems.append(f"confidence {conf} out of range 0.5-1.0")
    except (TypeError, ValueError):
        problems.append(f"confidence '{claim.get('confidence')}' is not a float")

    # form
    form = claim.get("form")
    if isinstance(form, str):
        try:
            form = json.loads(form)
        except json.JSONDecodeError:
            problems.append("form is not valid JSON")
            return problems
    if not isinstance(form, dict):
        problems.append(f"form must be a dict, got {type(form)}")
        return problems

    # Type-specific checks
    if ctype == "fact":
        _validate_fact(claim, form, text, problems)
    elif ctype == "compare":
        _validate_compare(claim, form, text, problems)
    elif ctype == "change":
        _validate_change(claim, form, text, problems)
    elif ctype == "at_event":
        _validate_at_event(claim, form, text, problems)
    elif ctype == "relation":
        _validate_relation(claim, form, text, problems)

    return problems


def _validate_fact(claim, form, text, problems):
    if "subject" not in form:
        problems.append("fact form missing 'subject'")
    if "attribute" not in form:
        problems.append("fact form missing 'attribute'")
    if "value" not in form:
        problems.append("fact form missing 'value'")

    # Check subject appears in text
    subject = form.get("subject", "")
    if subject and subject not in text:
        problems.append(f"fact: subject '{subject}' not in text")

    # No negation for non-boolean true facts
    value = form.get("value", {})
    if value.get("kind") != "boolean" or value.get("value") == True:
        if NEGATION_WORDS.search(text):
            # Allow negation in boolean-false sentences
            if not (value.get("kind") == "boolean" and value.get("value") == False):
                problems.append("fact: negation word found in text")


def _validate_compare(claim, form, text, problems):
    if "left" not in form:
        problems.append("compare form missing 'left'")
    if "right" not in form:
        problems.append("compare form missing 'right'")
    if "op" not in form:
        problems.append("compare form missing 'op'")
    if form.get("op") not in ("gt", "lt", "eq"):
        problems.append(f"compare op '{form.get('op')}' must be gt/lt/eq")

    # No digits in text
    if re.search(r'\d', text):
        problems.append("compare: digits found in text")

    # No word numbers
    if WORD_NUMBERS.search(text):
        problems.append("compare: word numbers found in text")

    # No month names
    if MONTH_NAMES.search(text):
        problems.append("compare: month name found in text")

    # No time words
    if TIME_WORDS.search(text):
        problems.append("compare: time word found in text")


def _validate_change(claim, form, text, problems):
    if "subject" not in form:
        problems.append("change form missing 'subject'")
    if "from" not in form:
        problems.append("change form missing 'from'")
    if "to" not in form:
        problems.append("change form missing 'to'")


def _validate_at_event(claim, form, text, problems):
    if "subject" not in form:
        problems.append("at_event form missing 'subject'")
    if "attribute" not in form:
        problems.append("at_event form missing 'attribute'")
    if "event" not in form:
        problems.append("at_event form missing 'event'")
    if "value" not in form:
        problems.append("at_event form missing 'value'")

    # event name should appear in text
    event = form.get("event", "")
    if event and event not in text:
        problems.append(f"at_event: event '{event}' not in text")

    # subject should appear in text
    subject = form.get("subject", "")
    if subject and subject not in text:
        problems.append(f"at_event: subject '{subject}' not in text")


def _validate_relation(claim, form, text, problems):
    if "subject" not in form:
        problems.append("relation form missing 'subject'")
    if "link" not in form:
        problems.append("relation form missing 'link'")
    if "target" not in form:
        problems.append("relation form missing 'target'")
