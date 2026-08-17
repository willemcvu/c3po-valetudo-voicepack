#!/usr/bin/env bash
# Package encoded prompts into the tar.gz the Dreame firmware expects.
#
#   ./package.sh [ogg-dir] [output-name]
#
# The .ogg files must sit at the ARCHIVE ROOT — no enclosing directory, or the
# firmware extracts them somewhere it never looks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OGG_DIR="${1:-$ROOT/build/ogg}"
NAME="${2:-c3po}"
DIST="$ROOT/dist"

count=$(find "$OGG_DIR" -maxdepth 1 -name '*.ogg' | wc -l)
if [ "$count" -eq 0 ]; then
  echo "no .ogg files in $OGG_DIR — run encode.sh first" >&2
  exit 1
fi

mkdir -p "$DIST"
tar -czf "$DIST/$NAME.tar.gz" -C "$OGG_DIR" $(cd "$OGG_DIR" && ls *.ogg)

HASH=$(md5sum "$DIST/$NAME.tar.gz" | awk '{print $1}')
printf '%s\n' "$HASH" > "$DIST/HASH.txt"

echo "$count prompts -> $DIST/$NAME.tar.gz  ($(du -h "$DIST/$NAME.tar.gz" | cut -f1))"
echo "md5: $HASH"
