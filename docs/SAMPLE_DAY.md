# Sample day runbook: 29 October

The 20 sample rows land at **09:00**. The video and the pull request are due at **11:00**. **After 11:00 nobody pushes anything**, because that disqualifies the team.

## 08:30: get ready (captain's laptop)

1. Start **Docker Desktop** and wait for "Engine running".
2. Open a terminal in the repo and run `git checkout main` then `git pull origin main`.
3. Activate the environment: `.venv\Scripts\Activate.ps1`.
4. Start the API: `uvicorn server.app:app --port 8000`.
5. Open http://localhost:8000/api/health and wait until it shows `"warm": true`. That takes about a minute the first time, and seconds after that.
6. The frontend teammate starts the UI (or the built `web/dist` is served by the API at http://localhost:8000).

## 09:00: fetch the sample

```bash
git fetch upstream
git merge upstream/main
```

This brings `sample/sample.csv`. Check that it has 20 rows. Then run it exactly as the judges' pipeline would:

```bash
python scripts/run_local.py --sample
```

It must end with `the format checks pass`, and `out/output/output.csv` must hold a label for each `s-…` row.

## 09:15: record the video (deadline 11:00)

1. Open http://localhost:8000 for the story of one statement (scroll through it), then click **Run it live** (http://localhost:8000/console.html).
2. In the console, click **Load sample.csv**, then **Run polygraph**. It takes about 4 seconds; the diagram lights up and every row gets its verdict.
2. Click two or three FALSE rows to show the evidence board. Each one has a timeline and a one-line "why".
3. Show the **Claim Forge** tab: the 1,000 claims and their types.
4. Keep the architecture diagram on screen throughout. The rules require it beside the run.

Rehearse once at 09:10 before recording.

## 10:15: freeze the code

1. Run `python -m pytest`, which must pass.
2. Run `sh scripts/check_windows.sh` (or `sh scripts/check.sh` on Mac/Linux). It must end with `the format checks pass`.
3. Run `git push origin main`.

## 10:30: open the pull request

- From our fork's `main` to `QA-DNA/hype-arena-starter` `main`.
- **The title is the team name.**
- The description says how to start everything:
  - System: `docker build --platform linux/amd64 .` (the root `Dockerfile`).
  - Frontend: `pip install -r requirements-dev.txt`, then `uvicorn server.app:app --port 8000`, then open http://localhost:8000.
- Submit the video link as the organizers ask.

## 10:45: hands off

Nothing more gets pushed to `main`. A push after 11:00 disqualifies us.

## If something breaks

| Problem | Fix |
| --- | --- |
| `"warm": false` for over 2 minutes | Restart uvicorn; the first warm-up trains the extractor (~1 min) |
| The run is slow | Normal for the very first request; later ones take about 4 s |
| `check.sh` fails on Windows with `/universe/universe.csv` missing | Use `scripts/check_windows.sh` |
| The sample has new subjects | Expected; the engine handles unseen names through the lexicon |
