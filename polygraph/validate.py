"""Our clone of the referee's claim checks (contracts/claim-forms.md + entry.schema.json).

A claim ships only when validate() returns no problems.

STATUS: structural checks (schema, lexicon names, length, no copy of an input row, no
refused words). The text checks that need the reader (the sentence states exactly the
form's value, one value of its kind, no negation...) land once reader.IMPLEMENTED is True.
Owner: backend teammate (branch `forge`), see docs/BRIEF_backend.md.
"""
from __future__ import annotations

import re

from . import reader
from .lexicon import Lexicon
from .model import Claim
from .model import value_key
from .render import attribute_words

TYPES = {"fact", "compare", "change", "at_event", "relation"}
ID = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
MONTHS_SEASONS_DAYS = ["January", "February", "March", "April", "May", "June", "July", "August",
                       "September", "October", "November", "December", "spring", "summer",
                       "autumn", "winter", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                       "Saturday", "Sunday"]
TIME_WORDS = ["ago", "yesterday", "tomorrow", "once", "formerly", "previously", "originally",
              "initially", "recently", "lately", "soon", "eventually", "then", "before", "after",
              "since", "until", "till", "earlier", "later", "used to", "last week", "last month",
              "last quarter", "last year", "next week", "next month", "next quarter", "next year",
              "in the past", "in the future", "at the time", "at that time"]
NEGATION = re.compile(r"\b(?:not|no|never|none|nobody|nothing|neither|nor|without|cannot)\b|n't\b", re.I)


def has_time_word(text: str) -> list[str]:
    found = []
    for w in TIME_WORDS:
        if re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", text, re.I):
            found.append(w)
    for w in MONTHS_SEASONS_DAYS:
        flags = 0 if w == "May" else re.I  # `may` is the month only when written May
        if re.search(r"(?<![A-Za-z])" + w + r"(?![A-Za-z])", text, flags):
            found.append(w)
    return found


def _names_ok(lex: Lexicon, subject: str, attribute: str | None, why: list[str], what: str):
    canon = lex.canonical(subject)
    if canon is None:
        why.append(f"{what}: unknown subject {subject!r}")
    elif attribute is not None and not lex.has(canon, attribute):
        why.append(f"{what}: {canon!r} has no attribute {attribute!r}")


def validate(claim: Claim, lex: Lexicon, input_texts: set[str] | None = None) -> list[str]:
    why: list[str] = []
    if not ID.match(claim.id):
        why.append("id")
    if claim.type not in TYPES:
        why.append("type")
    text = claim.text.strip()
    if not text or len(text) > 300:
        why.append("text length")
    if input_texts is not None and normalize_text(text) in input_texts:
        why.append("a copy of an input row")
    if not 0.5 <= claim.confidence <= 1:
        why.append("confidence")
    f = claim.form
    if claim.type in ("fact", "change", "at_event"):
        _names_ok(lex, f.get("subject", ""), f.get("attribute", ""), why, "subject")
    if claim.type == "at_event":
        if lex.canonical(f.get("event", "")) not in lex.events:
            why.append("event not in the lexicon's events")
    if claim.type == "compare":
        for side in ("left", "right"):
            _names_ok(lex, f.get(side, {}).get("subject", ""), f.get(side, {}).get("attribute", ""), why, side)
        if f.get("op") not in ("gt", "lt", "eq"):
            why.append("op")
    if claim.type == "relation":
        _names_ok(lex, f.get("subject", ""), f.get("link", ""), why, "link")
        _names_ok(lex, f.get("target", ""), f.get("attribute", ""), why, "target")
        if not _relation_words_present(claim.text, f.get("subject", ""), f.get("link", ""), lex):
            why.append("relation words or subject missing from text")
    for k in ("value", "from", "to"):
        if isinstance(f.get(k), dict) and "op" in f[k]:
            why.append(f"{k} has an op")
        # the referee resolves a name value through the lexicon's spellings only
        if isinstance(f.get(k), dict) and f[k].get("kind") == "name" and lex.canonical(f[k]["value"]) is None:
            why.append(f"{k}: name {f[k]['value']!r} is not in the lexicon")
    if claim.type != "change":
        rest = _outside_names(text, lex)
        v = f.get("value")
        if isinstance(v, dict) and v.get("kind") == "date":  # the value may be a date itself
            from .render import render
            rest = rest.replace(render(v) or "\0", " ")
        if claim.type == "compare":  # the op phrase's own words are allowed
            rest = re.sub(r"\b(?:later than|earlier than|after|before|on the same day as|the same day as)\b",
                          " ", rest, count=1, flags=re.I)
        if claim.type == "at_event":  # so is the event phrase
            rest = re.sub(r"\b(?:at the time of|on the day of)\b", " ", rest, count=1, flags=re.I)
        tw = has_time_word(rest)
        if tw:
            why.append(f"time words {tw}")
    if NEGATION.search(text) and not _is_boolean(claim):
        why.append("negation")
    if reader.IMPLEMENTED:
        why.extend(_validate_text_values(claim, lex))
    return why


def _validate_text_values(claim: Claim, lex: Lexicon) -> list[str]:
    """Check that the referee-style reader sees exactly the claim's values."""
    text = claim.text
    names = _name_spans(text, lex)
    spans = reader.sentences(text)
    if len(spans) != 1:
        return ["claim text must hold its form in one sentence"]

    parsed = reader.parse_values(text, names)
    numeric = [v for v in parsed if not v.negated]
    form = claim.form

    if claim.type == "compare":
        if numeric:
            return ["compare text states a value"]
        if not _compare_phrase_matches(text, form.get("op")):
            return ["compare text does not contain exactly one allowed op phrase"]
        return []

    expected = []
    if claim.type == "change":
        expected = [form.get("from"), form.get("to")]
    else:
        expected = [form.get("value")]

    expected = [v for v in expected if isinstance(v, dict)]
    problems = []
    if any(v.get("kind") == "name" for v in expected):
        for value in expected:
            if value.get("kind") == "name" and lex.canonical(value.get("value", "")) is None:
                problems.append(f"unknown name value {value.get('value')!r}")
    expected_numeric = [v for v in expected if v.get("kind") not in ("name", "boolean")]
    if len(numeric) != len(expected_numeric):
        problems.append(f"reader found {len(numeric)} values, expected {len(expected_numeric)}")
    elif any(value_key(a.value) != value_key(b) for a, b in zip(numeric, expected_numeric)):
        problems.append("reader values do not match the claim form")

    for value in expected:
        if value.get("kind") == "name" and not _value_name_present(text, value["value"], lex):
            problems.append(f"name value missing from text: {value['value']!r}")
        if value.get("kind") == "boolean":
            if not _boolean_text_matches(text, claim, value):
                problems.append("boolean attribute or polarity missing from text")
    if claim.type in ("fact", "change", "at_event"):
        subject = form.get("subject", "")
        if not _value_name_present(text, subject, lex):
            problems.append("subject missing from text")
    if claim.type == "at_event":
        if not _value_name_present(text, form.get("event", ""), lex):
            problems.append("event missing from text")
        if not re.search(r"\b(?:at|during|on the day of|at the time of)\b", text, re.I):
            problems.append("event phrase missing from text")
    return problems


def _name_spans(text: str, lex: Lexicon) -> list[tuple[int, int]]:
    from .linker import Linker
    linker = getattr(lex, "_linker", None) or Linker(lex)
    lex._linker = linker
    return [(m.start, m.end) for m in linker.find(text)]


def _value_name_present(text: str, name: str, lex: Lexicon) -> bool:
    if not name:
        return False
    canon = lex.canonical(name)
    if canon is None:
        return False
    linker = getattr(lex, "_linker", None)
    if linker is None:
        from .linker import Linker
        linker = Linker(lex)
        lex._linker = linker
    return any(lex.canonical(m.subject) == canon for m in linker.find(text))


def _relation_words_present(text: str, subject: str, link: str, lex: Lexicon) -> bool:
    return _value_name_present(text, subject, lex) and bool(
        re.search(r"(?<![A-Za-z0-9])" + re.escape(attribute_words(link)).replace("_", r"[\s_-]*")
                  + r"(?![A-Za-z0-9])", text, re.I)
    )


def _boolean_text_matches(text: str, claim: Claim, value: dict) -> bool:
    attr = claim.form.get("attribute", "")
    words = r"[\s_-]*".join(re.escape(part) for part in re.split(r"[_\s-]+", attr) if part)
    has_attribute = bool(re.search(words, text, re.I))
    negative = bool(NEGATION.search(text))
    return has_attribute and negative is (value.get("value") is False)


def _compare_phrase_matches(text: str, op: str) -> bool:
    phrases = {
        "gt": r"(?:more|higher|greater|larger|bigger|longer)\b[^.?!]*?\bthan\b",
        "lt": r"(?:less|fewer|lower|smaller|shorter|cheaper)\b[^.?!]*?\bthan\b",
        "eq": r"(?:the same|as much|as many|as long|as high|equal to)\b[^.?!]*?\b(?:as|to)\b",
    }
    matches = re.findall(phrases.get(op, r"$^"), text, re.I)
    return len(matches) == 1


def _is_boolean(claim: Claim) -> bool:
    f = claim.form
    return any(isinstance(f.get(k), dict) and f[k].get("kind") == "boolean" for k in ("value", "from", "to"))


def _outside_names(text: str, lex: Lexicon) -> str:
    """The text with every lexicon name blanked out: words inside names don't count."""
    from .linker import Linker
    linker = getattr(lex, "_linker", None) or Linker(lex)
    lex._linker = linker
    out = list(text)
    for m in linker.find(text):
        out[m.start:m.end] = " " * (m.end - m.start)
    return "".join(out)


def normalize_text(text: str) -> str:
    """How check_output.py compares a claim with the input rows."""
    return " ".join(text.lower().split()).rstrip(".!? ")
