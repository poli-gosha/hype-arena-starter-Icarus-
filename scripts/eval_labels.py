"""Label accuracy over all 5 folds, the number to push up.

    python scripts/eval_labels.py          # first run extracts and caches (~5 min), then ~seconds
    python scripts/eval_labels.py --fresh  # re-extract (after changing reader/linker/attributor)

Prints per-fold and mean exact match, the all-true baseline, and the Brier score.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from polygraph import pipeline  # noqa: E402
from polygraph.lexicon import Lexicon  # noqa: E402

CACHE = ROOT / "out" / "cache"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--folds", type=int, default=5)
    p.add_argument("--gold", action="store_true", help="perfect extraction: the ceiling of the truth engine + judge")
    p.add_argument("--partitions", type=int, default=1,
                   help="2: also hide labels by a second, independent split (sturdier, twice as slow)")
    a = p.parse_args()
    if a.fresh:
        shutil.rmtree(CACHE, ignore_errors=True)
    lexicon = Lexicon.load(ROOT / "data" / "lexicon.json")
    bundle = pipeline.Bundle.load()
    truth = {r.id: r.label for r in bundle.rows}
    tot = Counter()
    import hashlib
    runs = [(part, k) for part in range(a.partitions) for k in range(a.folds)]
    for part, k in runs:
        if part == 0:  # the split scripts/input.py uses: every 5th row
            hide = lambda i, r: i % 5 == k  # noqa: E731
        else:  # an independent split: by a hash of the row id
            hide = lambda i, r: int(hashlib.md5(f"{part}:{r.id}".encode()).hexdigest(), 16) % 5 == k  # noqa: E731
        rows = [replace(r, label="" if hide(i, r) else r.label) for i, r in enumerate(bundle.rows)]
        tag = f"{'gold' if a.gold else 'fold'}{k}" + (f"-p{part}" if part else "")
        res = pipeline.run(rows, lexicon, bundle, claims=False, gold_extraction=a.gold, cache=CACHE / f"{tag}.pkl")
        cm = Counter((truth[v.id], v.label) for v in res.verdicts)
        n = sum(cm.values())
        right = sum(c for (t, q), c in cm.items() if t == q)
        base = sum(c for (t, _), c in cm.items() if t == "true")
        brier = sum(((v.confidence or 0.5) - (truth[v.id] == v.label)) ** 2 for v in res.verdicts if v.label != "unsure")
        tot.update({"n": n, "right": right, "base": base, "brier": brier,
                    "fp": cm[("true", "false")], "fn": cm[("false", "true")], "caught": cm[("false", "false")],
                    "lies": sum(c for (t, _), c in cm.items() if t == "false")})
        print(f"split {part} fold {k}: {right / n:.3f}  (all-true {base / n:.3f})  true->false {cm[('true', 'false')]:3d}  "
              f"false caught {cm[('false', 'false')]}/{sum(c for (t, _), c in cm.items() if t == 'false')}")
    print(f"MEAN  : {tot['right'] / tot['n']:.4f}  (all-true {tot['base'] / tot['n']:.4f})  "
          f"Brier {tot['brier'] / tot['n']:.3f}  lies caught {tot['caught']}/{tot['lies']}, true rows flagged {tot['fp']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
