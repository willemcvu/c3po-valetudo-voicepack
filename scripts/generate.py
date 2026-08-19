#!/usr/bin/env python3
"""Synthesise a pack's approved lines to packs/<pack>/build/mp3/<id>.mp3.

    scripts/generate.py <pack>

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
import packlib  # noqa: E402
import tts  # noqa: E402

MODEL = "eleven_v3"       # the only model that honours the inline [tags]
WORKERS = 3               # conservative; ElevenLabs caps concurrent requests by tier
MAX_RETRIES = 4

lock = Lock()
done = failed = skipped = 0


def synth(job, voice_id, out_dir, key, settings=None):
    global done, failed
    sound_id, text = job
    dest = out_dir / f"{sound_id}.mp3"
    for attempt in range(MAX_RETRIES):
        try:
            dest.write_bytes(tts.speak(text, voice_id, model=MODEL, settings=settings, key=key))
            with lock:
                done += 1
                print(f"  [{done + failed + skipped}] {sound_id}", flush=True)
            return
        except urllib.error.HTTPError as e:
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
    name = packlib.arg_pack(sys.argv)
    pack = packlib.load_pack(name)
    pdir = packlib.pack_dir(name)
    out_dir = pdir / "build" / "mp3"
    out_dir.mkdir(parents=True, exist_ok=True)

    voice_tag = pack.META["voice_tag"]
    voice_id = tts.voices(pdir)[voice_tag]
    settings = pack.META.get("voice_settings")
    key = tts.api_key()

    lines_csv = pdir / "lines.csv"
    jobs = []
    for r in csv.DictReader(lines_csv.open()):
        if r["status"] == "skip" or not r["voice_text"].strip():
            continue
        if (out_dir / f"{r['id']}.mp3").exists():
            skipped += 1
            continue
        jobs.append((r["id"], r["voice_text"]))

    chars = sum(len(t) for _, t in jobs)
    print(f"[{name}] voice {voice_tag} ({voice_id}) · model {MODEL}")
    print(f"[{name}] {len(jobs)} to synthesise, {skipped} already present, ~{chars:,} characters\n")
    if not jobs:
        print("nothing to do")
        return 0

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for job in jobs:
            pool.submit(synth, job, voice_id, out_dir, key, settings)

    print(f"\n[{name}] done {done}  failed {failed}  skipped {skipped}  ->  {out_dir}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
