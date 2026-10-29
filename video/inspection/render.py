"""Render "The Inspection" (docs/PITCH_PAPERS.md).

    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py                 the full film, 1920x1080
    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py --preview       960x540, quicker
    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py --from 1:16 --to 1:40
    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py --still 1:30 --still 2:15

Frames are drawn at 480x270 and scaled with nearest-neighbour (pixel art).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import imageio_ffmpeg  # noqa: E402
from PIL import Image  # noqa: E402

import sound  # noqa: E402
from story import ARRANGEMENT, CUES, END_CHORD, FPS, TOTAL, frame  # noqa: E402

OUT = HERE / "out"
HD = (1920, 1080)


def secs(s: str) -> float:
    if ":" in s:
        m, x = s.split(":")
        return int(m) * 60 + float(x)
    return float(s)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="start", default="0")
    p.add_argument("--to", dest="end", default=str(TOTAL))
    p.add_argument("--preview", action="store_true", help="960x540, faster")
    p.add_argument("--still", action="append", default=[], help="write one frame as PNG (m:ss)")
    p.add_argument("--out", default=str(HERE / "inspection.mp4"))
    a = p.parse_args()
    OUT.mkdir(exist_ok=True)
    size = (960, 540) if a.preview else HD

    if a.still:
        for s in a.still:
            path = OUT / f"still_{s.replace(':', '-')}.png"
            frame(secs(s)).resize(size, Image.NEAREST).save(path)
            print(path)
        return 0

    start, end = secs(a.start), min(TOTAL, secs(a.end))
    wav = OUT / "audio.wav"
    t0 = time.time()
    sound.write_wav(wav, sound.mix(CUES, TOTAL, ARRANGEMENT, END_CHORD))
    print(f"audio: {time.time() - t0:.1f} s")

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "-",
           "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast" if a.preview else "medium",
           "-crf", "20" if a.preview else "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", a.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = round((end - start) * FPS)
    t0 = time.time()
    for i in range(n):
        t = start + i / FPS
        proc.stdin.write(frame(t).resize(size, Image.NEAREST).tobytes())
        if i % 300 == 0:
            print(f"  {t:6.1f} s  ({time.time() - t0:.0f} s elapsed)", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"wrote {a.out} in {time.time() - t0:.0f} s")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
