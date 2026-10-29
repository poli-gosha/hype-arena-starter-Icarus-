"""Render "The Inspection" (docs/PITCH_PAPERS.md).

    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py                 the full film, 1920x1080
    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py --preview       960x540, quicker
    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py --from 1:16 --to 1:40
    video\\.venv\\Scripts\\python.exe video\\inspection\\render.py --still 1:30 --still 2:15

Frames are drawn at 480x270 and scaled with nearest-neighbour (pixel art), except the live
insert (1:32-1:57): video/inspection/live.mp4, the screen recording of the real frontend, is
composed in full HD inside the booth's monitor. Until it exists, a placeholder card stands in.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import imageio_ffmpeg  # noqa: E402
from PIL import Image  # noqa: E402

import sound  # noqa: E402
from art import SCREEN, W, H, NIGHT, caption, ease  # noqa: E402
from story import (ARRANGEMENT, CUES, END_CHORD, FPS, LIVE, LIVE_CAPTION, TOTAL, chapter, frame,  # noqa: E402
                   placeholder, s14_monitor)

OUT = HERE / "out"
LIVE_FILE = HERE / "live.mp4"
HD = (1920, 1080)


def secs(s: str) -> float:
    if ":" in s:
        m, x = s.split(":")
        return int(m) * 60 + float(x)
    return float(s)


LIVE_START, LIVE_SPEED = 0.0, 1.0  # set by --live-start / --live-speed


class Live:
    """The screen recording, read frame by frame at 30 fps and fitted to 1920x1080: from
    --live-start seconds in, played --live-speed times faster."""

    def __init__(self, start: float):
        self.frames = None
        self.last = None
        if LIVE_FILE.exists():
            self.frames = imageio_ffmpeg.read_frames(
                str(LIVE_FILE), input_params=["-ss", f"{LIVE_START + max(0.0, start) * LIVE_SPEED:.3f}"],
                output_params=["-vf", f"setpts=PTS/{LIVE_SPEED},fps={FPS},"
                                      "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"])
            next(self.frames)  # the metadata

    def next(self) -> Image.Image:
        if self.frames is not None:
            try:
                self.last = Image.frombytes("RGB", HD, next(self.frames))
            except StopIteration:
                self.frames = None
        if self.last is None:
            return placeholder(0).resize(HD, Image.NEAREST)
        return self.last


def cap_layer(s: str, t: float, at: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    caption(layer, s, t)
    chapter(layer, at)
    return layer.resize(HD, Image.NEAREST)


def live_frame(u: float, live: Live) -> Image.Image:
    """1:32-1:57: the monitor flickers on, we push in, the real recording plays, we pull out."""
    dur = LIVE[1] - LIVE[0]
    src = live.next() if u >= 0.6 else None
    zoom = ease((u - 0.6) / 1.6) if u < dur - 1.2 else 1 - ease((u - (dur - 1.2)) / 1.0)
    if zoom >= 1:
        out = src.copy()
    else:
        booth = s14_monitor(u, None)
        sx0, sy0, sx1, sy1 = SCREEN
        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
        tw, th = (sx1 - sx0), (sx1 - sx0) * 9 / 16  # a 16:9 box around the glass
        box = [0 + (cx - tw / 2) * zoom, 0 + (cy - th / 2) * zoom,
               W + (cx + tw / 2 - W) * zoom, H + (cy + th / 2 - H) * zoom]
        out = booth.transform(HD, Image.EXTENT, tuple(box), Image.NEAREST)
        if src is not None:
            fx = lambda x: (x - box[0]) / (box[2] - box[0]) * HD[0]  # noqa: E731
            fy = lambda y: (y - box[1]) / (box[3] - box[1]) * HD[1]  # noqa: E731
            gx0, gy0, gx1, gy1 = round(fx(sx0)), round(fy(sy0)), round(fx(sx1)), round(fy(sy1))
            if gx1 - gx0 > 2 and gy1 - gy0 > 2:
                out.paste(src.resize((gx1 - gx0, gy1 - gy0), Image.BILINEAR), (gx0, gy0))
    if 2.2 <= u < dur - 1.2:
        layer = cap_layer(LIVE_CAPTION + (f"  (x{LIVE_SPEED:g} speed)" if LIVE_SPEED != 1 else ""), u - 2.2, LIVE[0] + u)
        out.paste(layer, (0, 0), layer)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="start", default="0")
    p.add_argument("--to", dest="end", default=str(TOTAL))
    p.add_argument("--preview", action="store_true", help="960x540, faster")
    p.add_argument("--still", action="append", default=[], help="write one frame as PNG (m:ss)")
    p.add_argument("--out", default=str(HERE / "inspection.mp4"))
    p.add_argument("--live-start", type=float, default=0.0, help="skip this many seconds of live.mp4")
    p.add_argument("--live-speed", type=float, default=1.0, help="play live.mp4 this many times faster")
    a = p.parse_args()
    global LIVE_START, LIVE_SPEED
    LIVE_START, LIVE_SPEED = a.live_start, a.live_speed
    OUT.mkdir(exist_ok=True)
    size = (960, 540) if a.preview else HD

    if a.still:
        for s in a.still:
            t = secs(s)
            if LIVE[0] <= t < LIVE[1]:
                img = live_frame(t - LIVE[0], Live(t - LIVE[0] - 0.6))
            else:
                img = frame(t).resize(size, Image.NEAREST)
            path = OUT / f"still_{s.replace(':', '-')}.png"
            img.resize(size, Image.NEAREST).save(path)
            print(path)
        return 0

    start, end = secs(a.start), min(TOTAL, secs(a.end))
    wav = OUT / "audio.wav"
    t0 = time.time()
    sound.write_wav(wav, sound.mix(CUES, TOTAL, ARRANGEMENT, END_CHORD))
    print(f"audio: {time.time() - t0:.1f} s")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    import subprocess
    cmd = [ffmpeg, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "-",
           "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast" if a.preview else "medium",
           "-crf", "20" if a.preview else "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", a.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    live = None
    n = round((end - start) * FPS)
    t0 = time.time()
    for i in range(n):
        t = start + i / FPS
        if LIVE[0] <= t < LIVE[1]:
            if live is None:
                live = Live(max(0.0, t - LIVE[0] - 0.6))
            img = live_frame(t - LIVE[0], live)
            if img.size != size:
                img = img.resize(size, Image.BILINEAR)
        else:
            img = frame(t).resize(size, Image.NEAREST)
        proc.stdin.write(img.tobytes())
        if i % 300 == 0:
            print(f"  {t:6.1f} s  ({time.time() - t0:.0f} s elapsed)", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"wrote {a.out} in {time.time() - t0:.0f} s")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
