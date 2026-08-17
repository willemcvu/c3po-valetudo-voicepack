#!/usr/bin/env python3
"""Generate a royalty-free lo-fi beat as a WAV.

Everything here is synthesised from oscillators and noise, so the output is
categorically free of any copyright — no samples, no loops, nothing to license.
Tuned for the robot's tiny 16 kHz mono speaker: energy sits in the midrange, not
sub-bass the driver can't move.

    scripts/make_beat.py <out.wav> [bars]
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 88                      # boom-bap tempo
BEAT = 60 / BPM
STEP = BEAT / 4              # sixteenth note
SWING = 0.055               # push odd 16ths late for a lazy shuffle
RNG = np.random.default_rng(7)   # fixed seed → reproducible beat


def env(n, attack=0.002, decay=0.15, power=2.0):
    """A simple pluck envelope of length n samples."""
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    d = np.exp(-t / decay) ** power
    return a * d


def kick(dur=0.28):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # pitch drop 150 -> 55 Hz plus a click, so it reads on a small speaker
    f = 55 + 95 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    click = RNG.standard_normal(n) * np.exp(-t * 400) * 0.4
    return (body * env(n, decay=0.11, power=1.6) + click) * 0.9


def snare(dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = RNG.standard_normal(n)
    tone = np.sin(2 * np.pi * 190 * t) * 0.5
    return (noise * 0.7 + tone) * env(n, decay=0.09, power=1.8) * 0.7


def hat(dur=0.06, open_=False):
    n = int(dur * (SR if not open_ else SR))
    if open_:
        n = int(0.16 * SR)
    t = np.arange(n) / SR
    noise = RNG.standard_normal(n)
    # crude high-pass: difference of the noise emphasises highs
    hp = np.diff(noise, prepend=noise[0])
    return hp * np.exp(-t / (0.05 if open_ else 0.015)) * 0.35


def bass(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # square wave keeps harmonics the little speaker can actually reproduce
    sq = np.sign(np.sin(2 * np.pi * freq * t))
    return sq * env(n, decay=0.18, power=1.2) * 0.32


def bleep(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tri = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    return tri * env(n, decay=0.12, power=1.5) * 0.16


def place(buf, sound, step, vel=1.0):
    """Drop a one-shot at a 16th-note step, with swing on odd steps."""
    t = step * STEP + (SWING * STEP if step % 2 else 0)
    i = int(t * SR)
    j = min(i + len(sound), len(buf))
    buf[i:j] += sound[: j - i] * vel


# note frequencies (a minor-ish riff): A2, C3, E3, G2
A2, C3, E3, G2 = 110.0, 130.8, 164.8, 98.0


def make(bars):
    steps_per_bar = 16
    total = bars * steps_per_bar
    buf = np.zeros(int(total * STEP * SR) + SR // 2)

    # patterns are per-bar step lists (0..15); velocities add human-ish bounce
    kick_steps = [0, 3, 6, 10, 11]
    snare_steps = [4, 12]
    bass_line = {0: A2, 3: A2, 6: G2, 8: C3, 10: E3, 11: E3}  # follows the kick, moves in the 2nd half
    hook = {0: E3 * 2, 6: G2 * 2, 8: C3 * 2, 14: A2 * 2}       # sparse melodic hook, octave up

    for b in range(bars):
        base = b * steps_per_bar
        for s in kick_steps:
            place(buf, kick(), base + s, 0.9 + 0.1 * RNG.random())
        for s in snare_steps:
            place(buf, snare(), base + s, 0.85 + 0.1 * RNG.random())
        for s in range(0, steps_per_bar, 2):          # hats on every 8th
            place(buf, hat(open_=(s % 8 == 6)), base + s, 0.6 + 0.4 * RNG.random())
        for s, f in bass_line.items():
            place(buf, bass(f, STEP * 2.2), base + s, 0.9)
        if b % 2 == 1:                                 # hook only every other bar, so it's a lift
            for s, f in hook.items():
                place(buf, bleep(f, STEP * 1.8), base + s, 1.0)

    # light lo-fi glue: gentle saturation + a whisper of vinyl hiss
    buf = np.tanh(buf * 1.4) * 0.8
    buf += RNG.standard_normal(len(buf)) * 0.004
    buf /= np.max(np.abs(buf)) + 1e-9
    return (buf * 0.92 * 32767).astype(np.int16)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "beat.wav"
    bars = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    data = make(bars)
    with wave.open(out, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"wrote {out}  ({len(data)/SR:.2f}s, {bars} bars @ {BPM} BPM)")


if __name__ == "__main__":
    main()
