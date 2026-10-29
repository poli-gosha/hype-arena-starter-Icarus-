# The main page, rebuilt: the Ministry, with Caesar

The main page becomes the interactive version of the film *The Inspection*: same pixel Ministry,
same art, same case (the Hooly Pixel 10 at €799 on 5 October 2026). It is guided by **Caesar**, the
mouse clerk, who lives on the page. The testing page (`console.html`, `inside.html`) comes next, in
a separate plan.

**Deadline.** Everything the pitch needs must be pushed **before 11:00** (a push after 11:00
disqualifies). The scope is set so the core lands by about 07:30 and the testing page by 10:30.

---

## 1 · Principles

1. **One world.** The site and the film are one thing: same palette, fonts, sprites and wording.
   The sprites are rendered from the film's own drawing code (`video/inspection/art.py`), so they match pixel for pixel.
2. **Play explains.** Every interaction shows how the system really works, with real data.
   Nothing is decoration only.
3. **Honest numbers.** Every statement, verdict and figure comes from the data or our measurements,
   as in the film.
4. **Caesar is charming, never in the way.** He can be hidden, he respects reduced motion, and
   everything he says is also on the page.

---

## 2 · Caesar

**Who he is.** The Clerk from the film, now with a name: a small grey mouse in a green visor and
round glasses, in a brown vest. He is deadpan, bureaucratic, secretly delighted by a good stamp, and
hungry. For verdicts he puts on a **laurel wreath** and gives the arena's **thumbs up** (true) or
**thumbs down** (false). The challenge is the *Hype Arena*; he is its emperor.

**How he lives on the page.** A fixed layer above the page. He walks along a floor line at the
bottom of the screen, follows the reader from scene to scene, and steps *into* the scenes to do the
work of each stage. He speaks in pixel speech bubbles, typed letter by letter.

**What he does** (one sprite sheet, 12 fps, drawn from the film's code):

| State | Used for |
|---|---|
| idle (breathing, blinking), look left or right | always; he turns toward the cursor |
| walk, run | moving between scenes, chasing a cheese |
| wave, point, push up glasses | greetings, showing things |
| underline / circle (pencil), carry lamp | the linker, reader and truth desks |
| stamp (wind-up, slam) | the judge desk |
| thumbs up / thumbs down, with laurel | verdicts |
| sniff, eat (chomp) | the cheese game |
| poisoned: turns green, X eyes, tongue out, "bleh", flops over, ghost rises, then he revives | a lie eaten |
| blessed: sparkles, wings and halo, flies up out of view, floats back down on a cloud | a truth eaten |
| yawn, sleep (Zzz), startled | idle too long, poked too often |

**When he reacts** (examples of his lines; each is short and typed):

| Trigger | Caesar |
|---|---|
| page load | pops up in the booth window, waves: "Ave. I'm Caesar. I check what Hooly says." |
| enters each stage | does the stage's job and says one line: "Who is it about? Pixel 10. Underlined." |
| hover the €799 | squints: "That number smells… stale." |
| clicked | a random quip: "Careful. I'm on duty." · after 5 clicks: "Stop poking the Ministry." · after 10: falls asleep |
| idle 25 s | yawns: "Still there? The archive doesn't read itself." |
| scrubbing the timeline | reads the date aloud: "On 1 June it was €799. True!" |
| cheese game outcomes | below |
| typing "gavin" (easter egg) | puts on a black turtleneck: "Trust me. Best phone ever made." |
| the end of the page | holds the door to the live desk: "Bring me real statements." |

**Controls.** A small "hide Caesar" button. With `prefers-reduced-motion` he doesn't walk or fly:
he stays in a corner and only talks. On phones he is smaller and reacts to taps.

---

## 3 · The page, top to bottom

The four parts follow the organisers' structure, like the film. A small label names each part.

### 0 · Title: "Press start"
A pixel starfield of 20,000 dots, one for each statement. One star glows and the camera falls into it.
The star becomes the slip in the Ministry window. Title: **POLYGRAPH · Ministry of Statements**, a
blinking "PRESS START" (scroll or click). Caesar waves from the window.

### 1 · The problem: who, why, what
The booth from the film, with a queue of Hooly's people outside and a counter ticking to 20,000. The
notice reads "No guessing. No LLMs. No internet. 30 minutes." Text: who it's for (auditors,
analysts, newsrooms); why it's hard (weeks by hand; an LLM would guess, and this world contradicts
the web); what we built.

### 2 · The shift: one statement, desk by desk (scroll-driven)
The salesman slides the slip "The Hooly Pixel 10 costs €799." (05 OCT 2026). Each desk is a pixel
scene from the film, with Caesar doing the work, the step tab, and the technical-decision caption.

| Desk | What you see | Interaction |
|---|---|---|
| 1 Input | the slip on its page, the date circled | (extra) click the date: "Watch this. It matters." |
| 2 Linker | the Registry; *Hooly Pixel 10* underlined | (extra) click who the sentence is about |
| 3 Reader | the Rulebook; *€799* circled → money · 799 · EUR | (extra) click the value; Caesar reads it out |
| 4 Attributor | the 52 drawers; Pixel 10 · price, 99.3% | (extra) open any drawer to see its score |
| 5 Knowledge base | the ledger: no correction | — |
| 6 Truth engine | the corkboard: 10 real documents, the lime staircase €799 → €749 | **core: drag the date pin along the year.** The holding value updates, and so does the verdict the same sentence would get on that date ("True on 1 June · False on 5 October"). Caesar reads it out. This is the whole idea in one gesture. |
| 7 Judge | the polygraph needle to 98.2% | **core: press the stamp.** Caesar winds up and slams FALSE · STALE; laurel, thumbs down. |
| 8 Writer | the typewriter: `s-7,,,,false,0.982` | — |

### 3 · Your turn: "Feed Caesar" (you against Polygraph)
The cheese game, using real statements:

1. Two wedges of cheese on two plates. Each carries a slip: a real statement with its date. One is
   true, the other a lie, both from the labelled practice data.
2. You click the cheese Caesar should eat. He runs to it, sniffs, eats it.
3. **A lie**: he turns green, his eyes become X's, "bleh!", and he flops over. A tiny ghost rises,
   then he revives with a sigh. The lie's card flips over to show its kind and the archive's
   evidence, e.g. "STALE: €799 held until 2 September; on 5 October it was €749."
4. **A truth**: sparkles, wings and a halo. He flies up out of view (a little harp) and floats back
   down on a cloud: "Certified delicious."
5. Then Polygraph's pick is shown, with its confidence: "Polygraph picked the same one, 98% sure."
   If Polygraph got one wrong, it says so.
6. Five rounds. Score: **You 3 · Polygraph 5**. A rank at the end: Intern · Clerk · Chief Inspector · Emperor.

The pairs cover all three kinds of lie (invented, stale, premature). They come from a small file the
build script makes from the practice data and our system's trace: short, clear sentences only.

### 4 · Why it matters
The film's memo, made playable:
- The three stamps: INVENTED · STALE · PREMATURE, each with a real example.
- **(extra)** "Draw a claim": a button pulls one of the real 1,000 claims (from `/api/claims`). Caesar reads it out and seals it.
- What makes it different: it judges facts on their date, not the wording; no LLM; every verdict shows its evidence; calibrated confidence.

### 5 · Under the hood
The film's two memos: the implementation numbers, then what it still misses, and what comes next.

### 6 · Exit
The archive door opens onto "**The live desk →**" (the testing page). Caesar holds the door.

---

## 4 · How it is built

| Part | How |
|---|---|
| Sprites | `scripts/make_site_art.py` renders PNG sprite sheets and scene backgrounds with the film's own drawing code (`video/inspection/art.py`): Caesar's states, cheese, plates, wings, halo, ghost, stamps, booth, desks, corkboard. Output in `server/static/assets/`. |
| Pixel display | Images drawn on canvases at the film's 480×270 scale, enlarged with `image-rendering: pixelated`. Text is HTML in the pixel fonts (crisp at any size), not baked into images. |
| Caesar | `assets/caesar.js`: a small state machine (states above) with a walk path, a typed speech-bubble queue, triggers (scroll, hover, click, idle, game events) and a "hide" switch. |
| Story | Scroll-driven scenes with the same timings and captions as the film. |
| Game data | `scripts/make_game_data.py` writes `assets/cheese.json`: pairs of real statements (truth labels from practice data, Polygraph's verdict and the reason from the trace). |
| Sound | The film's synthesised effects (`video/inspection/sound.py`) exported as small files: stamp, chomp, bleh, harp, pencil, typewriter. Off until the speaker icon is clicked. |
| Old page | The WebGL universe moves to `universe.html` (kept, linked in the footer). |
| Stack | Plain HTML, CSS and JavaScript, as now. No build step, served by `server/app.py`. |

---

## 5 · Tonight's order (checkpoints are pushed as they land)

| By | What |
|---|---|
| 02:00 | Sprite pipeline; page skeleton in pixel style; the old page moved to `universe.html` |
| 03:30 | Caesar: idle, walk, talk, click, idle quips, hide; follows the scroll |
| 05:00 | The story, parts 0–2, scroll-driven, with Caesar at each desk |
| 06:30 | The cheese game, with real pairs, both endings and the score |
| 07:30 | The core desks: the timeline pin and the stamp. Parts 4–6. **Core done, pushed.** |
| 08:30 | The testing page (its own plan) |
| 09:00 | The sample lands: run the live check on it |
| 09:00–10:30 | Extras if time allows; phone layout; a full pass in the browser |
| 10:45 | Last push. **Nothing after 11:00.** |

## 6 · Risks

- **Time.** The extras are optional by design; the core alone is a complete page.
- **Speed.** The pixel art is small images, much lighter than the WebGL page. Checked on a phone-sized screen.
- **Phones.** Caesar shrinks, taps replace hovers, and the scenes stack.
