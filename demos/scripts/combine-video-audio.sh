#!/usr/bin/env bash
#
# Combine a terminal recording MP4 with narration audio.
#
# Usage: ./scripts/combine-video-audio.sh <video.mp4> <audio.mp3> <output.mp4>
#
# This overlays narration audio onto the terminal recording video.
# The -shortest flag truncates the output to match the shorter stream.

set -euo pipefail

VIDEO_INPUT="${1:?Usage: $0 <video.mp4> <audio.mp3> <output.mp4>}"
AUDIO_INPUT="${2:?Usage: $0 <video.mp4> <audio.mp3> <output.mp4>}"
OUTPUT="${3:?Usage: $0 <video.mp4> <audio.mp3> <output.mp4>}"

if [[ ! -f "${VIDEO_INPUT}" ]]; then
    echo "Video file not found: ${VIDEO_INPUT}"
    exit 1
fi

if [[ ! -f "${AUDIO_INPUT}" ]]; then
    echo "Audio file not found: ${AUDIO_INPUT}"
    exit 1
fi

OUTPUT_DIR="$(dirname "${OUTPUT}")"
mkdir -p "${OUTPUT_DIR}"

echo "=== Combining Video + Audio ==="
echo ""
echo "  Video: ${VIDEO_INPUT}"
echo "  Audio: ${AUDIO_INPUT}"
echo "  Output: ${OUTPUT}"
echo ""

ffmpeg -y \
    -i "${VIDEO_INPUT}" \
    -i "${AUDIO_INPUT}" \
    -c:v copy \
    -c:a aac \
    -b:a 192k \
    -shortest \
    -movflags +faststart \
    "${OUTPUT}"

echo ""
echo "Output saved: ${OUTPUT}"
echo "File size: $(du -h "${OUTPUT}" | cut -f1)"
