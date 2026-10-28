"""The sound of "The Inspection": every effect and the music synthesised with numpy (no
samples, nothing to license). mix(cues, total) -> stereo float array at SR."""
from __future__ import annotations

import math
import wave

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _noise(sec):
    return _rng.standard_normal(int(sec * SR))


def _lp(x, k):
    """A crude low-pass: a moving average over k samples."""
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def _hp(x, k):
    return x - _lp(x, k)


def _dec(sec, rate):
    return np.exp(-rate * _t(sec))


def _fade(x, a=0.003, r=0.02):
    n = len(x)
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] = np.minimum(e[-nr:], np.linspace(1, 0, nr))
    return x * e


# ---- effects -------------------------------------------------------------------------------------
def key():
    s = 0.07
    x = _hp(_noise(s), 6) * _dec(s, 90) * 0.6 + np.sin(2 * math.pi * 1900 * _t(s)) * _dec(s, 120) * 0.25
    return _fade(x, 0.0005, 0.01)


def thud():
    s = 0.6
    t = _t(s)
    f = 50 + 110 * np.exp(-18 * t)
    body = np.sin(2 * math.pi * np.cumsum(f) / SR) * _dec(s, 7)
    hit = _lp(_noise(s), 12) * _dec(s, 45) * 1.4
    clack = _hp(_noise(s), 4) * _dec(s, 160) * 0.5
    return _fade(body * 0.9 + hit + clack, 0.0005, 0.05)


def seal():
    s = 0.45
    return _fade(thud()[: int(s * SR)] * 0.6 + _lp(_noise(s), 30) * _dec(s, 12) * 0.5, 0.001, 0.05)


def paper(s=0.45):
    t = _t(s)
    band = _lp(_noise(s), 3) - _lp(_noise(s), 40) * 0.6
    return _fade(band * np.sin(math.pi * t / s) ** 1.5 * (0.8 + 0.2 * np.sin(2 * math.pi * 9 * t)) * 0.7)


def flick():
    return paper(0.08) * 0.8


def page():
    return paper(0.32)


def pencil(s=0.7):
    t = _t(s)
    strokes = np.abs(np.sin(2 * math.pi * 6.5 * t)) ** 3
    return _fade(_hp(_noise(s), 3) * strokes * 0.35 * np.sin(math.pi * t / s) ** 0.5)


def marker():
    s = 2.6
    t = _t(s)
    squeak = np.sin(2 * math.pi * (1500 + 120 * np.sin(2 * math.pi * 3 * t)) * t) * 0.05
    return _fade((pencil(s) * 0.8 + squeak) * np.minimum(1, t * 4))


def drawer():
    s = 0.7
    rumble = _lp(_noise(s), 50) * 2.0 * np.sin(math.pi * _t(s) / s)
    x = rumble
    clunk = thud()[: int(0.25 * SR)] * 0.5
    x[-len(clunk):] += clunk
    return _fade(x, 0.01, 0.03)


def step():
    s = 0.13
    return _fade(np.sin(2 * math.pi * 85 * _t(s)) * _dec(s, 30) * 0.6 + _lp(_noise(s), 8) * _dec(s, 60) * 0.3)


def pin():
    s = 0.1
    return _fade(_hp(_noise(s), 2) * _dec(s, 300) * 0.5 + np.sin(2 * math.pi * 3200 * _t(s)) * _dec(s, 60) * 0.15)


def tick():
    s = 0.03
    return _fade(_hp(_noise(s), 2) * _dec(s, 400) * 0.5, 0.0003, 0.005)


def clip():
    x = np.zeros(int(0.08 * SR))
    for at in (0.0, 0.035):
        c = pin() * 0.7
        i = int(at * SR)
        x[i: i + len(c)] += c[: len(x) - i]
    return x


def bell():
    s = 1.6
    t = _t(s)
    x = sum(a * np.sin(2 * math.pi * f * t) for f, a in ((2093, 1.0), (4186, 0.25), (3136, 0.18), (5274, 0.08)))
    return _fade(x * _dec(s, 3.2) * 0.25, 0.001, 0.1)


def shutter():
    s = 1.15
    x = _lp(_noise(s), 25) * 0.6 * np.sin(math.pi * _t(s) / s)
    for k in range(int(s / 0.03)):
        c = tick() * 0.8
        i = int(k * 0.03 * SR)
        x[i: i + len(c)] += c[: len(x) - i]
    return _fade(x)


def blip():
    s = 0.09
    t = _t(s)
    f = np.where(t < 0.04, 660, 990)
    return _fade(np.sign(np.sin(2 * math.pi * np.cumsum(f) / SR)) * 0.08 * _dec(s, 18))


def book():
    return thud()[: int(0.4 * SR)] * 0.45 + np.pad(paper(0.3), (0, int(0.1 * SR)))[: int(0.4 * SR)] * 0.5


def mumble():
    """Game-style gibberish speech: a buzzy voice in syllables."""
    s = 1.3
    t = _t(s)
    pitch = 135 + 25 * np.sin(2 * math.pi * 1.7 * t) + 15 * np.sign(np.sin(2 * math.pi * 5.5 * t))
    saw = 2 * ((np.cumsum(pitch) / SR) % 1.0) - 1
    voice = _lp(saw, 18) * 0.5
    syll = np.clip(np.sin(2 * math.pi * 5.5 * t) * 1.6, 0, 1)
    return _fade(voice * syll * 0.55, 0.01, 0.1)


def cards():
    x = np.zeros(int(2.1 * SR))
    for k in range(40):
        c = flick() * 0.5
        i = int(k * 0.05 * SR)
        x[i: i + len(c)] += c[: len(x) - i]
    return x


def hum():
    s = 135.0
    t = _t(s)
    return (np.sin(2 * math.pi * 50 * t) * 0.6 + np.sin(2 * math.pi * 100 * t) * 0.3) * 0.02 * np.minimum(1, t / 1.5)


EFFECTS = {f.__name__: f for f in (key, thud, seal, paper, flick, page, pencil, marker, drawer, step, pin, tick, clip,
                                    bell, shutter, blip, book, mumble, cards, hum)}


# ---- music: a slow, dry loop in D minor ----------------------------------------------------------
BPM = 84
BEAT = 60 / BPM
NOTE = {"D2": 73.42, "F2": 87.31, "G2": 98.0, "A2": 110.0, "Bb1": 58.27, "C2": 65.41, "A1": 55.0,
        "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0, "C5": 523.25, "D5": 587.33, "Bb3": 233.08}
BASS = ["D2", "D2", "Bb1", "A1"]  # one per bar
MELODY = [  # (beat in an 8-beat phrase, note, beats)
    (0, "A4", 1.5), (1.5, "G4", 0.5), (2, "F4", 1), (3, "E4", 1), (4, "D4", 2), (6.5, "F4", 0.5), (7, "A4", 1)]
MELODY2 = [(0, "D5", 1), (1, "C5", 0.5), (1.5, "A4", 1.5), (3, "G4", 1), (4, "F4", 1.5), (5.5, "G4", 0.5), (6, "A4", 2)]


def _tri(f, s):
    ph = (f * _t(s)) % 1.0
    return 4 * np.abs(ph - 0.5) - 1


def _sq(f, s, duty=0.25):
    return np.where((f * _t(s)) % 1.0 < duty, 1.0, -1.0)


def _put(buf, at, x, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    x = x[: len(buf) - i]
    buf[i: i + len(x), 0] += x * gain * (1 - max(0, pan))
    buf[i: i + len(x), 1] += x * gain * (1 + min(0, pan))


def music(total: float) -> np.ndarray:
    buf = np.zeros((int(total * SR) + SR, 2))

    def level(t):  # the arrangement, by section
        if t < 7:
            return None
        if t < 25:
            return {"bass": 1, "kick": 0.6, "hat": 0, "mel": 0}
        if t < 115:
            return {"bass": 1, "kick": 0.8, "hat": 0.5, "mel": 0.6}
        if t < 130:
            return {"bass": 1.1, "kick": 1, "hat": 1, "mel": 0.9, "fast": 1}
        if t < 142:
            return {"bass": 0.8, "kick": 0.4, "hat": 0, "mel": 0.5}
        if t < 170:
            return {"bass": 0.6, "kick": 0.4, "hat": 0.3, "mel": 0.3}
        return {"bass": 0, "kick": 0, "hat": 0, "mel": 0}

    t = 7.0
    bar = 0
    while t < 170:
        lv = level(t)
        root = NOTE[BASS[bar % 4]]
        for b in range(4):
            bt = t + b * BEAT
            lvb = level(bt)
            if not lvb:
                continue
            if b in (0, 2):
                n = _tri(root, BEAT * 1.6) * np.exp(-1.4 * _t(BEAT * 1.6))
                _put(buf, bt, _fade(n, 0.005, 0.05), 0.32 * lvb["bass"])
                k = np.sin(2 * math.pi * (45 + 60 * np.exp(-25 * _t(0.25))) * _t(0.25)) * _dec(0.25, 14)
                _put(buf, bt, k, 0.35 * lvb["kick"])
            if b == 3:
                _put(buf, bt + BEAT / 2, _fade(_tri(root * 2, BEAT / 2) * _dec(BEAT / 2, 4), 0.005, 0.03), 0.18 * lvb["bass"])
            steps = 4 if lvb.get("fast") else 2
            for s in range(steps):
                if lvb["hat"]:
                    h = _hp(_noise(0.04), 2) * _dec(0.04, 120)
                    _put(buf, bt + s * BEAT / steps, h, 0.08 * lvb["hat"] * (1.0 if s % 2 else 0.6), pan=0.3)
        # the melody, over 2 bars (8 beats), every other phrase
        if lv and lv["mel"] and bar % 2 == 0 and (bar // 2) % 2 == 1:
            phrase = MELODY if (bar // 4) % 2 == 0 else MELODY2
            for at, note, beats in phrase:
                s = beats * BEAT
                n = _lp(_sq(NOTE[note], s), 6) * np.minimum(1, _t(s) * 30) * np.exp(-1.2 * _t(s))
                _put(buf, t + at * BEAT, _fade(n, 0.005, 0.06), 0.07 * lv["mel"], pan=-0.25)
        t += 4 * BEAT
        bar += 1
    # the last chord, under the shift report and the title
    chord = sum(_tri(NOTE[n] * (2 if n.endswith("2") or n.endswith("1") else 1), 8.0) for n in ("D2", "A2", "D4", "F4", "A4"))
    _put(buf, 170.0, _fade(chord * np.minimum(1, _t(8.0) / 1.2) * np.exp(-0.25 * _t(8.0)), 0.01, 2.0), 0.05)
    return buf[: int(total * SR)]


def mix(cues, total: float) -> np.ndarray:
    out = music(total)
    cache = {}
    for at, name, gain in cues:
        if name not in cache:
            cache[name] = EFFECTS[name]()
        _put(out, at, cache[name], gain * 0.9)
    # gentle compression: soft-clip the stamp thuds so everything else can sit louder
    out = out / (np.max(np.abs(out)) or 1.0)
    out = np.tanh(out * 3.2) / np.tanh(3.2)
    return out * 0.89


def write_wav(path, stereo: np.ndarray):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
