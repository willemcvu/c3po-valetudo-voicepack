#!/usr/bin/env python3
"""Thin ElevenLabs TTS helper shared by the sample and batch generators."""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io"

# eleven_v3 is the one that honours inline emotion tags like [anxious], which is
# what gives Threepio his exaggerated, panicky delivery. The older models flatten it.
DEFAULT_MODEL = "eleven_v3"


def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key.strip()
    return (ROOT / "elevenlabs_api_key.txt").read_text().strip()


def voices():
    """Saved C-3PO candidate voices, tag -> ElevenLabs voice_id.

    C2 is the one the pack ships; B1 and C1 were the other two finalists, kept
    so they can be swapped in without redoing the voice design.
    """
    return json.loads((ROOT / "voices.json").read_text())


def speak(text, voice_id, model=DEFAULT_MODEL, settings=None, key=None):
    """Synthesise `text` and return mp3 bytes."""
    body = {"text": text, "model_id": model}
    if settings:
        body["voice_settings"] = settings
    req = urllib.request.Request(
        f"{API}/v1/text-to-speech/{voice_id}",
        data=json.dumps(body).encode(),
        headers={
            "xi-api-key": key or api_key(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    return urllib.request.urlopen(req, timeout=180).read()


def design(description, text, key=None):
    """Generate voice-design previews. Returns [(generated_voice_id, mp3_bytes)]."""
    import base64

    req = urllib.request.Request(
        f"{API}/v1/text-to-voice/design",
        data=json.dumps(
            {"voice_description": description, "text": text, "auto_generate_text": False}
        ).encode(),
        headers={"xi-api-key": key or api_key(), "Content-Type": "application/json"},
    )
    data = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return [
        (p["generated_voice_id"], base64.b64decode(p["audio_base_64"]))
        for p in data["previews"]
    ]


def save_voice(name, generated_voice_id, description="", key=None):
    req = urllib.request.Request(
        f"{API}/v1/text-to-voice",
        data=json.dumps(
            {
                "voice_name": name,
                "voice_description": description or name,
                "generated_voice_id": generated_voice_id,
            }
        ).encode(),
        headers={"xi-api-key": key or api_key(), "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=120).read())["voice_id"]
