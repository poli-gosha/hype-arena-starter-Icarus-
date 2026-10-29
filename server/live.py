"""The live run: build our Docker image and run it exactly as the judges' check does.

Steps, in a background thread:
  1. build    docker build --platform linux/amd64 (the Dockerfile at the repo root)
  2. prepare  the input like scripts/check.sh: the 1,897 practice rows with every 5th label
              hidden (scripts/input.py), the lexicon, and optionally the 20 sample rows
  3. run      docker run offline, read-only, user 10001, 2 CPUs, 6 GiB, 30-minute deadline;
              its log lines and peak memory are tracked while it runs
  4. check    the organisers' own checker (scripts/check_output.py), then our labels on the
              hidden rows scored against the practice labels

The container's real /output/output.csv is kept for download, and the container itself is
kept (stopped) until the next run, so anyone can check it in Docker Desktop or with
`docker ps -a --filter name=polygraph-live`. Its settings are read back from Docker.
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
         ("run", "Run the container"), ("trace", "Trace every sentence"), ("check", "Check the output")]


# the organisers published it at datasets/sample.csv (their README said sample/sample.csv)
SAMPLE = next((p for p in (ROOT / "datasets" / "sample.csv", ROOT / "sample" / "sample.csv") if p.exists()),
              ROOT / "datasets" / "sample.csv")
STANDIN = ROOT / "data" / "sample_standin.csv"


def sample_file() -> Path:
    """The organisers' 20 sample rows once they are published (09:00, 29 Oct), else our own
    stand-in of 20 sentences written in the same style."""
    return SAMPLE if SAMPLE.exists() else STANDIN


def docker_exe() -> str | None:
    for c in (shutil.which("docker"), r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"):
        if c and Path(c).exists():
            return c
    return None


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()
        self.trace = {}
        if (RUN / "trace.json").exists():
            try:
                self.trace = json.loads((RUN / "trace.json").read_text(encoding="utf-8"))
            except ValueError:
                pass
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
        self.trace = {}
        self.trace_error = None
        self.started = None
        self.peak_mb = 0.0
        self.container = None
        self.image = None

    def say(self, line: str):
        line = line.rstrip()
        if line:
            self.log.append(line)
            del self.log[:-400]

    def status(self) -> dict:
        return {"state": self.state, "steps": self.steps, "log": self.log[-60:], "error": self.error,
                "elapsed": round(time.time() - self.started, 1) if self.started and self.state == "running" else None,
                "peak_mb": round(self.peak_mb), "has_result": self.result is not None,
                "container": self.container, "image": self.image,
                "docker": docker_exe() is not None, "sample_available": True, "sample_real": SAMPLE.exists()}

    def start(self, with_sample: bool) -> bool:
        with self.lock:
            if self.state == "running":
                return False
            self.reset()
            self.state, self.started = "running", time.time()
        threading.Thread(target=self._run, args=(with_sample,), daemon=True).start()
        return True

    def _trace(self, uni: Path):
        t = time.time()
        self._step("trace", "running")
        try:
            self.trace = _trace_run(self, uni)
            (RUN / "trace.json").write_text(json.dumps(self.trace), encoding="utf-8")
            self._step("trace", "done", time.time() - t)
        except Exception as e:  # noqa: BLE001 - the Docker run stands on its own; the trace is extra
            self.trace_error = str(e)
            self.say("trace failed: " + str(e))
            self._step("trace", "failed")

    # ---- the steps -------------------------------------------------------------------------
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
            img = subprocess.run([docker, "image", "inspect", IMAGE, "--format", "{{.Id}}|{{.Created}}|{{.Size}}"],
                                 capture_output=True, text=True).stdout.strip().split("|")
            self.image = {"name": IMAGE, "id": img[0], "created": img[1][:19].replace("T", " ") if len(img) > 1 else "",
                          "size_mb": round(int(img[2]) / 1e6) if len(img) > 2 and img[2].isdigit() else None}
            self.say(f"image {IMAGE}: {img[0][:19]}")
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
            if with_sample:
                src = sample_file()
                with open(src, encoding="utf-8-sig", newline="") as f, \
                        open(uni / "universe.csv", "a", encoding="utf-8", newline="") as g:
                    w, n = csv.writer(g), 0
                    for row in csv.DictReader(f):
                        w.writerow([row["id"], row["text"], row["date"], ""]); n += 1
                self.say(f"added {n} sample rows ({src.relative_to(ROOT).as_posix()})")
            self._step("prepare", "done", time.time() - t)
            # while the container runs, the same code runs here on the same input and records
            # what every stage computed for each sentence it labels
            tracer = threading.Thread(target=self._trace, args=(uni,), daemon=True)
            tracer.start()

            current = "run"
            t = time.time(); self._step("run", "running")
            name = f"polygraph-live-{int(t)}"
            old = subprocess.run([docker, "ps", "-aq", "--filter", "name=polygraph-live-"], capture_output=True, text=True).stdout.split()
            if old:  # only the latest run's container is kept
                subprocess.run([docker, "rm", "-f", *old], capture_output=True)
            deadline = int(t) + 1800
            cmd = [docker, "run", "-d", "--name", name, "--platform", "linux/amd64", "--network", "none", "--read-only",
                   "--user", "10001:10001", "--cpus", "2", "--memory", "6g", "--memory-swap", "6g", "--pids-limit", "256",
                   "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,size=128m,mode=1777",
                   "--mount", f"type=bind,source={uni},target=/universe,readonly",
                   "--mount", f"type=bind,source={out},target=/output",
                   "-e", f"ARENA_DEADLINE={deadline}", IMAGE]
            self.say("$ docker run --network none --read-only --user 10001 --cpus 2 --memory 6g ... " + IMAGE)
            cid = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
            self.container = {"name": name, "id": cid}
            self.say(f"container {name}: {cid[:12]}")
            # what Docker itself says this container runs with
            fmt = ("{{.Config.User}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{.HostConfig.NanoCpus}}|"
                   "{{.HostConfig.Memory}}|{{.HostConfig.PidsLimit}}|{{.Config.Image}}|{{.Image}}")
            f = subprocess.run([docker, "inspect", "-f", fmt, name], capture_output=True, text=True).stdout.strip().split("|")
            settings = {"user": f[0], "network": f[1], "read_only": f[2] == "true",
                        "cpus": round(int(f[3]) / 1e9, 2) if f[3].isdigit() else f[3],
                        "memory_gb": round(int(f[4]) / 1024 ** 3, 2) if f[4].isdigit() else f[4],
                        "pids_limit": f[5], "image_name": f[6], "image_id": f[7]}
            self.container["settings"] = settings
            self.say("docker inspect: user {user}, network {network}, read-only {read_only}, cpus {cpus}, "
                     "memory {memory_gb} GiB, pids {pids_limit}".format(**settings))
            seen = 0
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
            run_seconds = time.time() - t
            self.container["exit_code"] = int(code[0]) if code and code[0].lstrip("-").isdigit() else code[0]
            self.say(f"the container is kept: docker ps -a --filter name={name}")
            self.say(f"exit code {code[0]}, out of memory: {code[1]}, peak memory {self.peak_mb:.0f} MiB")
            if code[0] != "0":
                raise RuntimeError(f"The container exited with code {code[0]}.")
            if not (out / "output.csv").exists():
                raise RuntimeError("The container wrote no /output/output.csv.")
            self._step("run", "done", run_seconds)

            tracer.join()
            current = "check"
            t = time.time(); self._step("check", "running")
            chk = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_output.py"), str(out),
                                  str(ROOT / "data" / "practice.csv"), str(uni / "universe.csv")],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in chk.stdout.splitlines():
                self.say("checker: " + line)
            self.result = _score(uni / "universe.csv", out / "output.csv", chk.stdout, chk.returncode == 0,
                                 run_seconds, self.peak_mb, with_sample)
            self.result["proof"] = {"image": self.image, "container": self.container}
            docker_labels = {r["id"]: r["label"] for r in self.result["rows"]}
            traced = {rid: t["verdict"]["label"] for rid, t in self.trace.items() if "verdict" in t}
            same = sum(docker_labels.get(rid) == lab for rid, lab in traced.items())
            self.result["trace"] = {"traced": len(traced), "same_label": same, "error": self.trace_error}
            for r in self.result["rows"]:
                r["traced"] = r["id"] in traced
            self.say(f"trace: {len(traced)} sentences traced, {same} with the same label as the container")
            (RUN / "result.json").write_text(json.dumps(self.result), encoding="utf-8")
            self._step("check", "done", time.time() - t)
            self.state = "done"
        except Exception as e:  # noqa: BLE001 - every failure is shown to the user
            self._step(current, "failed")
            self.error = str(e) if not isinstance(e, subprocess.CalledProcessError) else (e.stderr or str(e))
            self.say("ERROR: " + str(self.error))
            self.state = "failed"


def _trace_run(job: "Job", uni: Path):
    """The in-process trace (see Job._trace)."""
    from polygraph import explain, pipeline
    rows, lexicon = pipeline.load_universe(uni)
    bundle = pipeline.Bundle.load()
    with explain.LOCK:
        explain.start([r.id for r in rows if not r.label])
        try:
            pipeline.run(rows, lexicon, bundle, claims=False)
            return dict(explain.ROWS)
        finally:
            explain.stop()


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
