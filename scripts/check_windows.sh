#!/bin/sh
# Runs the organizers' scripts/check.sh from Git Bash on Windows.
#   sh scripts/check_windows.sh                  # build and run
#   MINUTES=10 sh scripts/check_windows.sh       # a shorter run
# Git Bash rewrites paths like /universe into Windows paths, which breaks Docker's volume
# mounts; Windows has no python3. This turns path rewriting off, gives check.sh Windows-style
# temp folders, and a python3 that translates POSIX paths for Windows Python.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
shim=$(mktemp -d)
cat > "$shim/python3" <<EOF
#!/bin/sh
args=""
for a in "\$@"; do
  case "\$a" in /*) a=\$(cygpath -m "\$a");; esac
  args="\$args \"\$a\""
done
py="$root/.venv/Scripts/python.exe"
[ -x "\$py" ] || py=python
eval exec "\$py" \$args
EOF
chmod +x "$shim/python3"
export PATH="$shim:/c/Program Files/Docker/Docker/resources/bin:$PATH"
tmp=$(cygpath -m "${TEMP:-/tmp}")
image=${1:-}
if [ -z "$image" ]; then  # build here: with path rewriting off, docker needs a Windows path
	image=hype-arena-check
	docker build --platform linux/amd64 -t "$image" "$(cygpath -m "$root")"
fi
MSYS_NO_PATHCONV=1 TMPDIR="$tmp" sh "$root/scripts/check.sh" "$image"
