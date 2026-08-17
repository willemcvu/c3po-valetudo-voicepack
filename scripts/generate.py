#!/usr/bin/env python3
"""Synthesise every approved C-3PO line to build/mp3/<id>.mp3.

Resumable: a line whose mp3 already exists is skipped, so an interrupted run
costs nothing to restart and a text tweak only re-bills the lines that changed.
Delete a single mp3 to regenerate just that one.
"""
import csv
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "lines.csv"
OUT = ROOT / "build" / "mp3"

VOICE_TAG = "C2"          # the candidate picked in listening tests
MODEL = "eleven_v3"       # the only model that honours the inline [tags]
WORKERS = 3               # conservative; ElevenLabs caps concurrent requests by tier
MAX_RETRIES = 4

lock = Lock()
done = failed = skipped = 0


def synth(job, voice_id, key):
    global done, failed
    sound_id, text = job
    dest = OUT / f"{sound_id}.mp3"

    for attempt in range(MAX_RETRIES):
        try:
            dest.write_bytes(tts.speak(text, voice_id, model=MODEL, key=key))
            with lock:
                done += 1
                print(f"  [{done + failed + skipped}] {sound_id}", flush=True)
            return
        except urllib.error.HTTPError as e:
            # 429 = rate limited, 5xx = transient. Back off and retry; anything
            # else is a real problem with the line and shouldn't be retried.
            if e.code not in (429, 500, 502, 503, 504) or attempt == MAX_RETRIES - 1:
                with lock:
                    failed += 1
                    print(f"  FAIL {sound_id}: {e.code} {e.read()[:160]!r}", flush=True)
                return
            time.sleep(2 ** attempt)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                with lock:
                    failed += 1
                    print(f"  FAIL {sound_id}: {e}", flush=True)
                return
            time.sleep(2 ** attempt)


def main():
    global skipped
    OUT.mkdir(parents=True, exist_ok=True)
    voice_id = tts.voices()[VOICE_TAG]
    key = tts.api_key()

    jobs = []
    for r in csv.DictReader(CSV.open()):
        if r["status"] == "skip" or not r["c3po_text"].strip():
            continue
        if (OUT / f"{r['id']}.mp3").exists():
            skipped += 1
            continue
        jobs.append((r["id"], r["c3po_text"]))

    chars = sum(len(t) for _, t in jobs)
    print(f"voice {VOICE_TAG} ({voice_id}) · model {MODEL}")
    print(f"{len(jobs)} to synthesise, {skipped} already present, ~{chars:,} characters\n")
    if not jobs:
        print("nothing to do")
        return 0

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for job in jobs:
            pool.submit(synth, job, voice_id, key)

    print(f"\ndone {done}  failed {failed}  skipped {skipped}  ->  {OUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
