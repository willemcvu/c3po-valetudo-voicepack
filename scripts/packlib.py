#!/usr/bin/env python3
"""Shared helpers for the multi-pack build.

Each voice pack lives in packs/<name>/ and is a self-contained Python module
packs/<name>/pack.py exposing:

    META      dict: name, language_code, voice_tag, profile, description
    SKIP      dict: sound_id -> reason (no TTS; stock audio kept)
    REWRITES  dict: sound_id -> line text for that character

The stock prompt inventory (stock_lines.csv) is shared across every pack, since
it only depends on the robot, not the character.
"""
import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKS = ROOT / "packs"
STOCK_CSV = ROOT / "stock_lines.csv"


def pack_dir(name):
    d = PACKS / name
    if not (d / "pack.py").exists():
        sys.exit(f"no pack '{name}' (expected {d/'pack.py'})")
    return d


def load_pack(name):
    """Import packs/<name>/pack.py and return the module."""
    path = pack_dir(name) / "pack.py"
    spec = importlib.util.spec_from_file_location(f"pack_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def list_packs():
    return sorted(p.name for p in PACKS.iterdir() if (p / "pack.py").exists())


def stock_lines():
    """Shared stock inventory as a list of dict rows."""
    return list(csv.DictReader(STOCK_CSV.open()))


def arg_pack(argv, flag_index=1):
    """Resolve the pack name from argv, erroring helpfully if missing/unknown."""
    packs = list_packs()
    if len(argv) <= flag_index:
        sys.exit(f"usage: {Path(argv[0]).name} <pack>\navailable: {', '.join(packs)}")
    name = argv[flag_index]
    if name not in packs:
        sys.exit(f"unknown pack '{name}'\navailable: {', '.join(packs)}")
    return name
