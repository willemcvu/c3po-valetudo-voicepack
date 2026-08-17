#!/usr/bin/env bash
# Serve the pack over HTTP and tell the robot to fetch it.
#
#   ./install.sh [tar.gz] [robot-ip]
#
# The robot downloads the archive itself, verifies the MD5, and extracts to
# /data/personalized_voice/<LANGUAGE_CODE>/. The HTTP server only needs to live
# long enough for that one fetch.
#
# To revert: set the language back to "EN" in Valetudo (Robot Settings -> Misc),
# or PUT {"action":"download", ...} with a stock pack. The factory prompts in
# /audio/EN are never touched.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK="${1:-$ROOT/dist/c3po.tar.gz}"
ROBOT="${2:-192.168.68.78}"
LANG_CODE="${LANG_CODE:-C3PO}"
PORT="${PORT:-8123}"

[ -f "$PACK" ] || { echo "no pack at $PACK — run package.sh first" >&2; exit 1; }

# Pick the interface that actually routes to the robot, so we advertise a URL
# the robot can reach rather than whichever address happens to be first.
HOST_IP=$(ip route get "$ROBOT" | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')
[ -n "$HOST_IP" ] || { echo "could not determine local IP toward $ROBOT" >&2; exit 1; }

HASH=$(md5sum "$PACK" | awk '{print $1}')
URL="http://${HOST_IP}:${PORT}/$(basename "$PACK")"

echo "pack     $PACK ($(du -h "$PACK" | cut -f1))"
echo "md5      $HASH"
echo "url      $URL"
echo "language $LANG_CODE"
echo

python3 -m http.server "$PORT" --bind "$HOST_IP" --directory "$(dirname "$PACK")" >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
sleep 1

curl -fsS -X PUT -H "Content-Type: application/json" \
  -d "{\"action\":\"download\",\"url\":\"$URL\",\"hash\":\"$HASH\",\"language\":\"$LANG_CODE\"}" \
  "http://${ROBOT}/api/v2/robot/capabilities/VoicePackManagementCapability"
echo "request accepted; waiting for the robot to fetch and install"

for _ in $(seq 1 60); do
  sleep 5
  STATUS=$(curl -fsS "http://${ROBOT}/api/v2/robot/capabilities/VoicePackManagementCapability" \
           | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["operationStatus"]["type"], d.get("currentLanguage",""))')
  echo "  $STATUS"
  case "$STATUS" in
    idle*)  [ -n "${SEEN:-}" ] && { echo "install finished"; exit 0; } ;;
    error*) echo "robot reported an error" >&2; exit 1 ;;
    *)      SEEN=1 ;;
  esac
done

echo "timed out waiting for the robot" >&2
exit 1
