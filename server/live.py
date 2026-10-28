"""The live run: build our Docker image and run it exactly as the judges' check does.

Steps, in a background thread:
  1. build    docker build --platform linux/amd64 (the Dockerfile at the repo root)
  2. prepare  the input like scripts/check.sh: the 1,897 practice rows with every 5th label
              hidden (scripts/input.py), the lexicon, and optionally the 20 sample rows
  3. run      docker run offline, read-only, user 10001, 2 CPUs, 6 GiB, 30-minute deadline;
              its log lines and peak memory are tracked while it runs
  4. check    the organisers' own checker (scripts/check_output.py), then our labels on the
              hidden rows scored against the practice labels

The container's real /output/output.csv is kept for download.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "out" / "live"
IMAGE = "polygraph-live"
STEPS = [("build", "Build the Docker image"), ("prepare", "Prepare the input"),
         ("run", "Run the container"), ("check", "Check the output")]


def docker_exe() -> str | None:
    for c in (shutil.which("docker"), r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"):
        if c and Path(c).exists():
            return c
    return None


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()
        saved = RUN / "result.json"
        if saved.exists():  # the last finished run survives a server restart
            try:
                self.result = json.loads(saved.read_text(encoding="utf-8"))
                self.state = "done"
                self.steps = [{"id": i, "name": n, "status": "done", "seconds": None} for i, n in STEPS]
            except ValueError:
                pass

    def reset(self):
        self.state = "idle"  # idle | running | done | failed
        self.steps = [{"id": i, "name": n, "status": "waiting", "seconds": None} for i, n in STEPS]
        self.log: list[str] = []
        self.error = None
        self.result = None
        self.started = None
        self.peak_mb = 0.0

    def say(self, line: str):
        line = line.rstrip()
        if line:
            self.log.append(line)
            del self.log[:-400]

    def status(self) -> dict:
        return {"state": self.state, "steps": self.steps, "log": self.log[-60:], "error": self.error,
                "elapsed": round(time.time() - self.started, 1) if self.started and self.state == "running" else None,
                "peak_mb": round(self.peak_mb), "has_result": self.result is not None,
                "docker": docker_exe() is not None, "sample_available": (ROOT / "sample" / "sample.csv").exists()}

    def start(self, with_sample: bool) -> bool:
        with self.lock:
            if self.state == "running":
                return False
            self.reset()
            self.state, self.started = "running", time.time()
        threading.Thread(target=self._run, args=(with_sample,), daemon=True).start()
        return True

    # ---- the four steps --------------------------------------------------------------------
    def _step(self, sid: str, status: str, seconds=None):
        for s in self.steps:
            if s["id"] == sid:
                s["status"] = status
                if seconds is not None:
                    s["seconds"] = round(seconds, 1)

    def _run(self, with_sample: bool):
        docker = docker_exe()
        current = "build"
        try:
            if docker is None:
                raise RuntimeError("Docker isn't installed or isn't on this computer's PATH.")
            info = subprocess.run([docker, "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True)
            if info.returncode != 0:
                raise RuntimeError("Docker isn't running. Start Docker Desktop and wait for 'Engine running'.")

            t = time.time(); self._step("build", "running")
            self.say(f"$ docker build --platform linux/amd64 -t {IMAGE} .")
            env = {**os.environ, "BUILDKIT_PROGRESS": "plain"}
            p = subprocess.Popen([docker, "build", "--platform", "linux/amd64", "-t", IMAGE, str(ROOT)],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                 errors="replace", env=env)
            for line in p.stdout:
                self.say(line)
            if p.wait() != 0:
                raise RuntimeError("The image did not build; see the log.")
            self._step("build", "done", time.time() - t)

            current = "prepare"
            t = time.time(); self._step("prepare", "running")
            shutil.rmtree(RUN, ignore_errors=True)
            uni, out = RUN / "universe", RUN / "output"
            uni.mkdir(parents=True); out.mkdir(parents=True)
            os.chmod(out, 0o777)  # the container writes as user 10001
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "input.py"), str(ROOT / "data" / "practice.csv"),
                                str(uni / "universe.csv")], capture_output=True, text=True, check=True)
            self.say(r.stdout)
            shutil.copy(ROOT / "data" / "lexicon.json", uni / "lexicon.json")
            if with_sample and (ROOT / "sample" / "sample.csv").exists():
                with open(ROOT / "sample" / "sample.csv", encoding="utf-8-sig", newline="") as f, \
                        open(uni / "universe.csv", "a", encoding="utf-8", newline="") as g:
                    w, n = csv.writer(g), 0
                    for row in csv.DictReader(f):
                        w.writerow([row["id"], row["text"], row["date"], ""]); n += 1
                self.say(f"added {n} sample rows (sample/sample.csv)")
            self._step("prepare", "done", time.time() - t)

            current = "run"
            t = time.time(); self._step("run", "running")
            name = f"polygraph-live-{int(t)}"
            deadline = int(t) + 1800
            cmd = [docker, "run", "-d", "--name", name, "--platform", "linux/amd64", "--network", "none", "--read-only",
                   "--user", "10001:10001", "--cpus", "2", "--memory", "6g", "--memory-swap", "6g", "--pids-limit", "256",
                   "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,size=128m,mode=1777",
                   "--mount", f"type=bind,source={uni},target=/universe,readonly",
                   "--mount", f"type=bind,source={out},target=/output",
                   "-e", f"ARENA_DEADLINE={deadline}", IMAGE]
            self.say("$ docker run --network none --read-only --user 10001 --cpus 2 --memory 6g ... " + IMAGE)
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            seen = 0
            try:
                while True:
                    state = subprocess.run([docker, "inspect", "-f", "{{.State.Running}}", name], capture_output=True, text=True)
                    logs = subprocess.run([docker, "logs", name], capture_output=True, text=True, encoding="utf-8", errors="replace")
                    lines = (logs.stdout + logs.stderr).splitlines()
                    for line in lines[seen:]:
                        self.say("  | " + line)
                    seen = len(lines)
                    mem = subprocess.run([docker, "stats", "--no-stream", "--format", "{{.MemUsage}}", name],
                                         capture_output=True, text=True).stdout
                    self.peak_mb = max(self.peak_mb, _mib(mem))
                    if state.stdout.strip() != "true":
                        break
                    if time.time() > deadline:
                        self.say("deadline: stopping the container")
                        subprocess.run([docker, "stop", "-t", "10", name], capture_output=True)
                        break
                    time.sleep(1.5)
                code = subprocess.run([docker, "inspect", "-f", "{{.State.ExitCode}} {{.State.OOMKilled}}", name],
                                      capture_output=True, text=True).stdout.split()
            finally:
                subprocess.run([docker, "rm", "-f", name], capture_output=True)
            run_seconds = time.time() - t
            self.say(f"exit code {code[0]}, out of memory: {code[1]}, peak memory {self.peak_mb:.0f} MiB")
            if code[0] != "0":
                raise RuntimeError(f"The container exited with code {code[0]}.")
            if not (out / "output.csv").exists():
                raise RuntimeError("The container wrote no /output/output.csv.")
            self._step("run", "done", run_seconds)

            current = "check"
            t = time.time(); self._step("check", "running")
            chk = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_output.py"), str(out),
                                  str(ROOT / "data" / "practice.csv"), str(uni / "universe.csv")],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in chk.stdout.splitlines():
                self.say("checker: " + line)
            self.result = _score(uni / "universe.csv", out / "output.csv", chk.stdout, chk.returncode == 0,
                                 run_seconds, self.peak_mb, with_sample)
            (RUN / "result.json").write_text(json.dumps(self.result), encoding="utf-8")
            self._step("check", "done", time.time() - t)
            self.state = "done"
        except Exception as e:  # noqa: BLE001 - every failure is shown to the user
            self._step(current, "failed")
            self.error = str(e) if not isinstance(e, subprocess.CalledProcessError) else (e.stderr or str(e))
            self.say("ERROR: " + str(self.error))
            self.state = "failed"


def _mib(usage: str) -> float:
    m = re.match(r"\s*([\d.]+)\s*(KiB|MiB|GiB|B)", usage or "")
    if not m:
        return 0.0
    v, u = float(m.group(1)), m.group(2)
    return v / 1024 if u == "KiB" else v * 1024 if u == "GiB" else v / 1048576 if u == "B" else v


def _score(universe: Path, output: Path, checker: str, passed: bool, seconds: float, peak: float, sample: bool) -> dict:
    """What the run handed in, and how its labels compare with the hidden practice labels."""
    with open(ROOT / "data" / "practice.csv", encoding="utf-8-sig", newline="") as f:
        truth = {r["id"]: r["label"] for r in csv.DictReader(f)}
    with open(universe, encoding="utf-8-sig", newline="") as f:
        uni = {r["id"]: r for r in csv.DictReader(f)}
    hidden = [rid for rid, r in uni.items() if not r["label"]]
    with open(output, encoding="utf-8-sig", newline="") as f:
        out = list(csv.DictReader(f))
    labels = {r["id"]: r for r in out if not r["type"]}
    claims = [r for r in out if r["type"]]
    rows, cm = [], Counter()
    for rid in hidden:
        o = labels.get(rid, {})
        ours, t = (o.get("label") or "unsure"), truth.get(rid)
        if t:
            cm[(t, ours)] += 1
        rows.append({"id": rid, "text": uni[rid]["text"], "date": uni[rid]["date"], "label": ours,
                     "confidence": o.get("confidence") or None, "truth": t, "sample": t is None})
    scored = [r for r in rows if r["truth"]]
    right = sum(r["label"] == r["truth"] for r in scored)
    lies = sum(1 for r in scored if r["truth"] == "false")
    return {
        "finished": time.strftime("%H:%M:%S"), "passed": passed, "checker": checker.strip(),
        "seconds": round(seconds, 1), "peak_mb": round(peak), "with_sample": sample,
        "labels_written": len(labels), "hidden": len(hidden), "scored": len(scored), "right": right,
        "accuracy": round(right / len(scored), 4) if scored else None,
        "all_true_baseline": round(sum(r["truth"] == "true" for r in scored) / len(scored), 4) if scored else None,
        "lies": lies, "lies_caught": cm[("false", "false")], "true_flagged": cm[("true", "false")],
        "verdicts": dict(Counter(r["label"] for r in rows)),
        "claims_count": len(claims), "claim_types": dict(Counter(c["type"] for c in claims)),
        "rows": rows,
        "claims": [{"id": c["id"], "type": c["type"], "text": c["text"], "confidence": c["confidence"]} for c in claims],
    }


JOB = Job()
