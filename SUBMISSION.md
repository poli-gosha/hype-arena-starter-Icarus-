# Team Icarus · Polygraph

## The system (what you run)

The `Dockerfile` at the root builds it: `docker build --platform linux/amd64 .`, then the image reads
`/universe/universe.csv` and `/universe/lexicon.json` and writes `/output/output.csv`. No LLM runs: a
rule-based reader, a gradient-boosted attributor, a temporal truth engine and a judge trained at run
time on the labelled rows. It writes a safe table within seconds, then the final one, swapped in
whole. On a run the size of yours: about 19,000 rows in 200 s and 0.8 GB, within 2 CPUs, 6 GiB and
30 minutes. How it works: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## The frontend (what starts it)

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt          # Windows: .venv\Scripts\pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn server.app:app --port 8000  # Windows: .venv\Scripts\python -m uvicorn server.app:app --port 8000
```

Then open <http://localhost:8000>:

| Page | What |
|---|---|
| `/` | The Ministry of Statements: one statement through every stage, guided by Caesar, with the date pin, the stamp and the cheese game |
| `/console.html` | The live desk: builds the Docker image and runs it like your check, on the practice rows plus the 20 sample rows (`datasets/sample.csv`), with the output to download |
| `/inside.html` | Inside the machine: any sample sentence traced through the architecture, stage by stage |

The live desk needs Docker running. The pitch film is `video/inspection/inspection.mp4`.
