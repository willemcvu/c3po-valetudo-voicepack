# Valetudo voice packs for Dreame

Custom voice packs for Dreame robot vacuums running [Valetudo](https://valetudo.cloud/). Each
pack rewrites and re-voices all 421 stock prompts in character.

Built and tested on a Dreame L10S Pro Ultra Heat (`r2338`). Other Dreame models using the
same sound IDs are likely compatible but untested.

Packs:

- **C-3PO** (`packs/c3po/`) — fussy, anxious protocol droid. Language code `C3PO`.
- **DJ Catnip** (`packs/djcatnip/`) — hip music-loving cat DJ, cloned voice. Language code `CATNIP`.
- **JARVIS** (`packs/jarvis/`) — calm, refined AI butler, cloned voice. Language code `JARVIS`.

## Browse and install

A catalog site (GitHub Pages, generated into `docs/`) lets you sample each pack and copy its
install fields: browse, play, then paste the URL / Language Code / Hash into Valetudo.
Regenerate it with `scripts/build_site.py` after adding or rebuilding a pack.

## Install

In Valetudo, open **Robot Settings > Misc Settings > Voice packs** and enter the URL, Language
Code and Hash for a pack. Get them from the catalog site (copy buttons), or read them from the
pack: the URL follows

```
https://github.com/<owner>/<repo>/raw/main/packs/<pack>/dist/<pack>.tar.gz
```

the Language Code is `META["language_code"]` in `packs/<pack>/pack.py`, and the Hash is in
`packs/<pack>/dist/HASH.txt`.

Select **Set Voice Pack**. The robot downloads the archive, verifies the MD5, and extracts it
to `/data/personalized_voice/<language code>/`.

## Uninstall

Set the language code back to `EN`. The factory prompts in `/audio/EN` are not modified by
the install.

## Build

Each pack lives in `packs/<name>/`. A pack is one `pack.py` declaring `META` (name, language
code, voice tag, encode profile), `SKIP`, and `REWRITES`, plus a `voices.json` of ElevenLabs
voice IDs. The stock prompt inventory (`stock_lines.csv`) is shared across packs. Scripts take
a pack name:

```bash
python3 -m venv .venv && .venv/bin/pip install faster-whisper numpy
echo "sk-..." > elevenlabs_api_key.txt

.venv/bin/python scripts/transcribe.py            # robot's stock oggs -> stock_lines.csv (once)
.venv/bin/python scripts/merge_rewrites.py <pack> # pack.py + stock -> packs/<pack>/lines.csv
.venv/bin/python scripts/generate.py <pack>       # -> packs/<pack>/build/mp3/
./scripts/encode.sh <pack>                        # -> packs/<pack>/build/ogg (profile from pack.py)
./scripts/package.sh <pack>                        # -> packs/<pack>/dist/<pack>.tar.gz + hash
.venv/bin/python scripts/build_site.py            # regenerate docs/ catalog
```

`generate.py` skips lines that already have an mp3, so editing a subset only regenerates
those — delete the corresponding files in `packs/<pack>/build/mp3/` to force it.

`encode.sh` uses the profile in `pack.py` (`p0` clean … `p3` heavily processed); a droid uses
`p1`, a natural voice `p0`. `scripts/make_beat.py` generates royalty-free beats (synthesised,
no samples) for mixing under signature prompts.

Requires ffmpeg and an ElevenLabs API key. The key is read from `ELEVENLABS_API_KEY` if set,
otherwise from `elevenlabs_api_key.txt`.

## Format

Dreame voice packs are a gzipped tar archive of Ogg Vorbis files, mono 16 kHz, named by sound
ID with no enclosing directory. Valetudo passes the robot a URL and an MD5; the robot performs
the download and extraction.

This format is unrelated to Roborock voice packs. Roborock instructions and the
`valetudo-helper-voicepacks` tool do not apply.

Two implementation notes:

1. Delivery is determined largely by punctuation in the source text (interjections, capitals,
   exclamation marks) rather than by the voice model.
2. Evaluate output as encoded `.ogg` files, not the intermediate `.mp3` files. The robot plays
   16 kHz mono through a small speaker, which differs substantially from full-rate audio.

## Credit

Format and process documented by:

- [czaky/dreame_voice_pack](https://github.com/czaky/dreame_voice_pack)
- [RobinFrcd/valetudo-dreame-voicepack](https://github.com/RobinFrcd/valetudo-dreame-voicepack)
- [Findus23/voice_pack_dreame](https://github.com/Findus23/voice_pack_dreame)
- [sproft/dreame-x40-glados-voice-pack](https://github.com/sproft/dreame-x40-glados-voice-pack)

Voice generated with ElevenLabs Voice Design. Not affiliated with Lucasfilm or Dreame.
