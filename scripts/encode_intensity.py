#!/usr/bin/env python3
"""Per-line loudness encoder: loud-and-clipping for shouts, loud-and-clean for calm.

    scripts/encode_intensity.py <pack>

Some packs (Gordon Ramsay) want the shouting lines slammed into clipping and the
quiet lines merely loud. This reads packs/<pack>/lines.csv, classifies each line
by intensity, and applies the matching ffmpeg chain when encoding build/mp3 ->
build/ogg (mono 16 kHz).

A line is "shout" if it carries a [shouting]/[angry] tag or contains an
ALL-CAPS emphasis word; everything else is "calm".
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import packlib  # noqa: E402

# Shared front of the chain: faster (1.12x), presence-lifted, compressed.
FRONT = ("atempo=1.12,highpass=f=130,equalizer=f=3800:t=q:w=1.3:g=5,"
         "acompressor=threshold=-18dB:ratio=4:attack=4:release=110")
# calm: loud but clean — brickwall-limited just under full scale.
CALM = FRONT + ",loudnorm=I=-9:TP=-1.0,alimiter=limit=0.98"
# shout: LOUD, pushed ~2 dB past full scale so the peaks clip and grit.
SHOUT = FRONT + ",loudnorm=I=-11:TP=-1.0,volume=3dB"

CAPS = re.compile(r"\b[A-Z]{2,}\b")


def is_shout(text):
    if re.search(r"\[(shouting|angry)\]", text):
        return True
    # strip the emotion tag before looking for emphasis capitals
    return bool(CAPS.search(re.sub(r"\[[a-z ]+\]", "", text)))


def main():
    name = packlib.arg_pack(sys.argv)
    pdir = packlib.pack_dir(name)
    src = pdir / "build" / "mp3"
    out = pdir / "build" / "ogg"
    out.mkdir(parents=True, exist_ok=True)

    rows = {r["id"]: r for r in csv.DictReader((pdir / "lines.csv").open())}
    n = shouts = 0
    for mp3 in sorted(src.glob("*.mp3"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
        row = rows.get(mp3.stem)
        if not row:
            continue
        shout = is_shout(row["voice_text"])
        shouts += shout
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp3),
             "-af", SHOUT if shout else CALM,
             "-ac", "1", "-ar", "16000", "-c:a", "libvorbis", "-q:a", "4",
             str(out / f"{mp3.stem}.ogg")],
            check=True,
        )
        n += 1
    print(f"[{name}] encoded {n} files -> {out}  ({shouts} shout / {n - shouts} calm)")


if __name__ == "__main__":
    sys.exit(main())
