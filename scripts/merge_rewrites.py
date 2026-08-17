#!/usr/bin/env python3
"""Merge the authored C-3PO rewrites into lines.csv.

Safe to re-run. Rows already marked 'approved' are left untouched, so hand
edits survive a regeneration.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rewrites as R  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "lines.csv"

FIELDS = [
    "id", "duration", "whisper_text", "community_text", "stock_text",
    "source", "c3po_text", "status",
]


def main():
    rows = list(csv.DictReader(CSV.open()))
    filled = skipped = kept = missing = 0

    for r in rows:
        sid = int(r["id"]) if r["id"].isdigit() else None

        if r.get("status") == "approved":
            kept += 1
            continue

        if sid in R.SKIP:
            r["c3po_text"] = ""
            r["status"] = "skip"
            skipped += 1
        elif sid in R.REWRITES:
            r["c3po_text"] = R.REWRITES[sid]
            r["status"] = "review"
            filled += 1
        else:
            r["status"] = "MISSING"
            missing += 1

    with CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    chars = sum(len(r["c3po_text"]) for r in rows)
    print(f"filled {filled}  skip {skipped}  kept-approved {kept}  MISSING {missing}")
    print(f"total characters to synthesise: {chars:,}")
    if missing:
        ids = [r["id"] for r in rows if r["status"] == "MISSING"]
        print("no rewrite for ids:", ", ".join(ids))


if __name__ == "__main__":
    sys.exit(main())
