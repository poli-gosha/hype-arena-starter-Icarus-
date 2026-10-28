"""How good are our 1,000 claims? Valid (our referee clone) and true (gold knowledge base).

    python scripts/eval_claims.py            # claims from a run with every 5th label hidden
    python scripts/eval_claims.py --show 15  # print 15 claims of each verdict

Truth is checked against a knowledge base built from ALL practice labels (the gold forms of
every `true` row): the best stand-in for the referee's universe we have. "unknown" means the
gold KB can't say (e.g. a fact only extracted from unlabelled rows).
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from polygraph import AS_OF, pipeline  # noqa: E402
from polygraph.kb import KB  # noqa: E402
from polygraph.lexicon import Lexicon  # noqa: E402
from polygraph.model import value_key  # noqa: E402
from polygraph.validate import validate  # noqa: E402

DUR = {"ms": 0.001, "s": 1, "min": 60, "h": 3600, "day": 86400, "week": 604800}


def num(v):
    import json
    return json.loads(value_key(v))["value"]


def truth(c, gold: KB) -> str:
    f = c.form
    if c.type == "fact":
        st = gold.current(f["subject"], f["attribute"])
        return "unknown" if st is None else ("true" if value_key(st.value) == value_key(f["value"]) else "FALSE")
    if c.type == "at_event":
        day = gold.events.get(f["event"])
        st = gold.value_on(f["subject"], f["attribute"], day) if day and len(day) == 10 else None
        return "unknown" if st is None else ("true" if value_key(st.value) == value_key(f["value"]) else "FALSE")
    if c.type == "change":
        steps = gold.timeline(f["subject"], f["attribute"])
        if not steps:
            return "unknown"
        ks = [value_key(s.value) for s in steps]
        a, b = value_key(f["from"]), value_key(f["to"])
        ok = any(ks[i] == a and b in ks[i + 1:] for i in range(len(ks)))
        return "true" if ok else "FALSE"
    if c.type == "compare":
        l = gold.current(f["left"]["subject"], f["left"]["attribute"])
        r = gold.current(f["right"]["subject"], f["right"]["attribute"])
        if l is None or r is None:
            return "unknown"
        if l.value["kind"] == "date":
            lv, rv = l.value["value"], r.value["value"]
        else:
            try:
                lv, rv = float(num(l.value)), float(num(r.value))
            except (TypeError, ValueError):
                return "unknown"
        op = "gt" if lv > rv else "lt" if lv < rv else "eq"
        return "true" if op == f["op"] else "FALSE"
    if c.type == "relation":
        links = gold.timeline(f["subject"], f["link"])
        target_steps = [s for s in links if gold.lexicon.canonical(s.value.get("value", "")) == f["target"]]
        if not target_steps:
            return "unknown"
        for ls in target_steps:
            for ts in gold.timeline(f["target"], f["attribute"]):
                if value_key(ts.value) == value_key(f["value"]) and ts.start < (ls.end or "9999") and ls.start < (ts.end or "9999"):
                    return "true"
        return "FALSE" if gold.timeline(f["target"], f["attribute"]) else "unknown"
    return "unknown"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--show", type=int, default=0)
    p.add_argument("--keep", type=int, default=0,
                   help="keep only every Nth label (10: the judges' run, where ~10%% of rows are labelled)")
    a = p.parse_args()
    lex = Lexicon.load(ROOT / "data" / "lexicon.json")
    b = pipeline.Bundle.load()
    gold = KB.from_gold(lex, b.rows, b.forms)
    if a.keep:
        rows = [replace(r, label=r.label if i % a.keep == 0 else "") for i, r in enumerate(b.rows)]
        res = pipeline.run(rows, lex, b, cache=ROOT / "out" / "cache" / f"keep{a.keep}.pkl")
    else:
        rows = [replace(r, label="" if i % 5 == 0 else r.label) for i, r in enumerate(b.rows)]
        res = pipeline.run(rows, lex, b, cache=ROOT / "out" / "cache" / "fold0.pkl")
    by = Counter()
    examples = {}
    for c in res.claims:
        v = "INVALID" if validate(c, lex) else truth(c, gold)
        by[(c.type, v)] += 1
        examples.setdefault(v, []).append(c)
    types = ["fact", "compare", "change", "at_event", "relation"]
    print(f"{len(res.claims)} claims         " + "".join(f"{t:>10}" for t in types) + "     total")
    for v in ("true", "unknown", "FALSE", "INVALID"):
        print(f"  {v:<16}" + "".join(f"{by[(t, v)]:>10}" for t in types) + f"{sum(by[(t, v)] for t in types):>10}")
    # how truth holds up by confidence (0.93+: confirmed by labelled rows; below: support alone)
    for lo, hi in ((0.93, 1.01), (0.9, 0.93), (0.0, 0.9)):
        cs = [c for c in res.claims if lo <= c.confidence < hi]
        vs = Counter("INVALID" if validate(c, lex) else truth(c, gold) for c in cs)
        print(f"  confidence {lo:.2f}-{min(hi, 1):.2f}: {len(cs):4d} claims, {vs['true']} true, {vs['FALSE']} false, {vs['unknown']} unknown")
    if a.show:
        for v in ("FALSE", "unknown", "true"):
            print(f"\n== {v}")
            for c in examples.get(v, [])[: a.show]:
                print(f"  {c.confidence:.2f} [{c.type}] {c.text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
