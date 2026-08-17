# C-3PO voice pack for Valetudo

A C-3PO voice pack for Dreame robot vacuums running [Valetudo](https://valetudo.cloud/).
All 421 stock prompts are rewritten and re-voiced.

Built and tested on a Dreame L10S Pro Ultra Heat (`r2338`). Other Dreame models using the
same sound IDs are likely compatible but untested.

Sample: [`samples/demo.ogg`](samples/demo.ogg) (16 kHz mono, as played by the robot).

## Install

In Valetudo, open **Robot Settings > Misc Settings > Voice packs** and enter:

| Field | Value |
|---|---|
| URL | `https://github.com/willemcvu/c3po-valetudo-voicepack/raw/main/dist/c3po.tar.gz` |
| Language Code | `C3PO` |
| Hash | `1b1cf266a263a2bdc34df61368a4d429` |

Select **Set Voice Pack**. The robot downloads the archive, verifies the MD5, and extracts it
to `/data/personalized_voice/C3PO/`.

## Uninstall

Set the language code back to `EN`. The factory prompts in `/audio/EN` are not modified by
the install.

## Build

```bash
python3 -m venv .venv && .venv/bin/pip install faster-whisper
echo "sk-..." > elevenlabs_api_key.txt

.venv/bin/python scripts/transcribe.py       # robot's stock oggs -> lines.csv
.venv/bin/python scripts/merge_rewrites.py   # rewrites.py -> lines.csv
.venv/bin/python scripts/generate.py         # lines.csv -> build/mp3/
./scripts/encode.sh build/mp3 build/ogg p1   # -> ogg mono 16 kHz
./scripts/package.sh                         # -> dist/c3po.tar.gz + hash
```

Prompt text is defined in `scripts/rewrites.py`. `generate.py` skips lines that already have
an mp3, so editing a subset only regenerates those. Delete the corresponding files in
`build/mp3/` to force regeneration.

`encode.sh` accepts a profile argument from `p0` (no processing) to `p3` (maximum). The
published pack uses `p1`.

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
