"""Reading the input table and writing the output table (contracts/README.md)."""
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

from .model import Claim, Row, Verdict, dumps

COLUMNS = ["id", "type", "text", "form", "label", "confidence"]


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def iso_date(s: str) -> str | None:
    """A page date as YYYY-MM-DD, from the forms a CSV might hold it in; None if unreadable.
    The engine compares dates as text, so every row must carry this one form."""
    s = (s or "").strip()
    m = re.fullmatch(r"(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?(?:[T ].*)?", s)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3] or 1)
    elif m := re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s):  # day first, as Europe writes it
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
        if mo > 12 >= d:
            d, mo = mo, d
    elif m := re.fullmatch(r"(?:(\d{1,2})\s+)?([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", s):  # 14 April 2026, April 2026
        if m[2].lower() not in MONTHS:
            return None
        d, mo, y = int(m[1] or 1), MONTHS[m[2].lower()], int(m[3])
    else:
        return None
    try:
        import datetime as dt
        return dt.date(y, mo, d).isoformat()
    except ValueError:
        return None


def read_rows(path: str | Path) -> list[Row]:
    """Rows of universe.csv (or practice.csv), with pages numbered: a page is a run of
    consecutive rows sharing a date. A date that can't be read takes the row before's (its
    page's, most likely)."""
    rows: list[Row] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        raw = [{(k or "").strip().lower(): (v or "") for k, v in r.items()} for r in csv.DictReader(f)]
    dates = [iso_date(r.get("date", "")) for r in raw]
    first = next((d for d in dates if d), "2026-06-01")
    page, last, prev = -1, None, first
    for r, d in zip(raw, dates):
        d = d or prev
        prev = d
        if d != last:
            page, last = page + 1, d
        label = r.get("label", "").strip().lower()
        rows.append(Row(r.get("id", "").strip(), r.get("text", ""), d, label, page))
    return rows


def read_practice_forms(path: str | Path) -> dict[str, list[dict]]:
    """id -> the facts the practice row states (its `form` column)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {r["id"]: json.loads(r["form"]) for r in csv.DictReader(f) if r.get("form")}


def _conf(c: float | None) -> str:
    return "" if c is None else f"{min(1.0, max(0.5, c)):.3f}"


def write_output(path: str | Path, verdicts: list[Verdict], claims: list[Claim]) -> None:
    """Write the table under a temporary name, then rename it, so a half-written table
    never counts (contracts/README.md)."""
    path = Path(path)
    tmp = path.with_name(path.name + ".partial")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for v in verdicts:
            w.writerow([v.id, "", "", "", v.label, "" if v.label == "unsure" else _conf(v.confidence)])
        for c in claims:
            w.writerow([c.id, c.type, c.text, dumps(c.form), "true", _conf(c.confidence)])
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
