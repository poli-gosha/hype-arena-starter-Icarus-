"""Contact sheet of the preview renders: N frames per scene, plus the total run time."""
import sys
from pathlib import Path

import av
from PIL import Image, ImageDraw

SCENES = ["S01Court", "S02Case", "S03IntoBrain", "S04Dissect", "S05Truth", "S06Verdict", "S07Shapes", "S08Judge",
          "S09Forge", "S10Numbers", "S11Finale"]
quality = sys.argv[1] if len(sys.argv) > 1 else "480p15"
only = sys.argv[2:] or SCENES
per = 6
W, H = 320, 180
total = 0.0
sheet = Image.new("RGB", (W * per, H * len(only)), "black")
for row, s in enumerate(only):
    path = Path("media/videos/polygraph") / quality / f"{s}.mp4"
    c = av.open(str(path))
    st = c.streams.video[0]
    dur = float(st.duration * st.time_base)
    total += dur
    times = [dur * (i + 0.5) / per for i in range(per)]
    frames, ti = [], 0
    for f in c.decode(st):
        if ti < len(times) and f.time >= times[ti]:
            frames.append(f.to_image().resize((W, H)))
            ti += 1
    c.close()
    for i, im in enumerate(frames):
        sheet.paste(im, (i * W, row * H))
    ImageDraw.Draw(sheet).text((4, row * H + 2), f"{s} {dur:.1f}s", fill="yellow")
    print(f"{s:14s} {dur:6.1f}s")
print(f"TOTAL {total:.1f}s = {int(total // 60)}:{int(total % 60):02d}")
sheet.save("sheet.png")
