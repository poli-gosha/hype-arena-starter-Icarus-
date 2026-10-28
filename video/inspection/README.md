# The Inspection: the pitch film

A 3:00 pixel-art film of one statement going through Polygraph, desk by desk, as planned in
[`docs/PITCH_PAPERS.md`](../../docs/PITCH_PAPERS.md). Everything is drawn and synthesised in code
(Pillow, numpy, ffmpeg): no downloaded art, no samples, open fonts only (`../fonts/`).

| File | What |
|---|---|
| `art.py` | Palette, fonts, paper, stamps, seals, the booth, the desk and the cast (the Clerk, the applicants) |
| `story.py` | Every shot on the timeline, with its captions and sound cues; the case data |
| `sound.py` | The sound effects and the music, synthesised |
| `render.py` | Renders the film (and stills) and mixes the sound |

```powershell
video\.venv\Scripts\python.exe video\inspection\render.py                      # the film, 1080p, about 5 minutes
video\.venv\Scripts\python.exe video\inspection\render.py --preview            # 960x540, quicker
video\.venv\Scripts\python.exe video\inspection\render.py --still 1:31         # one frame as PNG, in out/
```

## The live insert (2:22-2:50)

The film keeps 28 seconds for the real frontend running on the 20 sample rows. Until a recording
exists it shows a placeholder card.

1. At 09:00, put the organisers' file in `sample/sample.csv`, start the server, open
   `http://localhost:8000/console.html`, keep the sample ticked and press **Build and run in Docker**.
2. Record the screen (`Win+Alt+R`, or OBS): the button, Docker Desktop showing the container, the
   results, then `/inside.html` scrolling one or two sample sentences through the pipeline.
3. Save the recording as `video/inspection/live.mp4` and render again. If it is longer than 28 s,
   skip its start and speed it up; the caption then says so:

```powershell
video\.venv\Scripts\python.exe video\inspection\render.py --live-start 5 --live-speed 4
```
