"""Reads a claim's text back the way the referee does (contracts/claim-forms.md).

validate.py calls text_problems(claim) for every candidate claim: a claim ships only if
its text states exactly what its form says, in one sentence, by the published rules:

  fact / at_event / relation  the sentence names the subject, states the value (read by our
                              reader, the clone of value-forms.md) and no other value of its
                              kind, and no date of its own; at_event has an event phrase right
                              before the event's name; relation holds the link's words
  compare                     left name, ONE op phrase, right name, in that order; no value,
                              number or date at all
  change                      the subject and "from <from> to <to>", each side whole
  yes / no                    the attribute's words, and the polarity by negation
"""
from __future__ import annotations

import re

from . import reader
from .lexicon import Lexicon
from .linker import Linker
from .model import Claim, value_key
from .validate import MONTHS_SEASONS_DAYS, NEGATION, TIME_WORDS

AMOUNT_OPS = {"gt": ["more", "higher", "greater", "larger", "bigger", "longer"],
              "lt": ["less", "fewer", "lower", "smaller", "shorter", "cheaper"]}
EQ_AMOUNT = [r"the same(?:\s+\S+){0,3}\s+as", r"as much(?:\s+\S+){0,3}\s+as", r"as many(?:\s+\S+){0,3}\s+as",
             r"as long as", r"as high as", r"equal to"]
DATE_OPS = {"gt": [r"after", r"later than"], "lt": [r"before", r"earlier than"],
            "eq": [r"on the same day as", r"the same day as"]}
EVENT_PHRASES = r"(?:at the time of|on the day of|during|at)"
NUMBER_WORDS = re.compile(r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
                          r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|"
                          r"sixty|seventy|eighty|ninety|hundred|thousand|million|billion|dozen)\b", re.I)


def _linker(lex: Lexicon) -> Linker:
    lk = getattr(lex, "_referee_linker", None)
    if lk is None:
        lk = lex._referee_linker = Linker(lex)
    return lk


def _amount_phrases(op: str) -> list[str]:
    if op == "eq":
        return EQ_AMOUNT
    return [w + r"(?:\s+\S+){0,3}\s+than" for w in AMOUNT_OPS[op]]


def _same_kind(a: dict, b: dict) -> bool:
    """Two values of one kind, as the 'one value' rule means it."""
    if a.get("kind") != b.get("kind"):
        return False
    k = a["kind"]
    if k == "money":
        return a.get("currency") == b.get("currency") and a.get("per") == b.get("per")
    if k == "quantity":
        ka, kb = value_key({**a, "value": 1}), value_key({**b, "value": 1})
        return json_unit(ka) == json_unit(kb)
    if k == "duration":
        return json_unit(value_key({**a, "value": 1})) == json_unit(value_key({**b, "value": 1}))
    return True


def json_unit(key: str) -> str:
    import json
    return str(json.loads(key).get("unit"))


def _words_re(attribute: str) -> re.Pattern:
    """An attribute's words, word for word, any case, with a space, a hyphen or nothing
    between words and between a word's letters and digits."""
    parts = []
    for w in attribute.split("_"):
        chunks = re.findall(r"[a-z]+|\d+", w.lower())
        parts.append(r"[\s-]?".join(re.escape(c) for c in chunks))
    return re.compile(r"(?<![A-Za-z0-9])" + r"[\s-]?".join(parts) + r"(?![A-Za-z0-9])", re.I)


def _mentions(text: str, lex: Lexicon):
    return _linker(lex).find(text)


def _names(text: str, lex: Lexicon, subject: str) -> list:
    canon = lex.canonical(subject)
    return [m for m in _mentions(text, lex) if m.subject == canon]


def _time_words(text: str) -> list[str]:
    found = []
    for w in TIME_WORDS:
        if re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", text, re.I):
            found.append(w)
    for w in MONTHS_SEASONS_DAYS:
        if re.search(r"(?<![A-Za-z])" + w + r"(?![A-Za-z])", text, 0 if w == "May" else re.I):
            found.append(w)
    return found


def _blank(text: str, spans) -> str:
    chars = list(text)
    for a, b in spans:
        for i in range(max(0, a), min(len(chars), b)):
            chars[i] = " "
    return "".join(chars)


def text_problems(c: Claim, lex: Lexicon) -> list[str]:
    spans = reader.sentences(c.text)
    if len(spans) != 1:
        return [f"{len(spans)} sentences: we write claims as one sentence"]
    s = c.text
    f = c.form
    if c.type == "compare":
        return _compare(s, f, lex)
    if c.type == "change":
        return _change(s, f, lex)
    return _single(s, c.type, f, lex)


def _single(s: str, typ: str, f: dict, lex: Lexicon) -> list[str]:
    why = []
    v = f["value"]
    subj = f["subject"]
    needed = _names(s, lex, subj)
    if not needed:
        return [f"the subject {subj!r} is not named"]
    name_spans = [(m.start, m.end) for m in needed]
    if typ == "at_event":
        ev = lex.canonical(f["event"])
        em = _names(s, lex, ev)
        ok = False
        for m in em:
            if re.search(EVENT_PHRASES + r"\s+(?:the\s+)?$", s[:m.start], re.I):
                ok = True
                ph = re.search(EVENT_PHRASES + r"\s+(?:the\s+)?$", s[:m.start], re.I)
                name_spans += [(m.start, m.end), (ph.start(), ph.end())]
        if not ok:
            why.append("no event phrase right before the event's name")
    if typ == "relation":
        if not _words_re(f["link"]).search(s):
            why.append(f"the relation words {f['link']!r} are missing")
    if v["kind"] == "boolean":
        if not _words_re(f["attribute"]).search(s):
            why.append(f"the attribute words {f['attribute']!r} are missing")
        neg = bool(NEGATION.search(s))
        if neg == bool(v["value"]):
            why.append("the polarity says the opposite")
        rest = _blank(s, name_spans)
        tw = _time_words(rest)
        if tw:
            why.append(f"time words {tw}")
        return why
    if NEGATION.search(s):
        why.append("a negation")
    vals = [x for x in reader.parse_values(s, name_spans) if not x.negated]
    k = value_key(v)
    hits = [x for x in vals if value_key(x.value) == k or any(value_key(a) == k for a in x.alts)]
    if v["kind"] == "name":
        target = lex.canonical(v["value"])
        nm = [m for m in _mentions(s, lex) if m.subject == target and (m.start, m.end) not in name_spans]
        if not nm:
            why.append(f"the name {v['value']!r} is not written")
        value_spans = [(m.start, m.end) for m in nm]
        others = [m for m in _mentions(s, lex) if (m.start, m.end) not in name_spans + value_spans
                  and m.subject not in (subj, target)]
        if others:
            why.append(f"another name {others[0].written!r}")
    else:
        if not hits:
            why.append(f"the value {v!r} does not read")
        value_spans = [(h.start, h.end) for h in hits]
        for x in vals:
            if (x.start, x.end) in value_spans:
                continue
            if _same_kind(x.value, v) or x.value["kind"] == "date":
                why.append(f"another value {x.value!r}")
    rest = _blank(s, name_spans + value_spans)
    tw = _time_words(rest)
    if tw:
        why.append(f"time words {tw}")
    return why


def _compare(s: str, f: dict, lex: Lexicon) -> list[str]:
    why = []
    left, right, op = f["left"], f["right"], f["op"]
    lm = _names(s, lex, left["subject"])
    rm = _names(s, lex, right["subject"])
    if not lm or not rm:
        return ["a compared subject is not named"]
    is_date = _kind_of(left, lex) == "date"
    phrases = DATE_OPS[op] if is_date else _amount_phrases(op)
    all_phrases = [p for ps in (DATE_OPS.values() if is_date else [_amount_phrases(o) for o in ("gt", "lt", "eq")])
                   for p in ps]
    found = []
    for p in all_phrases:
        for m in re.finditer(r"(?<![A-Za-z])" + p + r"(?![A-Za-z])", s, re.I):
            found.append((m.start(), m.end(), p))
    mine = [x for x in found if x[2] in phrases]
    if not mine:
        return ["no phrase of the claim's op"]
    if len({(a, b) for a, b, _ in found}) > 1:
        why.append("more than one comparison phrase")
    ps, pe, _ = mine[0]
    if not any(m.end <= ps for m in lm) or not any(m.start >= pe for m in rm):
        why.append("the left subject must come before the phrase and the right one after")
    names = [(m.start, m.end) for m in _mentions(s, lex)]
    rest = _blank(s, names + [(ps, pe)])
    if reader.parse_values(rest) or re.search(r"\d", rest) or NUMBER_WORDS.search(rest):
        why.append("a value or a number")
    tw = _time_words(rest)
    if tw:
        why.append(f"time words {tw}")
    if NEGATION.search(s):
        why.append("a negation")
    return why


def _kind_of(ref: dict, lex: Lexicon) -> str:
    return getattr(lex, "_kinds", {}).get((lex.canonical(ref["subject"]), ref["attribute"]), "")


def _change(s: str, f: dict, lex: Lexicon) -> list[str]:
    why = []
    subj = f["subject"]
    needed = _names(s, lex, subj)
    if not needed:
        return [f"the subject {subj!r} is not named"]
    spans = [(m.start, m.end) for m in needed]
    a, b = f["from"], f["to"]
    if a["kind"] == "boolean":
        if not _words_re(f["attribute"]).search(s):
            why.append("the attribute words are missing")
        return why + ["yes/no changes are not generated"]
    m = re.search(r"\bfrom\b(?P<a>.+?)\bto\b(?P<b>.+)$", s, re.I)
    if not m:
        return ["no from ... to phrase"]
    va = [x for x in reader.parse_values(m.group("a").strip()) if not x.negated]
    vb = [x for x in reader.parse_values(m.group("b").strip()) if not x.negated]
    if not any(value_key(x.value) == value_key(a) or any(value_key(y) == value_key(a) for y in x.alts) for x in va):
        why.append(f"the from value {a!r} does not read whole")
    if not any(value_key(x.value) == value_key(b) or any(value_key(y) == value_key(b) for y in x.alts) for x in vb):
        why.append(f"the to value {b!r} does not read whole")
    if NEGATION.search(s):
        why.append("a negation")
    return why
