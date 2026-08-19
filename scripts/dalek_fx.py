#!/usr/bin/env python3
"""Ring-modulator "Dalek" effect + robot-format encode.

The classic Dalek voice is a performance multiplied by a low sine carrier
(~30 Hz) — true ring modulation, which ffmpeg has no native filter for, so we
do it in numpy. Adds light soft-clip grit and a presence lift, then encodes to
the robot's mono 16 kHz Ogg.

    scripts/dalek_fx.py <pack>              # batch: build/mp3 -> build/ogg
    scripts/dalek_fx.py in.mp3 out.ogg      # single file (for samples)
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

CARRIER_HZ = 30.0     # the Dalek frequency
WORK_SR = 22050       # process above 16 kHz, downsample on encode


def _decode(path):
    """Decode any input to mono float32 at WORK_SR via ffmpeg."""
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-ac", "1", "-ar", str(WORK_SR), "-f", "wav", "-"],
        capture_output=True, check=True,
    ).stdout
    import io
    with wave.open(io.BytesIO(raw)) as w:
        frames = w.readframes(w.getnframes())
    x = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    return x


def ringmod(path, out_ogg, carrier=CARRIER_HZ):
    x = _decode(path)
    t = np.arange(len(x)) / WORK_SR
    y = x * np.sin(2 * np.pi * carrier * t)   # true ring modulation
    y = np.tanh(y * 1.6)                       # grit
    y /= np.max(np.abs(y)) + 1e-9
    pcm = (y * 0.95 * 32767).astype("<i2").tobytes()

    tmp = Path(str(out_ogg) + ".tmp.wav")
    with wave.open(str(tmp), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(WORK_SR)
        w.writeframes(pcm)
    # presence lift + consistent loudness, down to the robot's 16 kHz mono
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp),
         "-af", "highpass=f=180,equalizer=f=2600:t=q:w=1.6:g=4,loudnorm=I=-14:TP=-1.0",
         "-ac", "1", "-ar", "16000", "-c:a", "libvorbis", "-q:a", "4", str(out_ogg)],
        check=True,
    )
    tmp.unlink(missing_ok=True)


def main():
    args = sys.argv[1:]
    # single-file mode
    if len(args) == 2 and args[0].endswith((".mp3", ".wav", ".ogg")):
        ringmod(args[0], args[1])
        print(f"ring-modulated {args[0]} -> {args[1]}")
        return
    # batch mode: a pack name
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import packlib
    name = packlib.arg_pack(sys.argv)
    pdir = packlib.pack_dir(name)
    src, out = pdir / "build" / "mp3", pdir / "build" / "ogg"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for mp3 in sorted(src.glob("*.mp3"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
        ringmod(mp3, out / f"{mp3.stem}.ogg")
        n += 1
    print(f"[{name}] ring-modulated {n} files -> {out}")


if __name__ == "__main__":
    main()
