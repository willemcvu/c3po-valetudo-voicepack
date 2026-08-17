#!/usr/bin/env python3
"""Merge a pack's authored rewrites with the shared stock inventory.

    scripts/merge_rewrites.py <pack>

Reads stock_lines.csv + packs/<pack>/pack.py, writes packs/<pack>/lines.csv
(the reviewable, per-pack source of truth). Safe to re-run; rows already marked
'approved' keep their hand-edited text.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import packlib  # noqa: E402

FIELDS = ["id", "duration", "stock_text", "voice_text", "status"]


def main():
    name = packlib.arg_pack(sys.argv)
    pack = packlib.load_pack(name)
    out = packlib.pack_dir(name) / "lines.csv"

    existing = {}
    if out.exists():
        existing = {r["id"]: r for r in csv.DictReader(out.open())}

    rows = []
    filled = skipped = kept = missing = 0
    for s in packlib.stock_lines():
        sid = int(s["id"]) if s["id"].isdigit() else None
        prev = existing.get(s["id"], {})

        if prev.get("status") == "approved":
            row = {**prev, "duration": s["duration"], "stock_text": s["stock_text"]}
            kept += 1
        elif sid in pack.SKIP:
            row = {"id": s["id"], "duration": s["duration"], "stock_text": s["stock_text"],
                   "voice_text": "", "status": "skip"}
            skipped += 1
        elif sid in pack.REWRITES:
            row = {"id": s["id"], "duration": s["duration"], "stock_text": s["stock_text"],
                   "voice_text": pack.REWRITES[sid], "status": "review"}
            filled += 1
        else:
            row = {"id": s["id"], "duration": s["duration"], "stock_text": s["stock_text"],
                   "voice_text": "", "status": "MISSING"}
            missing += 1
        rows.append({k: row.get(k, "") for k in FIELDS})

    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    chars = sum(len(r["voice_text"]) for r in rows)
    print(f"[{name}] filled {filled}  skip {skipped}  kept-approved {kept}  MISSING {missing}")
    print(f"[{name}] {chars:,} characters to synthesise  ->  {out}")
    if missing:
        ids = [r["id"] for r in rows if r["status"] == "MISSING"]
        print("no rewrite for ids:", ", ".join(ids))


if __name__ == "__main__":
    sys.exit(main())
