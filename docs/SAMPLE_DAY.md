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

1. Open http://localhost:8000 and scroll through the story of one statement (the architecture, shape by shape).
2. Click **Run it live** (http://localhost:8000/console.html). Tick **Also label the 20 sample sentences**, then
   **Build and run in Docker**. It builds our image and runs it exactly like the judges' check (2 to 3 minutes).
3. **Prove it's really Docker**, on camera, while it runs: switch to Docker Desktop → **Containers**. The
   container named on the page (`polygraph-live-…`) is there, *Running*. Its logs in Docker Desktop are the same
   lines the page shows. (Or run `docker ps --filter name=polygraph-live` in a terminal.)
4. Back on the page: the results, the organisers' checker output, and the **Proof it ran in Docker** panel
   (image id, container id, and its settings read back from Docker: user 10001, no network, read-only, 2 CPUs, 6 GB).
   Filter the sentence table with **Sample rows** to show the sample's verdicts.
5. Click **Download output.csv** and open it: the table the container wrote.

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
