#!/bin/sh
# The 20,000-row test: runs the Docker image on a universe ~10x the practice data, with the
# judges' exact limits (offline, 2 CPUs, 6 GiB, read-only, user 10001, 30-minute deadline).
#   sh scripts/stress_windows.sh                  # build the image, then run
#   sh scripts/stress_windows.sh hype-arena-check # reuse an image built by check_windows.sh
# The universe is the practice rows (labelled) plus 9 unlabelled copies with fresh ids, so
# it has the real run's shape: ~19,000 rows, ~90% of them unlabelled. Works on Mac/Linux too.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
winpath() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else echo "$1"; fi; }
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
py="$root/.venv/Scripts/python.exe"; [ -x "$py" ] || py="$root/.venv/bin/python"; [ -x "$py" ] || py=python3

image=${1:-}
if [ -z "$image" ]; then
	image=hype-arena-check
	docker build --platform linux/amd64 -t "$image" "$(winpath "$root")"
fi

uni="$root/out/stress"
outd="$root/out/stress_out"
rm -rf "$uni" "$outd"
mkdir -p "$uni" "$outd"
chmod 777 "$outd"
"$py" - "$(winpath "$root")" "$(winpath "$uni")" <<'EOF'
import csv, shutil, sys
root, uni = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(f"{root}/data/practice.csv", encoding="utf-8")))
with open(f"{uni}/universe.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "text", "date", "label"])
    for r in rows:
        w.writerow([r["id"], r["text"], r["date"], r["label"]])
    for c in range(1, 10):
        for r in rows:
            w.writerow([f"{r['id']}-c{c}", r["text"], r["date"], ""])
shutil.copy(f"{root}/data/lexicon.json", f"{uni}/lexicon.json")
print(f"universe: {len(rows) * 10} rows, {len(rows) * 9} unlabelled")
EOF

start=$(date +%s)
name=hype-arena-stress-$$
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
# detached, like the organizers' check.sh: an attached run can be cut off under Git Bash
MSYS_NO_PATHCONV=1 docker run -d --name "$name" --platform linux/amd64 --network none --read-only --user 10001:10001 \
	--cpus 2 --memory 6g --memory-swap 6g --pids-limit 256 --cap-drop ALL --security-opt no-new-privileges \
	--tmpfs /tmp:rw,size=128m,mode=1777 \
	-v "$(winpath "$uni"):/universe:ro" -v "$(winpath "$outd"):/output" \
	-e ARENA_DEADLINE=$((start + 1800)) "$image" >/dev/null
echo "running on the 20,000-row universe (judges' limits); this takes about 4 minutes"
peak=0
while [ "$(docker inspect -f '{{.State.Running}}' "$name")" = true ]; do
	if [ $(( $(date +%s) - start )) -ge 1800 ]; then echo "deadline: stopping"; docker stop -t 10 "$name" >/dev/null; break; fi
	mib=$(docker stats --no-stream --format '{{.MemUsage}}' "$name" 2>/dev/null | awk '{v=$1; if (v ~ /GiB/) {sub(/GiB/,"",v); v=v*1024} else {sub(/MiB/,"",v)}; printf "%d", v}')
	[ -n "$mib" ] && [ "$mib" -gt "$peak" ] && peak=$mib
	sleep 5
done
took=$(( $(date +%s) - start ))
docker logs "$name" 2>&1 | tail -10 | sed 's/^/  | /'
code=$(docker inspect -f '{{.State.ExitCode}}' "$name"); oom=$(docker inspect -f '{{.State.OOMKilled}}' "$name")
lines=0; [ -f "$outd/output.csv" ] && lines=$(($(wc -l < "$outd/output.csv") - 1))
echo "exit code $code, out of memory: $oom, peak memory ${peak} MiB of 6144, took ${took}s of 1800"
echo "output.csv: ${lines} rows (expected 18073: 17,073 labels + 1,000 claims)"
if [ "$code" = 0 ] && [ "$oom" = false ] && [ "$lines" = 18073 ]; then echo "STRESS TEST PASSED"; else echo "STRESS TEST FAILED"; exit 1; fi
