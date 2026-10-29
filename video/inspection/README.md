# The Inspection: the pitch film

A 2:44 pixel-art film, in the organisers' four-part structure, of one statement going through Polygraph, desk by desk, as planned in
[`docs/PITCH_PAPERS.md`](../../docs/PITCH_PAPERS.md). Everything is drawn and synthesised in code
(Pillow, numpy, ffmpeg): no downloaded art, no samples, open fonts only (`../fonts/`).

| File | What |
|---|---|
| `art.py` | Palette, fonts, paper, stamps, seals, the booth, the desk and the cast (the Clerk, the applicants) |
| `story.py` | Every shot on the timeline, with its captions and sound cues; the case data |
| `sound.py` | The sound effects and the music, synthesised |
| `render.py` | Renders the film (and stills) and mixes the sound |

```powershell
video\.venv\Scripts\python.exe video\inspection\render.py                      # the film, 1080p, about 3 minutes
video\.venv\Scripts\python.exe video\inspection\render.py --preview            # 960x540, quicker
video\.venv\Scripts\python.exe video\inspection\render.py --still 1:31         # one frame as PNG, in out/
```

## Not in the film: the live run

The film shows the workflow drawn, not the frontend running. The challenge asks the 11:00 video to
show the frontend running live on the 20 sample rows beside its architecture diagram: cover that
with a separate screen recording of `/console.html` and `/inside.html`, or live at the pitch.
