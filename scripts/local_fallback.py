#!/usr/bin/env python3
"""
local_fallback.py — offline TTS for podcast-this-tech-stuff.

Claude writes the calibrated two-host script (it can Read PDF/PNG/text directly).
This script ONLY turns that script into audio: macOS `say` per speaker -> stitch
with stdlib `wave` -> compact .m4a via `afconvert`. No paid APIs, no ffmpeg.

Script file format: one line per spoken turn, prefixed "A:" or "B:".

Usage:
  python3 local_fallback.py <script.txt> <episode-slug>

Env overrides:
  PTTS_VOICE_A (default Samantha)  PTTS_VOICE_B (default Daniel)
  PTTS_RATE    (default 178 wpm)
"""

import os
import re
import sys
import wave
import shutil
import tempfile
import subprocess
from pathlib import Path

VOICE_A = os.environ.get("PTTS_VOICE_A", "Samantha")
VOICE_B = os.environ.get("PTTS_VOICE_B", "Daniel")
RATE = os.environ.get("PTTS_RATE", "178")
DATA_FORMAT = "LEI16@22050"  # uniform PCM so segments concat cleanly
EPISODES = Path.home() / "doc2podcast" / "episodes"


def die(msg: str) -> None:
    print(f"[local_fallback] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_script(path: Path) -> list[tuple[str, str]]:
    segs: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([AB])\s*[:\-]\s*(.+?)\s*$", line)
        if m:
            segs.append((m.group(1), m.group(2)))
    if not segs:
        die(f"No 'A:'/'B:' lines found in {path}")
    return segs


def synth(voice: str, text: str, out_wav: Path, txt_tmp: Path) -> None:
    txt_tmp.write_text(text, encoding="utf-8")
    r = subprocess.run(
        ["say", "-v", voice, "-r", RATE, "-f", str(txt_tmp),
         "-o", str(out_wav), "--data-format=" + DATA_FORMAT],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        die(f"`say` failed for voice {voice}: {r.stderr.strip()}")


def concat(wavs: list[Path], dest: Path) -> None:
    with wave.open(str(wavs[0]), "rb") as w0:
        params = w0.getparams()
    with wave.open(str(dest), "wb") as out:
        out.setparams(params)
        for wp in wavs:
            with wave.open(str(wp), "rb") as w:
                out.writeframes(w.readframes(w.getnframes()))


def to_m4a(src: Path, dest: Path) -> None:
    r = subprocess.run(
        ["afconvert", str(src), str(dest), "-f", "m4af", "-d", "aac",
         "-b", "64000"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        die(f"afconvert failed: {r.stderr.strip()}")


def main() -> None:
    if len(sys.argv) != 3:
        die("Usage: python3 local_fallback.py <script.txt> <episode-slug>")
    for tool in ("say", "afconvert"):
        if shutil.which(tool) is None:
            die(f"Required tool missing: {tool}")

    script_path = Path(sys.argv[1]).expanduser()
    if not script_path.is_file():
        die(f"Script file not found: {script_path}")
    slug = re.sub(r"[^\w.-]+", "-", sys.argv[2]).strip("-") or "episode"

    segs = parse_script(script_path)
    EPISODES.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        txt_tmp = tdp / "seg.txt"
        wavs: list[Path] = []
        for i, (spk, text) in enumerate(segs):
            wp = tdp / f"s{i:04d}.wav"
            synth(VOICE_A if spk == "A" else VOICE_B, text, wp, txt_tmp)
            wavs.append(wp)
            if (i + 1) % 10 == 0 or i + 1 == len(segs):
                print(f"[local_fallback] voiced {i + 1}/{len(segs)}")
        merged = tdp / "merged.wav"
        concat(wavs, merged)
        out = EPISODES / f"{slug}.m4a"
        to_m4a(merged, out)

    size_mb = out.stat().st_size / 1e6
    print(f"[local_fallback] done -> {out} ({size_mb:.1f} MB)  "
          f"voices A={VOICE_A} B={VOICE_B} rate={RATE}wpm")


if __name__ == "__main__":
    main()
