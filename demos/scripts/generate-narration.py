#!/usr/bin/env python3
"""Generate narration audio from a markdown script using the ElevenLabs API.

Usage:
    python scripts/generate-narration.py <script.md> <output.mp3>

Environment variables:
    ELEVENLABS_API_KEY   Your ElevenLabs API key (required)
    ELEVENLABS_VOICE_ID  Voice ID to use for synthesis (required)

The script reads a narration markdown file and extracts text blocks
(ignoring timing markers and headings), then sends the combined text
to the ElevenLabs text-to-speech API.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import (
    Request,
    urlopen,
)


def extract_narration_text(script_path: Path) -> str:
    """Extract plain narration text from a markdown script file.

    Strips timing markers like [00:00], headings, code blocks, and
    metadata lines, keeping only the narration paragraphs.
    """
    content = script_path.read_text()
    lines = content.splitlines()

    narration_lines: list[str] = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        if stripped.startswith("#"):
            continue

        if stripped.startswith("---"):
            continue

        cleaned = re.sub(r"\[[\d:]+\]\s*", "", stripped)
        cleaned = re.sub(r"\*\*.*?\*\*:\s*", "", cleaned)

        if cleaned:
            narration_lines.append(cleaned)

    return " ".join(narration_lines)


def generate_audio(text: str, output_path: Path, api_key: str, voice_id: str) -> None:
    """Send text to ElevenLabs API and save the resulting audio."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    payload = json.dumps({
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    })

    request = Request(
        url,
        data=payload.encode("utf-8"),
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request) as response:  # noqa: S310 — URL is hardcoded to https://api.elevenlabs.io; voice_id is validated alphanumeric
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.read())
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"ElevenLabs API error (HTTP {exc.code}): {body}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <script.md> <output.mp3>", file=sys.stderr)
        sys.exit(1)

    script_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not script_path.exists():
        print(f"Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ELEVENLABS_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    if not voice_id:
        print("ELEVENLABS_VOICE_ID environment variable is required", file=sys.stderr)
        sys.exit(1)

    if not re.fullmatch(r"[A-Za-z0-9]+", voice_id):
        print("ELEVENLABS_VOICE_ID must contain only alphanumeric characters", file=sys.stderr)
        sys.exit(1)

    narration_text = extract_narration_text(script_path)

    if not narration_text.strip():
        print("No narration text found in script", file=sys.stderr)
        sys.exit(1)

    print(f"Extracted {len(narration_text)} characters of narration text")
    print(f"Generating audio with voice {voice_id}...")

    generate_audio(narration_text, output_path, api_key, voice_id)

    print(f"Audio saved to {output_path}")


if __name__ == "__main__":
    main()
