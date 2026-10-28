"""Records what every stage actually computed for chosen rows, for the "inside the machine"
view. Off unless start() names rows; recording never changes what the stages compute.

Stages call put(row_id, key, value); a later call for the same key overwrites an earlier
one, so with self-training (two passes) what's kept is the final pass, the one the verdict
comes from.
"""
from __future__ import annotations

import json
import threading

LOCK = threading.Lock()  # one recording at a time (the server traces in a background thread)
IDS: set[str] = set()
ROWS: dict[str, dict] = {}

# the judge's 61 row features, in the order judge.row_features builds them, then the 3 page
# features of the second pass (judge._page_scores)
FEATURES = [
    "facts found", "facts that agree with their timeline", "facts that are stale", "facts that are premature",
    "facts never true (invented)", "facts with no other evidence", "share of facts that agree",
    "worst status (0 none .. 5 invented)", "other mentions of the worst fact (log)",
    "mentions with the same value, any date (log)", "mentions with the same value within 30 days (log)",
    "mentions with a different value within 30 days (log)", "confirmed-true rows with the same value",
    "labelled-false rows with the same value", "confirmed-true rows with the same value within 30 days",
    "days to the nearest other mention", "lowest extraction score", "mean extraction score",
    "trust of the rest of the page", "sentences on the page", "labelled-false sentences on the page",
    "labelled-true sentences on the page", "labelled-unsure sentences on the page", "has a speaker (\"Name:\")",
    "the speaker is Gavin", "hedging words (\"I have been told\")", "hype words", "first person (we, our, I)",
    "future words (will, soon, plan)", "now words (today, currently)", "question mark", "exclamation mark",
    "sentence length", "days since 1 Oct 2025", "states a yes/no fact", "a value with a comparison word",
    "nearest earlier mention has the same value", "nearest later mention has the same value",
    "the value is the most common one", "distinct values this fact has had",
    "weighted support for the same value within 60 days", "weighted support for other values within 60 days",
    "labelled-false rows nearby with a different value", "same-value mentions per fact",
    "different-value mentions nearby per fact", "the same sentence labelled elsewhere (1 true, 0 false, 0.5 unsure)",
    "unit matches the timeline's value", "relative difference from the timeline's value",
    "the value belongs to another attribute of the subject", "extraction score of the worst fact",
    "confirmed-true rows nearby with a different value", "days to the nearest confirmed-true different value",
    "days to the nearest confirmed-true same value", "a confirmed row with another value is closer",
    "newer values since this one was last seen (weight)", "newer values since, confirmed",
    "older values still held before this one first appears (weight)", "older values still held, confirmed",
    "other values before this one ever appears", "other values after this one stops appearing",
    "the same value seen both before and after",
    "page: mean first-pass P(false) of the other sentences", "page: highest first-pass P(false) of the others",
    "page: other sentences the first pass calls false",
]


def start(ids) -> None:
    IDS.clear()
    IDS.update(ids)
    ROWS.clear()


def stop() -> None:
    IDS.clear()


def on(row_id: str) -> bool:
    return row_id in IDS


def put(row_id: str, key: str, value) -> None:
    if row_id in IDS:
        ROWS.setdefault(row_id, {})[key] = plain(value)


def plain(x):
    """JSON-safe copy (numpy numbers, tuples, sets)."""
    return json.loads(json.dumps(x, default=_default))


def _default(o):
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if hasattr(o, "__dict__"):
        return o.__dict__
    return str(o)
