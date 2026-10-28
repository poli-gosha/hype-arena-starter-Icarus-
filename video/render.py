"""Render the explainer at 1080p and join the scenes into one MP4.

    .venv/Scripts/python.exe render.py                     # -> polygraph_explainer.mp4
    .venv/Scripts/python.exe render.py --music track.mp3   # also mix in music, faded out at the end
    .venv/Scripts/python.exe render.py --preview           # quick 480p version
"""
import argparse
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
SCENES = ["S01Court", "S02Case", "S03IntoBrain", "S04Dissect", "S05Truth", "S06Verdict", "S07Shapes", "S08Judge",
          "S09Forge", "S10Numbers", "S11Finale"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--music", help="an audio file to lay under the video")
    p.add_argument("--preview", action="store_true")
    a = p.parse_args()
    if a.preview:
        flags, folder, out = ["-ql"], "480p15", "polygraph_preview.mp4"
    else:
        flags, folder, out = ["-r", "1920,1080", "--fps", "30"], "1080p30", "polygraph_explainer.mp4"
    for s in SCENES:
        print(f"rendering {s} ...", flush=True)
        subprocess.run([sys.executable, "-m", "manim", *flags, "--disable_caching", "polygraph.py", s],
                       cwd=HERE, check=True, stdout=subprocess.DEVNULL)
    parts = [HERE / "media" / "videos" / "polygraph" / folder / f"{s}.mp4" for s in SCENES]
    listing = HERE / "media" / "concat.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    joined = HERE / ("_joined.mp4" if a.music else out)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(joined)], check=True)
    if a.music:
        dur = float(subprocess.run([ffmpeg, "-i", str(joined)], capture_output=True, text=True).stderr
                    .split("Duration: ")[1].split(",")[0].split(":")[-1]) + 60 * int(
            subprocess.run([ffmpeg, "-i", str(joined)], capture_output=True, text=True).stderr
            .split("Duration: ")[1].split(",")[0].split(":")[1])
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(joined), "-i", a.music, "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-af", f"afade=t=in:d=1.5,afade=t=out:st={dur - 4:.1f}:d=4,volume=0.8",
                        "-shortest", str(HERE / out)], check=True)
        joined.unlink()
    print(f"wrote {HERE / out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
