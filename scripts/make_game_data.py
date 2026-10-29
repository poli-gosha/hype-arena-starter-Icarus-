"""The cheese game's statements: pairs of real practice sentences, one true and one false, with
what Polygraph said about each and the archive's reason.

    .venv\\Scripts\\python.exe scripts\\make_game_data.py

Reads the last live run (out/live/trace.json, out/live/result.json): its hidden practice rows carry
the true label, Polygraph's verdict and the timeline status. Writes server/static/assets/cheese.json.
"""
from __future__ import annotations

import datetime as dt
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from polygraph.render import attribute_words, render  # noqa: E402

LIES = ("stale", "premature", "invented")


def day(s: str) -> str:
    return dt.date.fromisoformat(s).strftime("%-d %b %Y") if sys.platform != "win32" else dt.date.fromisoformat(s).strftime("%#d %b %Y")


def human(v: dict) -> dict:
    """Bytes and seconds back into the units people write."""
    v = dict(v)
    if v.get("kind") == "quantity" and v.get("unit") == "B":
        for u, k in (("TB", 10 ** 12), ("GB", 10 ** 9), ("MB", 10 ** 6), ("KB", 10 ** 3)):
            if v["value"] >= k:
                x = v["value"] / k
                return {"kind": "quantity", "value": int(x) if x == int(x) else round(x, 2), "unit": u}
    if v.get("kind") == "duration" and v.get("unit") == "s":
        for u, k in (("day", 86400), ("hour", 3600), ("min", 60)):
            if v["value"] >= k and v["value"] % k == 0:
                return {**v, "value": int(v["value"] // k), "unit": u}
    return v


def reason(r: dict, status: str, f: dict | None) -> str:
    date = day(r["row"]["date"])
    if not f:
        return f"The labelled data says this is {'true' if status == 'true' else 'false'}."
    said = render(human(f["value"])) or str(f["value"].get("value"))
    held = (render(human(f["held_on_date"])) or str(f["held_on_date"].get("value"))) if f.get("held_on_date") else None
    what = f"{f['subject']}'s {attribute_words(f['attribute'])}"
    if status == "agrees":
        return f"The archive holds {held or said} for {what} on {date}."
    if status == "stale":
        return f"{said} was true earlier; on {date} the archive holds {held} for {what}." if held else f"{said} was true earlier, not on {date}."
    if status == "premature":
        return f"{said} only becomes true later; on {date} the archive holds {held} for {what}." if held else f"{said} only becomes true after {date}."
    return f"No document ever gives {said} for {what}" + (f"; on {date} it is {held}." if held else ".")


def main() -> int:
    trace = json.loads((ROOT / "out" / "live" / "trace.json").read_text(encoding="utf-8"))
    trace = trace.get("rows", trace) if isinstance(trace, dict) and "rows" in trace else trace
    result = json.loads((ROOT / "out" / "live" / "result.json").read_text(encoding="utf-8"))
    truth = {r["id"]: r.get("truth") for r in result["rows"]}
    lies, trues, missed = [], [], []
    for rid, r in trace.items():
        if "verdict" not in r or "truth" not in r or not truth.get(rid):
            continue
        text = r["row"]["text"].strip()
        if len(text) > 82 or len(text) < 18:
            continue
        worst = r["truth"]["worst"]
        f = next((x for x in r["truth"]["facts"] if x["status"] == worst), None)
        v = r["verdict"]
        item = {"id": rid, "text": text, "date": day(r["row"]["date"]), "truth": truth[rid],
                "polygraph": {"label": v["label"], "confidence": round(v["confidence"] or 0, 2)}}
        if truth[rid] == "false" and v["label"] == "false" and worst in LIES and f:
            lies.append({**item, "kind": worst, "why": reason(r, worst, f)})
        elif truth[rid] == "true" and v["label"] == "true" and worst == "agrees" and f:
            trues.append({**item, "kind": "true", "why": reason(r, "agrees", f)})
        elif truth[rid] == "false" and v["label"] == "true":
            missed.append({**item, "kind": "missed", "why": "The labelled data says this is false. Polygraph missed it: it doesn't catch every lie."})
    rnd = random.Random(29)
    rnd.shuffle(lies)
    rnd.shuffle(trues)
    by_kind = {k: [x for x in lies if x["kind"] == k] for k in LIES}
    picked = []
    while len(picked) < 14 and any(by_kind.values()):  # every kind of lie, in turn
        for k in LIES:
            if by_kind[k] and len(picked) < 14:
                picked.append(by_kind[k].pop())
    picked += missed[:2]  # Polygraph isn't perfect, and the game says so
    pairs = []
    for lie, tru in zip(picked, trues):
        a, b = (lie, tru) if rnd.random() < 0.5 else (tru, lie)
        pairs.append([a, b])
    rnd.shuffle(pairs)
    out = ROOT / "server" / "static" / "assets" / "cheese.json"
    out.write_text(json.dumps({"pairs": pairs}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(pairs)} pairs; lies by kind:", {k: sum(1 for p in picked if p['kind'] == k) for k in (*LIES, 'missed')},
          f"(from {len(lies)} lies, {len(trues)} truths)")
    for p in pairs[:4]:
        for s in p:
            print(f"  [{s['kind']:<9}] {s['text']}  ({s['date']}) -> {s['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
