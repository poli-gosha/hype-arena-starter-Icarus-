"""Stage 6: write exactly 1,000 new claims, every one true.

Pipeline: KB -> candidates of all five types -> render text with templates ->
validate.validate() -> rank by confidence with a mix of types -> the best 1,000.

STATUS: baseline with plain templates for all five types.
Owner: backend teammate (branch `forge`), see docs/BRIEF_backend.md. Ideas to improve:
nicer per-attribute wording (artifacts/templates.json), unit conversion in compares,
smarter ranking, reading every text back through the reader once it lands.
"""
from __future__ import annotations

import itertools
from typing import Iterator

from . import AS_OF
from .kb import KB
from .model import Claim, Step, same_value
from .render import attribute_words, render
from . import wording
from .validate import has_time_word, normalize_text, validate

N_CLAIMS = 1000
DURATION_SECONDS = {"ms": 0.001, "s": 1, "min": 60, "h": 3600, "day": 86400, "week": 604800}
AMOUNT_PHRASES = {"gt": "higher than", "lt": "lower than", "eq": "the same as"}
DATE_PHRASES = {"gt": "later than", "lt": "earlier than"}


def _words_ok(attribute: str, allow_digits: bool = True) -> bool:
    w = attribute_words(attribute)
    if has_time_word(w):
        return False
    return allow_digits or not any(ch.isdigit() for ch in w)


def _step_conf(step: Step) -> float:
    """How sure we are of a stair: confirmed by labelled rows, or backed by agreeing rows
    with little dissent. 0 means: never build a claim on it."""
    if step.anchors:
        return min(0.99, 0.93 + 0.02 * step.anchors) if not step.dissent else 0.9
    if step.support >= 3 and step.dissent * 3 <= step.support:
        return min(0.9, 0.7 + 0.04 * step.support)
    return 0.0


def _precise(kb: KB, key: tuple, v: dict) -> dict | None:
    """A date as precisely as any row gives it: the referee compares dates as written, so
    "November 2025" is false when the truth is 4 November 2025. None: only a year is known
    while some row gives more (too vague to claim)."""
    if v.get("kind") != "date":
        return v
    best = str(v["value"])
    for m in kb.mentions.get(key, []):
        mv = m["value"]
        if mv.get("kind") == "date" and mv.get("op", "eq") == "eq" and str(mv["value"]).startswith(best[:7] if len(best) >= 7 else best):
            if len(str(mv["value"])) > len(best) and str(mv["value"]).startswith(best):
                best = str(mv["value"])
    if len(best) < 10:
        return None  # a month or a year alone: too easy to be wrong
    return {**v, "value": best}


def _covers(step: Step, day: str) -> bool:
    """Observations actually bracket the day: the stair was seen on or before it, and
    seen again (or replaced) on or after it."""
    # from the first date a real row backs it: a row labelled unsure, or a date that only
    # ruled out another value, doesn't stretch the stair back in time
    start = step.first_seen or step.start
    return start <= day and ((step.last_seen or step.start) >= day or (step.end is not None and day < step.end))


def _propped_by_lies(kb: KB, key: tuple, step: Step) -> bool:
    """The value's most recent support is a row judged (or labelled) false: an old value
    kept alive by stale lies, while the row with the new value may have been missed."""
    judged_false = getattr(kb, "judged_false", set())
    backing = sorted((m for m in kb.mentions.get(key, []) if same_value(m["value"], step.value)),
                     key=lambda m: m["date"])
    if not backing:
        return False
    last = backing[-1]
    return last["verdict"] == "false" or (last["verdict"] != "true" and last["row_id"] in judged_false)


# ---- fact ------------------------------------------------------------------------------
def fact_claims(kb: KB) -> Iterator[Claim]:
    for (subj, attr) in kb.facts():
        step = kb.current(subj, attr)
        if step is None or not _words_ok(attr) or not _step_conf(step) or _propped_by_lies(kb, (subj, attr), step):
            continue
        v = _precise(kb, (subj, attr), step.value)
        if v is None or (v["kind"] == "boolean" and not step.anchors):
            continue
        if v["kind"] == "boolean":
            words = attribute_words(attr)
            text = f"{subj} has {words}." if v["value"] else f"{subj} does not have {words}."
        else:
            r = render(v)
            if r is None:
                continue
            text = f"The {attribute_words(attr)} of {subj} is {r}."
        yield Claim("", "fact", text, {"subject": subj, "attribute": attr, "value": v},
                    _step_conf(step), [{"subject": subj, "attribute": attr}])


# ---- compare ---------------------------------------------------------------------------
def _amount(v: dict) -> tuple[tuple, float] | None:
    """(what it compares with, a comparable number), or None if it does not compare."""
    k = v["kind"]
    if k == "quantity":
        return ("quantity", v["unit"].lower()), float(v["value"])
    if k == "money":
        return ("money", v["currency"], v.get("per")), float(v["value"])
    if k == "percent":
        return ("percent",), float(v["value"])
    if k == "duration" and v["unit"] in DURATION_SECONDS:
        return ("duration",), float(v["value"]) * DURATION_SECONDS[v["unit"]]
    if k == "date" and len(v["value"]) == 10:
        return ("date",), float(v["value"].replace("-", ""))
    return None


def compare_claims(kb: KB) -> Iterator[Claim]:
    groups: dict[tuple, list] = {}
    for (subj, attr) in kb.facts():
        step = kb.current(subj, attr)
        if (step is None or not _words_ok(attr, allow_digits=False) or not _step_conf(step)
                or _propped_by_lies(kb, (subj, attr), step)):
            continue
        a = _amount(step.value)
        if a is not None:
            groups.setdefault(a[0], []).append((subj, attr, a[1], step))
    for kind, items in groups.items():
        for (ls, la, lv, lstep), (rs, ra, rv, rstep) in itertools.permutations(items, 2):
            if (ls, la) == (rs, ra):
                continue
            op = "gt" if lv > rv else "lt" if lv < rv else "eq"
            phrases = DATE_PHRASES if kind == ("date",) else AMOUNT_PHRASES
            if op not in phrases:
                continue
            text = (f"The {attribute_words(la)} of {ls} is {phrases[op]} "
                    f"the {attribute_words(ra)} of {rs}.")
            form = {"left": {"subject": ls, "attribute": la}, "right": {"subject": rs, "attribute": ra}, "op": op}
            conf = min(_step_conf(lstep), _step_conf(rstep)) * 0.95
            yield Claim("", "compare", text, form, conf,
                        [{"subject": ls, "attribute": la}, {"subject": rs, "attribute": ra}])


# ---- change ----------------------------------------------------------------------------
def change_claims(kb: KB) -> Iterator[Claim]:
    for (subj, attr) in kb.facts():
        steps = kb.timeline(subj, attr)
        if not _words_ok(attr):
            continue
        for a, b in zip(steps, steps[1:]):
            if a.value["kind"] == "boolean" or not _step_conf(a) or not _step_conf(b):
                continue
            va, vb = _precise(kb, (subj, attr), a.value), _precise(kb, (subj, attr), b.value)
            if va is None or vb is None or va == vb:
                continue
            ra, rb = render(va), render(vb)
            if ra is None or rb is None:
                continue
            text = f"The {attribute_words(attr)} of {subj} went from {ra} to {rb}."
            form = {"subject": subj, "attribute": attr, "from": va, "to": vb}
            yield Claim("", "change", text, form, min(_step_conf(a), _step_conf(b)) * 0.95,
                        [{"subject": subj, "attribute": attr}])


# ---- at_event --------------------------------------------------------------------------
def at_event_claims(kb: KB) -> Iterator[Claim]:
    # only events that already happened: a value at a future event is a guess
    events = {e: d for e, d in kb.events.items() if len(d) == 10 and d <= AS_OF}
    for (subj, attr) in kb.facts():
        if not _words_ok(attr) or kb.lexicon.is_event(subj):
            continue
        for event, day in events.items():
            step = kb.value_on(subj, attr, day)
            if step is None or step.value["kind"] == "boolean" or not _step_conf(step) or not _covers(step, day):
                continue
            v = _precise(kb, (subj, attr), step.value)
            r = render(v) if v is not None else None
            if r is None:
                continue
            text = f"The {attribute_words(attr)} of {subj} was {r} at {event}."
            form = {"subject": subj, "attribute": attr, "event": event, "value": v}
            yield Claim("", "at_event", text, form, _step_conf(step) * 0.9,
                        [{"subject": subj, "attribute": attr}, {"subject": event, "attribute": "date"}])


# ---- relation --------------------------------------------------------------------------
def relation_claims(kb: KB) -> Iterator[Claim]:
    for (subj, link), lsteps in kb.links().items():
        if not _words_ok(link):
            continue
        for ls in lsteps:
            if not _step_conf(ls):
                continue
            target = kb.lexicon.canonical(ls.value["value"])
            for attr in kb.lexicon.attributes(target):
                if not _words_ok(attr):
                    continue
                for ts in kb.timeline(target, attr):
                    overlaps = ts.start < (ls.end or "9999") and ls.start < (ts.end or "9999")
                    if not overlaps or ts.value["kind"] == "boolean" or not _step_conf(ts):
                        continue
                    v = _precise(kb, (target, attr), ts.value)
                    r = render(v) if v is not None else None
                    if r is None:
                        continue
                    text = f"The {attribute_words(attr)} of the {attribute_words(link)} of {subj} is {r}."
                    form = {"subject": subj, "link": link, "target": target, "attribute": attr, "value": v}
                    yield Claim("", "relation", text, form, min(_step_conf(ls), _step_conf(ts)) * 0.9,
                                [{"subject": subj, "attribute": link}, {"subject": target, "attribute": attr}])


def _options(c: Claim, kb: KB) -> list[str]:
    """Natural wordings for a claim, most natural first (polygraph/wording.py)."""
    f = c.form
    try:
        if c.type == "fact":
            return wording.fact(f["subject"], f["attribute"], f["value"])
        if c.type == "at_event":
            return wording.at_event(f["subject"], f["attribute"], f["value"], f["event"])
        if c.type == "change":
            return wording.change(f["subject"], f["attribute"], f["from"], f["to"])
        if c.type == "relation":
            return wording.relation(f["subject"], f["link"], f["attribute"], f["value"])
        if c.type == "compare":
            kind = kb.lexicon._kinds.get((f["left"]["subject"], f["left"]["attribute"]), "")
            phrase = (DATE_PHRASES if kind == "date" else AMOUNT_PHRASES)[f["op"]]
            return wording.compare(f["left"]["subject"], f["left"]["attribute"], f["right"]["subject"],
                                   f["right"]["attribute"], phrase, kind)
    except (KeyError, TypeError):
        pass
    return []


GENERATORS = {"fact": fact_claims, "compare": compare_claims, "change": change_claims,
              "at_event": at_event_claims, "relation": relation_claims}
# each type's share of the 1,000 (sums to 1,000): claims that connect facts (relation,
# at_event, change, compare) are the point of the challenge; a type that falls short leaves
# its slots to the most confident leftovers of the others
QUOTA = {"fact": 250, "relation": 150, "at_event": 150, "change": 150, "compare": 300}


def generate(kb: KB, input_texts: set[str], n: int = N_CLAIMS) -> list[Claim]:
    # the referee clone needs each fact's kind to know which compare phrases apply
    kb.lexicon._kinds = {key: steps[-1].value.get("kind") for key, steps in kb.timelines.items() if steps}
    seen_text: set[str] = set()
    pools: dict[str, list[Claim]] = {}
    for t, gen in GENERATORS.items():
        pool = []
        for c in gen(kb):
            c.id = "candidate"
            # the most natural wording the referee clone accepts; the plain template last
            for text in [o + "." for o in _options(c, kb)] + [c.text]:
                c.text = text
                key = normalize_text(text)
                if key not in seen_text and not validate(c, kb.lexicon, input_texts):
                    seen_text.add(key)
                    pool.append(c)
                    break
        pool.sort(key=lambda c: -c.confidence)
        pools[t] = pool
    chosen = []
    for t, pool in pools.items():
        chosen += pool[:QUOTA[t]]
    rest = sorted((c for t, p in pools.items() for c in p[QUOTA[t]:]), key=lambda c: -c.confidence)
    chosen += rest[: max(0, n - len(chosen))]
    chosen = sorted(chosen, key=lambda c: -c.confidence)[:n]
    for i, c in enumerate(chosen, 1):
        c.id = f"c{i:04d}-{c.type}"
    return chosen
