"""Run the real entrypoint (python -m polygraph.run) on awkward variants of the practice
input, and check each table: what the judges' input could look like that practice doesn't.

    python scripts/robustness.py [variant ...]      (all variants by default)

Each variant hides every fifth label as scripts/input.py does, then bends one thing. For
each it prints whether the run finished, the table check, label accuracy on the hidden
rows, the claims count and the time.
"""
from __future__ import annotations

import csv
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "robust"


def practice():
    with open(ROOT / "data" / "practice.csv", encoding="utf-8-sig", newline="") as f:
        rows = [{k: r[k] for k in ("id", "text", "date", "label")} for r in csv.DictReader(f)]
    truth = {}
    for i, r in enumerate(rows):
        if i % 5 == 0:
            truth[r["id"]] = r["label"]
            r["label"] = ""
    return rows, truth


def v_baseline(rows, truth):
    return rows, truth


def v_renamed_ids(rows, truth):
    """The judges' file gives the practice rows ids of its own."""
    ren = {r["id"]: f"u{1000 + i}" for i, r in enumerate(rows)}
    return [{**r, "id": ren[r["id"]]} for r in rows], {ren[k]: v for k, v in truth.items()}


def v_shuffled(rows, truth):
    """Rows in random order: pages no longer runs of consecutive rows."""
    rows = list(rows)
    random.Random(1).shuffle(rows)
    return rows, truth


def v_sorted_by_date(rows, truth):
    """Rows sorted by date: every page of a day merges into one."""
    return sorted(rows, key=lambda r: r["date"]), truth


def v_bad_dates(rows, truth):
    """A few dates empty or in other formats."""
    rows = [dict(r) for r in rows]
    forms = ["", "2026/04/14", "14.04.2026", "2026-04-14T09:30:00Z", "April 2026", "2026-4-7", "nonsense"]
    for i, f in zip(range(3, len(rows), 97), forms * 10):
        rows[i]["date"] = f
    return rows, truth


def v_odd_rows(rows, truth):
    """Empty and huge texts, quotes, line breaks, odd labels, a duplicated id."""
    rows = [dict(r) for r in rows]
    rows[7]["text"] = ""
    rows[11]["text"] = "Hooly " * 2000
    rows[13]["text"] = 'He said "it costs €59,\nper month" — 🚀 ' + rows[13]["text"]
    rows[17]["label"] = rows[17]["label"].upper() if rows[17]["label"] else ""
    rows[19]["label"] = " " + (rows[19]["label"] or "") + " "
    rows[23]["label"] = rows[23]["label"] and "maybe"
    rows.append(dict(rows[5]))  # a duplicated id (unlabelled or not, as the original)
    return rows, truth


def v_no_labels(rows, truth):
    """No labelled row at all."""
    return [{**r, "label": ""} for r in rows], {}


def v_big(rows, truth):
    """Ten times the rows (each practice row again under new ids, a day later), unlabelled."""
    out = list(rows)
    for k in range(1, 10):
        for r in rows:
            out.append({**r, "id": f"{r['id']}-c{k}", "label": ""})
    return out, truth


VARIANTS = {name[2:]: fn for name, fn in globals().items() if name.startswith("v_")}


def run(name: str) -> dict:
    rows, truth = VARIANTS[name](*practice())
    folder = OUT / name
    uni, out = folder / "universe", folder / "output"
    uni.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / "output.csv").unlink(missing_ok=True)
    with open(uni / "universe.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "text", "date", "label"])
        w.writeheader()
        w.writerows(rows)
    (uni / "lexicon.json").write_bytes((ROOT / "data" / "lexicon.json").read_bytes())
    t = time.time()
    p = subprocess.run([sys.executable, "-m", "polygraph.run", "--universe", str(uni), "--output", str(out)],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    secs = time.time() - t
    (folder / "log.txt").write_text(p.stdout + "\n" + p.stderr, encoding="utf-8")
    res = {"variant": name, "exit": p.returncode, "seconds": round(secs), "error": (p.stderr.strip().splitlines() or [""])[-1][:160]}
    path = out / "output.csv"
    if not path.exists():
        return {**res, "table": "MISSING"}
    with open(path, encoding="utf-8", newline="") as f:
        table = list(csv.DictReader(f))
    labels = {}
    for r in table:
        if not r["type"]:
            labels.setdefault(r["id"], r["label"])
    claims = [r for r in table if r["type"]]
    unl = [r["id"] for r in rows if not r["label"].strip()]
    right = sum(labels.get(i) == truth[i] for i in truth if i in labels)
    res.update(table="ok", labels=len(labels), unlabelled=len(set(unl)), missing=len(set(unl) - set(labels)),
               bad_labels=sum(v not in ("true", "false", "unsure") for v in labels.values()),
               accuracy=round(right / max(1, len(truth)), 4) if truth else None, claims=len(claims),
               claim_ids_unique=len({c["id"] for c in claims}) == len(claims),
               safe_only="final output written" not in p.stdout)
    return res


if __name__ == "__main__":
    names = sys.argv[1:] or list(VARIANTS)
    for n in names:
        r = run(n)
        print(json.dumps(r), flush=True)
