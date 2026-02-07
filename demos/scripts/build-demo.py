#!/usr/bin/env python3
"""Build a narration-synced demo video from a segmented narration script.

Narration-driven recording: generates audio first, measures durations,
then builds a demo script with sleep values that match each segment.

Usage:
    python scripts/build-demo.py <narration-script.md> <demo-name>

Flow:
    1. Parse narration script into labeled segments
    2. Generate audio for each segment via ElevenLabs
    3. Measure each clip's duration with ffprobe
    4. Write timing JSON file
    5. Concatenate clips into one narration track
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def parse_segments(script_path: Path) -> list[dict[str, str]]:
    """Parse a narration script into labeled segments."""
    content = script_path.read_text()
    segments: list[dict[str, str]] = []

    pattern = re.compile(r"<!--\s*SEGMENT:\s*(\w+)\s*-->\s*\n(.*?)(?=<!--\s*SEGMENT:|\Z)", re.DOTALL)

    for match in pattern.finditer(content):
        name = match.group(1)
        text = match.group(2).strip()
        if text:
            segments.append({"name": name, "text": text})

    return segments


def generate_segment_audio(
    text: str, output_path: Path, api_key: str, voice_id: str
) -> None:
    """Generate audio for a single narration segment."""
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
        with urlopen(request) as response:  # noqa: S310
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.read())
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"  ElevenLabs API error (HTTP {exc.code}): {body}", file=sys.stderr)
        sys.exit(1)


def get_audio_duration(path: Path) -> float:
    """Get duration of an audio file in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def concatenate_audio(clip_paths: list[Path], output_path: Path) -> None:
    """Concatenate audio clips into a single file using ffmpeg."""
    list_file = output_path.parent / "concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in clip_paths)
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(output_path)],
        capture_output=True, check=True,
    )
    list_file.unlink()


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <narration-script.md> <demo-name>", file=sys.stderr)
        sys.exit(1)

    script_path = Path(sys.argv[1])
    demo_name = sys.argv[2]

    if not script_path.exists():
        print(f"Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    if not api_key or not voice_id:
        print("ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID required", file=sys.stderr)
        sys.exit(1)
    if not re.fullmatch(r"[A-Za-z0-9]+", voice_id):
        print("ELEVENLABS_VOICE_ID must be alphanumeric", file=sys.stderr)
        sys.exit(1)

    demos_dir = Path(__file__).resolve().parent.parent
    clips_dir = demos_dir / "recordings" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Parse segments
    segments = parse_segments(script_path)
    if not segments:
        print("No segments found in script", file=sys.stderr)
        sys.exit(1)
    print(f"Found {len(segments)} narration segments")

    # Step 2: Generate audio for each segment
    timing: list[dict[str, float | str]] = []
    clip_paths: list[Path] = []

    for seg in segments:
        clip_path = clips_dir / f"{demo_name}_{seg['name']}.mp3"
        print(f"  Generating: {seg['name']} ({len(seg['text'])} chars)")
        generate_segment_audio(seg["text"], clip_path, api_key, voice_id)

        # Step 3: Measure duration
        duration = get_audio_duration(clip_path)
        print(f"    Duration: {duration:.1f}s")

        timing.append({
            "name": seg["name"],
            "text": seg["text"],
            "duration": round(duration, 2),
            "clip": str(clip_path.name),
        })
        clip_paths.append(clip_path)

    # Step 4: Write timing JSON
    timing_path = demos_dir / "recordings" / f"{demo_name}_timing.json"
    timing_path.write_text(json.dumps(timing, indent=2))
    print(f"\nTiming written to {timing_path}")

    total = sum(t["duration"] for t in timing)
    print(f"Total narration: {total:.1f}s")

    # Step 5: Concatenate into one narration track
    narration_path = demos_dir / "recordings" / f"{demo_name}-narration.mp3"
    concatenate_audio(clip_paths, narration_path)
    print(f"Combined narration: {narration_path}")

    # Print timing summary for demo script generation
    print("\n--- Segment Timing (use for demo.sh sleep values) ---")
    for t in timing:
        print(f"  {t['name']:20s}  {t['duration']:5.1f}s  \"{t['text'][:60]}...\"")


if __name__ == "__main__":
    main()
