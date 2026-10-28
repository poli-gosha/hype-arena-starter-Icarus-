# The explainer video

`polygraph_explainer.mp4`: 3:02, 1080p30, QA DNA colours, text on screen. Add music with `--music`.

Made with [Manim](https://www.manim.community/) (the library behind 3Blue1Brown's videos), from `polygraph.py`:
eleven scenes, from the mouse judge's courtroom, through Exhibit A's journey along the seven stages, to the numbers.

```powershell
py -3.13 -m venv video\.venv
video\.venv\Scripts\python.exe -m pip install manim imageio-ffmpeg
cd video
.venv\Scripts\python.exe render.py                      # 1080p, about 10 minutes
.venv\Scripts\python.exe render.py --music track.mp3    # with music, faded out at the end
.venv\Scripts\python.exe -m manim -ql polygraph.py S05Truth   # preview one scene
.venv\Scripts\python.exe sheet.py                       # contact sheet of the previews
```

Fonts: Figtree (SIL Open Font License, `fonts/`), Segoe UI Symbol for Σ ≠ λ ✓.
The numbers on screen are the measured ones from `scripts/eval_labels.py`, `eval_claims.py` and `stress_windows.sh`.
