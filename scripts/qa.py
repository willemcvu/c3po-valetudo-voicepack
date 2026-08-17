#!/usr/bin/env python3
"""Sanity-check generated prompts before packaging.

Flags the two failure modes that actually happen with TTS batches: a clip that
came out far longer than the stock prompt it replaces (the robot talks over
itself), and a clip that is suspiciously short or silent (a failed generation
that still wrote a file).
"""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "lines.csv"

# A rewrite is allowed to run longer than the stock line — Threepio is wordier by
# design — but past this it stops being charming.
LONG_RATIO = 2.5
LONG_ABS = 9.0
SHORT_ABS = 0.6


def duration(path):
    out = subprocess.run(
        ["/usr/bin/ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def main():
    audio_dir = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "build/mp3")
    ext = "*.mp3" if "mp3" in audio_dir.name else "*.ogg"
    rows = {r["id"]: r for r in csv.DictReader(CSV.open())}

    present, long_, short, silent = [], [], [], []
    for f in sorted(audio_dir.glob(ext), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
        row = rows.get(f.stem)
        if not row:
            continue
        d = duration(f)
        stock = float(row["duration"]) or 0.01
        present.append(f.stem)
        if d < SHORT_ABS:
            (silent if d < 0.1 else short).append((f.stem, d, stock, row["c3po_text"]))
        elif d > LONG_ABS or d / stock > LONG_RATIO:
            long_.append((f.stem, d, stock, row["c3po_text"]))

    expected = [r["id"] for r in rows.values() if r["status"] != "skip" and r["c3po_text"].strip()]
    missing = sorted(set(expected) - set(present), key=lambda x: int(x) if x.isdigit() else 0)

    print(f"{len(present)} / {len(expected)} generated in {audio_dir}")
    if missing:
        print(f"\nMISSING ({len(missing)}): {', '.join(missing[:40])}"
              + (" …" if len(missing) > 40 else ""))
    for label, items in (("SILENT", silent), ("VERY SHORT", short), ("LONG", long_)):
        if items:
            print(f"\n{label} ({len(items)}):")
            for sid, d, stock, text in items[:25]:
                print(f"  {sid:>4}  {d:5.2f}s (stock {stock:.2f}s)  {text[:66]}")
            if len(items) > 25:
                print(f"  … +{len(items) - 25} more")
    if not (missing or silent or short or long_):
        print("\nno issues found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
