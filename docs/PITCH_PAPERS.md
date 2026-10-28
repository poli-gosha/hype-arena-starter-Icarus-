# The pitch video: "The Inspection" (a document-checkpoint story)

A 3-minute pixel-art film about one tiny clerk inspecting statements about Hooly at a checkpoint
desk. Every desk, tool and document is one stage of Polygraph, in the order the code runs. Every
number on screen is real: what the system actually computed. The closing minute shows the real
frontend running live on the 20 sample rows, as the rules require.

Part 1 is the creative bible: theme, look, cast, and how the desk maps to the code. Part 2 is the
case file with the real data. Part 3 is the shot list. Part 4 is the prompt to build it. Part 5 is
tomorrow's timeline.

---

## Part 1 · The bible

### The idea in one line
**Truth depends on the date.** The same sentence, "Hooly Pixel 10 costs €799", is certified true
on 28 April 2026 and a lie on 5 October 2026. Our clerk doesn't guess; it goes to the archive and
checks the timeline.

### Theme
A bureaucratic document-inspection desk in the style of 1980s indie pixel-art games: a cramped
booth, a window where people slide papers through, a rulebook, a registry, stamps that land with a
thud, and an archive behind the desk. The mood is dry, slightly dystopian and funny: a ministry
that inspects hype.

**Inspired by the genre, never copied.** Everything is ours: the world (the *Ministry of
Statements*, Hooly), the characters, the documents, the UI, the music. Do not use the name, places,
slogans, characters, sprites, fonts, music or exact screen layout of any existing game.

### Look
| | |
|---|---|
| Resolution | Drawn at **480×270**, scaled ×4 with nearest-neighbour to **1920×1080**. Hard pixel edges, no blur, no anti-aliasing. |
| Motion | Props and characters animate in steps at **12 fps** (pixel-game feel); slides, pans and the timeline line move smoothly at 30 fps. |
| Palette | Muted and dusty, with four signal colours only. |
| Light | One desk lamp. The archive is darker and bluer, lit by a hand lamp. |
| Text | Pixel fonts only, at native sizes (8 or 16 px before scaling) so they stay crisp. |

Palette (hex):

| Role | Colour |
|---|---|
| Night / deep shadow | `#141518` |
| Booth wall | `#2B2D2A` |
| Desk wood | `#4A3F35`, highlight `#5E5043` |
| Paper | `#E8E0C9`, shade `#C9BFA3` |
| Ink, text | `#2A2622` |
| Archive blue-grey | `#4C5A63` |
| **Stamp red** (false) | `#B8322F` |
| **Seal green** (true, certified) | `#4F8A3C` |
| **Amber** (unsure) | `#C9932F` |
| **Lime highlighter** (our trace) | `#D7F13B` |

The **lime highlighter** is the bridge to our website: on the site a lime line traces the pipeline
as you scroll; in the film the clerk draws the same lime line, across the paper and then along the
archive's timeline. Use lime for nothing else.

Fonts (Google Fonts, open licence, bundled in `video/fonts/`):
- **Silkscreen**: signs, stamps, station titles (capitals).
- **VT323**: typewritten documents, the ledger, the shift report.
- **Pixelify Sans**: on-screen captions.
- Check each font has `€`; if not, draw the glyph as a sprite.

### Sound
No voice: text on screen, like our first video. Music is a slow, dry, low-tempo loop (bass,
typewriter-like percussion, a lonely melody), royalty-free or synthesised. Sound effects drive the
rhythm: paper slide, pencil scratch, drawer, footsteps in the archive, a pin pushed into cork, the
polygraph needle's tick, a heavy **stamp thud**, typewriter keys and a bell, the shutter of the
window. Synthesise them, or use only sounds released as CC0.

### Cast
- **The Clerk**: a small grey mouse in a green visor and round reading glasses, on a tall stool. Our
  human touch: it sighs, pushes up its glasses, licks a finger to turn pages, and nods once at a
  good stamp. It is the system: it never guesses, it checks.
- **The applicants**: Hooly's people sliding statements through the window. A **salesman** in a
  shiny suit with a phone for the main case. **Gavin Bellson**, Hooly's CEO (the dataset's own
  character), big grin, for the invented lie. A **launch-event host** with a lanyard for the
  premature lie.
- **The archive**: tall shelves of files, one per month, from October 2025 to October 2026.

### The desk is the architecture
Each step happens at its own place on the desk, in the order of `polygraph/pipeline.py`. A small
tab names the step and the module, so the jury sees the machine without a diagram.

| Step | In the code | On the desk | Prop |
|---|---|---|---|
| 1 | **Input**: the row and its page | The applicant slides the statement through; its **dossier**, the page it came from, is clipped behind it | Paper slip, paper clip |
| 2 | **Linker**: who it is about (lexicon) | The clerk checks the **Registry of Hooly**, the official list of every name and alias | Registry book, blue pencil underline |
| 3 | **Reader**: which values (value-forms rules) | The clerk reads each value by the **Rulebook**, the organisers' published rules for money, dates, counts | Rulebook, red pencil circle, a note in the margin |
| 4 | **Attributor**: which fact (trained model) | A **filing cabinet**: one drawer per candidate fact, each lit with its probability; the right drawer slides open | Cabinet, drawer labels with % |
| 5 | **Knowledge base**: correction | A glance at the **ledger** of what is already on file: if the drawer were wrong, the ledger would correct it | Ledger, a tick |
| 6 | **Truth engine**: the timeline | The clerk walks into the **archive**, pulls every document about this fact and pins them on a corkboard timeline; certified ones carry seals; the lime line traces the steps | Lamp, cork, pins, wax seals, lime string |
| 7 | **Judge**: 64 numbers, decision trees | The **polygraph** needle swings against the 60% line, then the **stamp** | Needle gauge, stamp |
| 8 | **Writer**: output.csv | The verdict is typed into the **ledger** and the slip goes into the outbox | Typewriter, outbox tray |
| after hours | **Claim forge**: 1,000 new true claims | Off duty, the clerk writes new certified statements, only from sealed records, each checked against the Rulebook before the seal | Certificate pad, "CERTIFIED TRUE" seal |

The three kinds of lies get their own stamps, one per thing the archive can show:
- **INVENTED**: no document ever had this value.
- **STALE**: it was true, but not any more on this date.
- **PREMATURE**: it only became true later.
- **TRUE** is a green seal; **UNSURE** is an amber stamp: "the archive can't tell".

---

## Part 2 · The case file (real data; use these numbers exactly)

### The main case: a stale price
From our live run on the 20 stand-in sample rows (`out/live/trace.json`, row `s-7`).

| | |
|---|---|
| Statement | **"The Hooly Pixel 10 costs €799."** · page dated **5 Oct 2026** |
| Linker | **Hooly Pixel 10** |
| Reader | **"€799"** → money · 799 · EUR |
| Attributor | **52** candidate facts scored; **Hooly Pixel 10 · price 99.3%**; Hooly Pixel 10 Pro · price 0.06%; Hooly Pixel 9 · price 0.06% |
| Knowledge base | No correction needed |
| Truth engine | **11** documents about Hooly Pixel 10 · price; **8** certified true, **1** certified false. Timeline: **€799 from 28 Apr 2026**, **€749 from 2 Sep 2026** |
| Status | **STALE**: €799 was true before 5 Oct, not on it |
| Judge | P(false) **98.2%** > 60% cutoff → **FALSE**, **98%** sure |
| Writer | `s-7,,,,false,0.982` |

Real documents from the archive (practice data) to pin on the board:
- 28 Apr 2026 · certified true · "Hooly Pixel 10 costs €799" (`p-370`)
- 28 Apr 2026 · certified true · "Hooly Pixel 10 is €799 today and ships on 14 May 2026." (`p-384`)
- 14 May 2026 · certified true · "Hooly Pixel 10 costs €799, and Hooly Pixel 10 Pro costs €1,099." (`p-1255`)
- 2 Sep 2026 · certified true · "Hooly Pixel 10: €749, with 256 GB of storage." (`p-1859`)
- 8 Oct 2026 · certified true · "Hooly Pixel 10 costs €749, and he calls it the best phone Hooly has made." (`p-946`)
- 28 Apr 2026 · certified false · "Hooly Pixel 10 goes on sale on 12 August 2025 for €799." (`p-1245`)

The key frame: the applicant's slip "The Hooly Pixel 10 costs €799." next to the archive's
"Hooly Pixel 10 costs €799", sealed true on 28 April. **Same sentence. True in April. False in
October.**

### The lie montage (all caught correctly by the system, against the hidden practice labels)
| Stamp | Applicant | Statement | Date | What the archive holds | System |
|---|---|---|---|---|---|
| INVENTED | Gavin Bellson | "Gavin: Gemini speaks 40 languages, which is more than any competitor." (`p-871`) | 10 Jun 2026 | 12 languages | FALSE, 96% |
| PREMATURE | Launch host | "Hooly Pixel 10 Pro arrives the same day at €1,049." (`p-1246`) | 28 Apr 2026 | €1,099 on that day; €1,049 only later | FALSE, 93% |
| TRUE | Salesman | "Hooly Photos Max now gives you 10 TB of storage." (stand-in `s-1`) | 14 Jun 2026 | 10 TB since 7 May 2026 | TRUE, 98% |

### After hours: real claims the forge wrote
- "Hooly Pixel 10 Pro costs €1,049." *(the premature lie of April is today's truth)*
- "Hooly Pixel 10 cost €799 at Made by Hooly 2026." *(the €799, honestly placed in time)*
- "The price of Hooly Pixel 9 went from €699 to €549."
- "The refresh rate of Hooly Pixel 10 is 120 Hz."

### The shift report (measured; keep the wording honest)
- About **19,000** statements in a test the size of the judges' run: **200 s** of the 30 minutes allowed, **0.8 GB** of the 6 GB.
- Labels right on held-out practice rows: **88%** (answering "true" to everything scores 83%).
- **1,000** new claims: **992** true when checked against every labelled fact.
- Traced in the frontend and run in Docker: **400 of 400** labels identical.
- LLMs at run time: **0**. Network: **none**.

---

## Part 3 · The shot list (3:00)

On-screen captions are in quotes. SFX in brackets.

### Act I · The booth (0:00–0:25)
| Time | Shot | Captions and sound |
|---|---|---|
| 0:00–0:07 | Black. Typewriter text, letter by letter. | "HOOLY. ONE YEAR. 20,000 STATEMENTS." then "SOME OF THEM LIE." [keys, bell, stamp thud on "LIE"] |
| 0:07–0:15 | Fade up: the booth at dusk. Sign over the window: **MINISTRY OF STATEMENTS · POLYGRAPH DESK**. The Clerk adjusts its visor. A notice pinned to the wall. | Notice: "NO GUESSING. NO LLMs. NO INTERNET. 30 MINUTES." [music starts, lamp hum] |
| 0:15–0:25 | Shutter opens. The salesman leans in, grins, slides a slip through. The date stamp on the slip: 05 OCT 2026. | Slip: "The Hooly Pixel 10 costs €799." · Caption: "Every statement gets the same inspection." [shutter, paper slide] |

### Act II · The inspection (0:25–1:55): one statement, step by step
Each step opens with a tab sliding in, e.g. **STEP 2 · WHO · linker**.

| Time | Step | Shot | Captions and sound |
|---|---|---|---|
| 0:25–0:35 | 1 Input | The slip lands on the desk; the dossier clipped behind it fans out: the other sentences of its page. | "A statement never travels alone: it comes with its page. Pages that lie, lie together." [clip, papers] |
| 0:35–0:47 | 2 Linker | The Registry thuds open; the clerk runs a finger down the names, then underlines **Hooly Pixel 10** in blue. Its registry card pops up: price · refresh rate · storage… | "WHO is it about? Checked against the Registry of Hooly: every name, every alias." [pages, pencil] |
| 0:47–0:59 | 3 Reader | The Rulebook opens at MONEY; red pencil circles **€799**; margin note: "money · 799 · EUR". | "WHICH value? Read exactly as the organisers' Rulebook reads it." [pencil scratch] |
| 0:59–1:11 | 4 Attributor | The filing cabinet: drawers light up with their odds. "PIXEL 10 · PRICE 99.3%" glows; "PIXEL 10 PRO · PRICE 0.06%" and "PIXEL 9 · PRICE 0.06%" stay dark. The drawer slides out; the slip goes in. | "WHICH fact? A model trained on 2,400 filed facts weighs 52 drawers." [drawer] |
| 1:11–1:16 | 5 Knowledge base | Quick: the ledger, a tick in the margin. | "Already on file? Nothing to correct." [tick] |
| 1:16–1:40 | 6 Truth engine | The clerk takes a lamp and walks into the archive (pan, footsteps). It pulls 11 documents and pins them on a corkboard timeline, Oct 2025 → Oct 2026. Eight get green seals, one a red one. The clerk draws the **lime line** through them: flat at €799 from 28 April, a step down to €749 on 2 September. A pin with the slip goes in at 5 October: the line there reads €749. Cut to the two slips side by side. | "WHEN was it true? Every document about this fact, on one timeline." → "€799 was true. In April." → the side-by-side, bold: "SAME SENTENCE. TRUE IN APRIL. FALSE IN OCTOBER." [footsteps, pins, the line drawn] |
| 1:40–1:52 | 7 Judge | Back at the desk. A stack of 64 tiny evidence cards feeds the polygraph; the needle swings past the 60% line and settles at 98%. The stamp rises… and lands: red **FALSE · STALE**. The clerk nods once. | "64 clues. A forest of decision trees. 98% sure." [needle ticks, STAMP THUD] |
| 1:52–1:55 | 8 Writer | The typewriter clacks the ledger line; the slip drops into the outbox marked output.csv. | Ledger: `s-7,,,,false,0.982` [keys, bell] |

### Act III · The shift (1:55–3:00)
| Time | Shot | Captions and sound |
|---|---|---|
| 1:55–2:10 | Montage, faster, the music lifts: three applicants, three stamps. Gavin with his slip: **INVENTED** (the archive card says 12 languages). The launch host: **PREMATURE** (the archive shows €1,099 that day, €1,049 only later). The salesman's 10 TB slip: green **TRUE** seal. | "Three kinds of lies: never true · no longer true · not true yet." [three stamps, in rhythm] |
| 2:10–2:22 | After hours: the window shutter closes, the lamp dims. The clerk takes a certificate pad and writes; each sheet is checked against the Rulebook, sealed "CERTIFIED TRUE", and stacked. The counter on the stack climbs to 1,000. Show two sheets: "Hooly Pixel 10 Pro costs €1,049." and "Hooly Pixel 10 cost €799 at Made by Hooly 2026." | "After hours: 1,000 new statements, written only from sealed records." [pen, seal, paper stack] |
| 2:22–2:52 | The booth's little monitor flickers on; push in until it fills the frame: **the real screen recording** (Part 5). The live console builds and runs the Docker image on the 20 sample rows, then *Inside the machine* scrolls one sample sentence through the pipeline, the lime line tracing it. Keep the pixel frame of the monitor around it for the first and last second only. | "Live: the real system, in Docker, offline, on the 20 sample rows." If a wait is sped up, say so: "×6". |
| 2:52–3:00 | The shift report, typed on paper. Then the title. | "SHIFT REPORT · 29 OCT 2026" with the numbers of Part 2, then "POLYGRAPH · TEAM ICARUS" and the last line: "Hype is easy to write. Hard to keep consistent. We check the timeline." [keys, final stamp] |

---

## Part 4 · The prompt (paste into a new Claude Code session in this repository)

> Build our 3-minute pitch film as code, in `video/inspection/`, following `docs/PITCH_PAPERS.md`
> exactly: its bible (Part 1), its real data (Part 2) and its shot list with timings and captions
> (Part 3). Read the whole file first.
>
> **How to make it.** A Python frame renderer with Pillow: draw every frame on a 480×270 canvas
> with the palette of Part 1, scale it ×4 with nearest-neighbour to 1920×1080, and assemble at
> 30 fps into `video/inspection/inspection.mp4` with ffmpeg (use `imageio-ffmpeg` if ffmpeg isn't
> on the path). Props and characters animate in 12 fps steps; pans, slides and the lime line move
> smoothly. Draw all art yourself in code (rectangles, pixel sprites defined as small text grids or
> drawn PNGs saved in `video/inspection/sprites/`): no downloaded game assets, and nothing that
> copies the name, characters, sprites, fonts, music or screen layout of an existing game.
> Download the fonts of Part 1 from Google Fonts into `video/fonts/` and render text at native
> pixel sizes (8 or 16 px) so it stays sharp; check `€` renders.
>
> **Sound.** Synthesise the sound effects with numpy (stamp thud, paper slide, pencil, drawer,
> footsteps, pin, needle tick, typewriter key and bell, shutter) and a slow, dry music loop;
> mix them on the shot list's beats into one WAV and mux it into the MP4. No voice.
>
> **Structure.** One function per shot, each taking the shot's local time and returning a frame,
> plus a timeline table that matches Part 3 to the second. `python video/inspection/render.py`
> renders everything; `--from 1:16 --to 1:40` renders one stretch; `--preview` renders at
> 480×270 for speed; `--still 1:30` writes one PNG to check a frame.
>
> **The live insert (2:22–2:52).** Read the screen recording from `video/inspection/live.mp4` if
> it exists, scale it into the monitor frame and then full screen as Part 3 says; until it exists,
> show a placeholder card "LIVE RECORDING · 09:00". Keep it real: never fake the console.
>
> **Accuracy.** Every number, name, date and sentence on screen comes from Part 2. Don't invent
> statistics. The tabs name the real module of each step.
>
> **Check your work.** Render stills at 0:20, 0:40, 1:05, 1:30, 1:45, 2:15 and 2:55 and look at
> them: text sharp and readable, nothing off-screen, the palette respected. Then render the full
> film and check it lasts 3:00.

---

## Part 5 · Timeline (29 Oct)

| When | What |
|---|---|
| Tonight | Build and render the film with the live placeholder; check the stills. |
| 09:00 | The sample lands in `sample/sample.csv` (pull it in from upstream). Start the server, open `/console.html`, tick the sample, **Build and run in Docker**. |
| 09:10 | Record the screen (Windows: `Win+Alt+R`, or OBS) for about 2 minutes: the button, Docker Desktop showing the container, the results, then `/inside.html` scrolling two sample sentences through the pipeline. Save it as `video/inspection/live.mp4`. Pick a sample sentence whose case reads well. |
| 09:30 | Cut the recording to 30 s (speed up the waiting, labelled "×6"), render the final film. |
| 10:15 | Watch it once, start to finish. Fix only what's wrong. |
| 10:30 | Export, hand in the video; PR titled "Icarus" open with everything pushed. **No push after 11:00.** |
