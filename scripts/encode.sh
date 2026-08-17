#!/usr/bin/env bash
# Encode TTS output to exactly what the Dreame firmware expects:
# Ogg Vorbis, mono, 16 kHz — optionally through a processing chain.
#
#   ./encode.sh <pack>                       # pack mode: build/mp3 -> build/ogg, profile from pack.py
#   ./encode.sh <input-dir> <output-dir> [p] # manual mode: explicit dirs + profile
#
# Profiles (character colouring, increasing):
#   p0  clean       loudness-normalised only, no colouring  (natural voices)
#   p1  light       presence lift + narrow band + short reflection
#   p2  medium      p1 + flanger shimmer (metallic)
#   p3  heavy       p2 + chorus and gentle bit-crush (overtly synthetic)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Pack mode when the single argument names a pack.
if [ "$#" -eq 1 ] && [ -f "$ROOT/packs/$1/pack.py" ]; then
  NAME="$1"
  IN="$ROOT/packs/$NAME/build/mp3"
  OUT="$ROOT/packs/$NAME/build/ogg"
  PROFILE=$(python3 -c "import sys;sys.path.insert(0,'$ROOT/scripts');import packlib;print(packlib.load_pack('$NAME').META['profile'])")
else
  IN="${1:?usage: encode.sh <pack>  |  encode.sh <in-dir> <out-dir> [profile]}"
  OUT="${2:?usage: encode.sh <pack>  |  encode.sh <in-dir> <out-dir> [profile]}"
  PROFILE="${3:-p1}"
fi

# Applied last in every chain: consistent perceived loudness across prompts,
# so an error message doesn't blast twice as loud as a status chirp.
NORM="loudnorm=I=-16:TP=-1.0:LRA=11"

case "$PROFILE" in
  p0) FX="highpass=f=150" ;;
  p1) FX="highpass=f=200,equalizer=f=2500:t=q:w=1.5:g=4,lowpass=f=7500,aecho=0.9:0.5:12:0.25" ;;
  p2) FX="highpass=f=220,equalizer=f=2800:t=q:w=1.5:g=5,flanger=delay=2:depth=1.5:speed=0.6:width=60,lowpass=f=7000,aecho=0.9:0.45:14:0.30" ;;
  p3) FX="highpass=f=250,equalizer=f=3000:t=q:w=1.5:g=6,chorus=0.6:0.9:35:0.5:0.4:2,acrusher=bits=10:mode=log:mix=0.25,lowpass=f=6800,aecho=0.9:0.45:16:0.32" ;;
  *)  echo "unknown profile: $PROFILE (expected p0|p1|p2|p3)" >&2; exit 1 ;;
esac

mkdir -p "$OUT"
n=0
shopt -s nullglob
for f in "$IN"/*.{mp3,wav,ogg}; do
  base="$(basename "$f")"
  ffmpeg -hide_banner -loglevel error -y -i "$f" \
    -ac 1 -ar 16000 -c:a libvorbis -q:a 4 \
    -af "${FX},${NORM}" \
    "$OUT/${base%.*}.ogg"
  n=$((n + 1))
done

echo "encoded $n file(s) -> $OUT (profile $PROFILE)"
