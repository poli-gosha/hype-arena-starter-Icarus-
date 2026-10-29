"""The API the frontend calls. Runs the same engine as the Docker image.

    uvicorn server.app:app --reload --port 8000       (from the repo root, venv active)

Endpoints (contract in docs/BRIEF_frontend.md):
  GET  /api/health        -> {"ok": true}
  GET  /api/architecture  -> the pipeline stages, for the diagram
  POST /api/run           -> body {"rows": [{id, text, date}], "include_claims": false}
                             runs the system on the practice universe + these rows and
                             returns the trace JSON for just these rows
  GET  /api/sample        -> the rows of sample/sample.csv (from 09:00 on 29 Oct), if present
  GET  /api/claims        -> the 1,000 claims the system writes on the practice universe
  POST /api/live/start    -> body {"sample": false}: build our Docker image and run it like the
                             judges' check, in the background (server/live.py)
  GET  /api/live/status   -> its steps, log and, when done, the results
  GET  /api/live/output.csv -> the table the container wrote
The site at / is web/dist (a built UI) if it exists, else server/static: index.html is the
immersive story of one statement, console.html the live console that runs the system.
"""
from __future__ import annotations

import csv
import sys
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from polygraph import pipeline  # noqa: E402
from polygraph.lexicon import Lexicon  # noqa: E402
from polygraph.model import Row  # noqa: E402
from polygraph.trace import to_trace  # noqa: E402
from server.live import JOB, RUN  # noqa: E402

app = FastAPI(title="Polygraph")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def fresh_pages(request, call_next):
    """Pages are re-checked on every load, so a changed page never shows an old copy."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache"
    return response

STAGES = [
    {"id": "reader", "name": "Reader", "what": "Reads every value as the referee does: money, counts, dates, versions, yes/no"},
    {"id": "linker", "name": "Linker", "what": "Finds which Hooly subjects a sentence names (lexicon + page context)"},
    {"id": "attributor", "name": "Attributor", "what": "Decides which attribute each value is about"},
    {"id": "truth", "name": "Truth engine", "what": "Rebuilds each fact's timeline from 20,000 rows, weighting trusted pages"},
    {"id": "judge", "name": "Judge", "what": "True / false / unsure per row with a calibrated confidence"},
    {"id": "forge", "name": "Claim forge", "what": "Writes 1,000 new true claims and checks each with our referee clone"},
]


class InRow(BaseModel):
    id: str
    text: str
    date: str


class RunRequest(BaseModel):
    rows: list[InRow]
    include_claims: bool = False


WARM: dict = {}  # the trained attributor + out-of-fold extraction, reused by every request
WARM_FILE = ROOT / "out" / "cache" / "warm.pkl"


def _warm_up():
    """Train once (about a minute), or load the last training from disk."""
    import pickle
    lexicon, bundle = universe()
    if not WARM and WARM_FILE.exists():
        try:
            WARM.update(pickle.loads(WARM_FILE.read_bytes()))
        except Exception:
            WARM.clear()
    if not WARM:
        pipeline.run(list(bundle.rows), lexicon, bundle, claims=False, warm=WARM)
        WARM_FILE.parent.mkdir(parents=True, exist_ok=True)
        WARM_FILE.write_bytes(pickle.dumps(WARM))


@app.on_event("startup")
def _start_warming():
    import threading
    threading.Thread(target=_warm_up, daemon=True).start()


@lru_cache(maxsize=1)
def universe():
    lexicon = Lexicon.load(ROOT / "data" / "lexicon.json")
    bundle = pipeline.Bundle.load()
    return lexicon, bundle


@app.get("/api/health")
def health():
    return {"ok": True, "warm": bool(WARM)}


@app.get("/api/architecture")
def architecture():
    return {"stages": STAGES, "edges": [[a["id"], b["id"]] for a, b in zip(STAGES, STAGES[1:])]}


@app.post("/api/run")
def run(req: RunRequest):
    lexicon, bundle = universe()
    base = list(bundle.rows)
    page = (base[-1].page + 1) if base else 0
    new = []
    for i, r in enumerate(req.rows):
        if i and r.date != req.rows[i - 1].date:
            page += 1
        new.append(Row(r.id, r.text, r.date, "", page))
    from polygraph import explain
    with explain.LOCK:  # never while a trace is recording
        res = pipeline.run(base + new, lexicon, bundle, claims=req.include_claims, warm=WARM)
    trace = to_trace(new, res)
    return trace


@app.get("/api/sample")
def sample():
    path = next((p for p in (ROOT / "datasets" / "sample.csv", ROOT / "sample" / "sample.csv") if p.exists()),
                ROOT / "datasets" / "sample.csv")
    if not path.exists():
        return {"rows": [], "note": "sample/sample.csv appears at 09:00 on 29 Oct"}
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {"rows": [{"id": r["id"], "text": r["text"], "date": r["date"]} for r in csv.DictReader(f)]}


@lru_cache(maxsize=1)
def _claims():
    lexicon, bundle = universe()
    res = pipeline.run(list(bundle.rows), lexicon, bundle, warm=WARM)
    return to_trace([], res)["claims"]


@app.get("/api/claims")
def claims():
    return {"claims": _claims()}


class LiveRequest(BaseModel):
    sample: bool = False


@app.post("/api/live/start")
def live_start(req: LiveRequest):
    if not JOB.start(req.sample):
        raise HTTPException(409, "a run is already in progress")
    return JOB.status()


@app.get("/api/live/status")
def live_status(full: bool = False):
    s = JOB.status()
    if full and JOB.result:
        s["result"] = JOB.result
    elif JOB.result:
        s["result"] = {k: v for k, v in JOB.result.items() if k not in ("rows", "claims")}
    return s


@app.get("/api/trace/index")
def trace_index():
    """The sentences of the last live run, with whether each has a trace."""
    if not JOB.result:
        return {"rows": [], "note": "run the live check first"}
    return {"rows": [{k: r.get(k) for k in ("id", "text", "date", "label", "confidence", "truth", "sample", "traced")}
                     for r in JOB.result["rows"]], "trace": JOB.result.get("trace")}


@app.get("/api/trace/row/{row_id}")
def trace_row(row_id: str):
    t = JOB.trace.get(row_id)
    if t is None:
        raise HTTPException(404, "no trace for this sentence")
    docker = next((r for r in JOB.result["rows"] if r["id"] == row_id), None) if JOB.result else None
    from polygraph import explain
    return {"trace": t, "docker": docker, "feature_names": explain.FEATURES}


@app.get("/api/live/output.csv")
def live_output():
    path = RUN / "output" / "output.csv"
    if not path.exists():
        raise HTTPException(404, "no run has finished yet")
    return FileResponse(path, media_type="text/csv", filename="output.csv")


# the frontend teammate's built UI if there is one, else our own console (server/static)
WEB = ROOT / "web" / "dist" if (ROOT / "web" / "dist" / "index.html").exists() else ROOT / "server" / "static"
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
