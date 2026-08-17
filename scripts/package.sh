#!/usr/bin/env bash
# Package a pack's encoded prompts into the tar.gz the Dreame firmware expects.
#
#   ./package.sh <pack>
#
# Reads packs/<pack>/build/ogg, writes packs/<pack>/dist/<pack>.tar.gz + HASH.txt.
# The .ogg files must sit at the ARCHIVE ROOT — no enclosing directory, or the
# firmware extracts them somewhere it never looks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${1:?usage: package.sh <pack>}"
PDIR="$ROOT/packs/$NAME"
OGG_DIR="$PDIR/build/ogg"
DIST="$PDIR/dist"

[ -f "$PDIR/pack.py" ] || { echo "no pack '$NAME' at $PDIR" >&2; exit 1; }

count=$(find "$OGG_DIR" -maxdepth 1 -name '*.ogg' 2>/dev/null | wc -l)
if [ "$count" -eq 0 ]; then
  echo "no .ogg files in $OGG_DIR — run encode.sh $NAME first" >&2
  exit 1
fi

mkdir -p "$DIST"
tar -czf "$DIST/$NAME.tar.gz" -C "$OGG_DIR" $(cd "$OGG_DIR" && ls *.ogg)

HASH=$(md5sum "$DIST/$NAME.tar.gz" | awk '{print $1}')
printf '%s\n' "$HASH" > "$DIST/HASH.txt"

echo "$count prompts -> $DIST/$NAME.tar.gz  ($(du -h "$DIST/$NAME.tar.gz" | cut -f1))"
echo "md5: $HASH"
