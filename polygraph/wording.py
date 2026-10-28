"""Natural sentences for claims. Every function returns options, most natural first; the
forge keeps the first one our referee clone (referee.py) accepts, and the plain template
("The <attribute> of <subject> is <value>.") is always the last resort.
"""
from __future__ import annotations

from .reader import singular
from .render import attribute_words, render

ACRONYMS = {"ceo", "cto", "cfo", "coo", "sla", "ai", "ar", "eu", "api", "cli", "ide", "sdk", "sdks", "soc2",
            "gdpr", "arr", "ram", "gpu", "cpu", "nps", "hr", "kpi", "io", "ux", "ui"}
DATE_VERBS = {"joined": "joined on", "founded": "was founded on", "launched": "launched on",
              "released": "was released on", "opened": "opened on", "announced": "was announced on",
              "published": "was published on", "discontinued": "was discontinued on",
              "date": "is on", "started": "started on", "closed": "closed on", "acquired": "was acquired on"}
ADJECTIVE_END = ("ed", "able", "ible")
ADJECTIVES = {"available", "remote", "live", "profitable", "free", "open", "public", "anonymous", "carbon neutral"}


def _a(word: str) -> str:
    """The article for a word: "an uptime SLA", "a median time" (acronyms by their sound)."""
    first = word.split()[0] if word else ""
    vowel_sound = first[:1].lower() in "aeiou" or (first.isupper() and first[:1] in "AEFHILMNORSX")
    return "an" if vowel_sound else "a"


def words(attribute: str) -> str:
    """Attribute words with acronyms in capitals: `cto` -> CTO, `soc2_certified` -> SOC2 certified."""
    return " ".join(w.upper() if w in ACRONYMS else w for w in attribute_words(attribute).split())


def plain(subject: str, attribute: str, value: dict, past: bool = False) -> str | None:
    r = render(value)
    if r is None:
        return None
    return f"The {words(attribute)} of {subject} {'was' if past else 'is'} {r}"


def fact(subject: str, attribute: str, value: dict) -> list[str]:
    """Sentences stating that subject's attribute is value (no trailing dot)."""
    out = []
    kind = value.get("kind")
    w = words(attribute)
    toks = attribute.split("_")
    if kind == "boolean":
        adjective = toks[-1].endswith(ADJECTIVE_END) or w.lower() in ADJECTIVES or toks[-1] in ADJECTIVES
        if adjective:
            out.append(f"{subject} is {w}" if value["value"] else f"{subject} is not {w}")
        out.append(f"{subject} has {w}" if value["value"] else f"{subject} does not have {w}")
        return out
    r = render(value)
    if r is None:
        return out
    if kind == "date" and attribute in DATE_VERBS:
        out.append(f"{subject} {DATE_VERBS[attribute]} {r}")
    if kind == "quantity" and singular(str(value.get("unit", ""))) in {singular(t) for t in toks}:
        out.append(f"{subject} has {r}")  # "Hooly Cloud has 8 regions"
    if kind == "money" and any(t in ("price", "cost") for t in toks) and len(toks) <= 2:
        out.append(f"{subject} costs {r}")
    if kind in ("percent", "duration"):
        out.append(f"{subject} has {_a(w)} {w} of {r}")
    out.append(f"The {w} of {subject} is {r}")
    return out


def at_event(subject: str, attribute: str, value: dict, event: str) -> list[str]:
    r = render(value)
    if r is None:
        return []
    toks = attribute.split("_")
    out = []
    if value.get("kind") == "quantity" and singular(str(value.get("unit", ""))) in {singular(t) for t in toks}:
        out.append(f"{subject} had {r} at {_event(event)}")
    if value.get("kind") == "money" and any(t in ("price", "cost") for t in toks) and len(toks) <= 2:
        out.append(f"{subject} cost {r} at {_event(event)}")
    out.append(f"The {words(attribute)} of {subject} was {r} at {_event(event)}")
    return out


def change(subject: str, attribute: str, a: dict, b: dict) -> list[str]:
    ra, rb = render(a), render(b)
    if ra is None or rb is None:
        return []
    toks = attribute.split("_")
    out = []
    if a.get("kind") == "quantity" and singular(str(a.get("unit", ""))) in {singular(t) for t in toks}:
        out.append(f"{subject} went from {ra} to {rb}")
    if a.get("kind") == "money" and any(t in ("price", "cost") for t in toks) and len(toks) <= 2:
        out.append(f"The price of {subject} went from {ra} to {rb}")
    out.append(f"The {words(attribute)} of {subject} went from {ra} to {rb}")
    return out


def relation(subject: str, link: str, attribute: str, value: dict) -> list[str]:
    r = render(value)
    if r is None:
        return []
    who = f"The {words(link)} of {subject}"
    out = []
    if value.get("kind") == "date" and attribute in DATE_VERBS:
        out.append(f"{who} {DATE_VERBS[attribute]} {r}")  # "The CTO of Hooly joined on 1 July 2026"
    toks = attribute.split("_")
    if value.get("kind") == "quantity" and singular(str(value.get("unit", ""))) in {singular(t) for t in toks}:
        out.append(f"{who} has {r}")
    out.append(f"The {words(attribute)} of the {words(link)} of {subject} is {r}")
    return out


def _event(name: str) -> str:
    """An event's name mid-sentence: "the May 2026 outage" (names match in any case)."""
    return "the" + name[3:] if name.startswith("The ") else name


def compare(ls: str, la: str, rs: str, ra: str, phrase: str, kind: str) -> list[str]:
    out = []
    if kind == "date" and la == ra and la in DATE_VERBS:
        # "Hooly Pixel Fold was released later than Hooly Android 16"
        verb = "takes place" if la == "date" else DATE_VERBS[la][: -len(" on")]
        out.append(f"{ls} {verb} {phrase} {rs}")
    if la == ra and kind == "money" and la in ("price", "monthly_price", "cost") and phrase in ("higher than", "lower than", "the same as"):
        verb = {"higher than": "costs more than", "lower than": "costs less than", "the same as": "costs the same as"}[phrase]
        out.append(f"{ls} {verb} {rs}")
    if la == ra:
        out.append(f"The {words(la)} of {ls} is {phrase} that of {rs}")
    out.append(f"The {words(la)} of {ls} is {phrase} the {words(ra)} of {rs}")
    return out
