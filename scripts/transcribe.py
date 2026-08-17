#!/usr/bin/env python3
"""Transcribe the robot's stock English prompts into a line inventory.

Reads every reference/robot/EN/<id>.ogg, transcribes it with faster-whisper,
and merges the result with the community-supplied labels we already trust.
Output is lines.csv, the source of truth for the rest of the pipeline.
"""
import csv
import json
import os
import struct
import sys
from pathlib import Path

from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
EN_DIR = ROOT / "reference" / "robot" / "EN"
COMMUNITY_CSV = ROOT / "reference" / "community" / "robinfrcd_sound_list_l10s_ultra.csv"
OUT_CSV = ROOT / "lines.csv"

MODEL = os.environ.get("WHISPER_MODEL", "small.en")

# Biases Whisper toward the vacuum-robot vocabulary these prompts actually use.
PROMPT = (
    "Robot vacuum voice prompts. Dust bin, mop pad, water tank, dock, charging "
    "station, main brush, side brush, filter, Wi-Fi network, cleaning complete, "
    "returning to the dock, battery low, living room, bedroom, kitchen, bathroom."
)


def duration(path):
    """Ogg duration from the final page's granulepos (all files are 16 kHz)."""
    data = path.read_bytes()
    i = data.rfind(b"OggS")
    if i < 0:
        return 0.0
    return struct.unpack("<q", data[i + 6 : i + 14])[0] / 16000.0


def sort_key(sound_id):
    return (0, int(sound_id)) if sound_id.isdigit() else (1, 0)


def load_community():
    """Optional cross-check labels.

    Other people's sound lists aren't redistributed here (see README for the
    projects worth crediting). Drop a two-column `filename,transcript` CSV at
    COMMUNITY_CSV to measure Whisper's error rate against known-good labels;
    without it transcription still works, just unverified.
    """
    if not COMMUNITY_CSV.exists():
        return {}
    rows = list(csv.reader(COMMUNITY_CSV.open()))[1:]
    return {r[0].removesuffix(".ogg"): r[1].strip() for r in rows if len(r) >= 2}


def main():
    known = load_community()
    files = sorted(EN_DIR.glob("*.ogg"), key=lambda p: sort_key(p.stem))
    print(f"{len(files)} prompts, {len(known)} community labels available")

    print(f"loading whisper '{MODEL}' (cpu/int8)...", flush=True)
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")

    rows = []
    agree = disagree = 0
    for n, path in enumerate(files, 1):
        segments, _ = model.transcribe(
            str(path), language="en", initial_prompt=PROMPT, beam_size=5
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        sound_id = path.stem
        ref = known.get(sound_id, "")

        if ref:
            # Cheap agreement signal so we can judge Whisper's reliability on
            # the 273 files nobody has ever labelled.
            a = set(text.lower().split())
            b = set(ref.lower().split())
            if b and len(a & b) / len(b) >= 0.6:
                agree += 1
            else:
                disagree += 1

        rows.append(
            {
                "id": sound_id,
                "duration": f"{duration(path):.2f}",
                "whisper_text": text,
                "community_text": ref,
                "stock_text": ref or text,
                "source": "community" if ref else "whisper",
                "c3po_text": "",
                "status": "todo",
            }
        )
        if n % 25 == 0 or n == len(files):
            print(f"  {n}/{len(files)}", flush=True)

    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    checked = agree + disagree
    print(f"\nwrote {OUT_CSV} ({len(rows)} rows)")
    if checked:
        print(f"whisper vs community: {agree}/{checked} agree ({agree/checked:.0%})")


if __name__ == "__main__":
    sys.exit(main())
