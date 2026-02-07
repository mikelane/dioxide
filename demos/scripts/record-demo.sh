#!/usr/bin/env bash
#
# Record a terminal demo using asciinema.
#
# Usage: ./scripts/record-demo.sh <demo-name>
#
# This creates a .cast file in recordings/ with standardized settings
# for consistent demo recordings across all dioxide demos.

set -euo pipefail

DEMO_NAME="${1:?Usage: $0 <demo-name>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEMOS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RECORDINGS_DIR="${DEMOS_DIR}/recordings"

COLS=120
ROWS=35
IDLE_LIMIT=2

mkdir -p "${RECORDINGS_DIR}"

OUTPUT_FILE="${RECORDINGS_DIR}/${DEMO_NAME}.cast"

if [[ -f "${OUTPUT_FILE}" ]]; then
    echo "Recording already exists: ${OUTPUT_FILE}"
    echo "Delete it first or choose a different name."
    exit 1
fi

echo "=== Dioxide Demo Recording ==="
echo ""
echo "  Demo:     ${DEMO_NAME}"
echo "  Output:   ${OUTPUT_FILE}"
echo "  Terminal: ${COLS}x${ROWS}"
echo "  Idle max: ${IDLE_LIMIT}s"
echo ""
echo "Tips:"
echo "  - Use a clean shell prompt (e.g., '$ ')"
echo "  - Type slowly and deliberately for clarity"
echo "  - Pause briefly after each command output"
echo "  - Press Ctrl+D or type 'exit' to stop recording"
echo ""
echo "Starting recording in 3 seconds..."
sleep 3

asciinema rec \
    --cols "${COLS}" \
    --rows "${ROWS}" \
    --idle-time-limit "${IDLE_LIMIT}" \
    "${OUTPUT_FILE}"

echo ""
echo "Recording saved: ${OUTPUT_FILE}"
echo ""
echo "Next steps:"
echo "  1. Preview:  asciinema play ${OUTPUT_FILE}"
echo "  2. Convert:  agg --theme dracula ${OUTPUT_FILE} ${RECORDINGS_DIR}/${DEMO_NAME}.gif"
echo "  3. To MP4:   ffmpeg -i ${RECORDINGS_DIR}/${DEMO_NAME}.gif -movflags faststart -pix_fmt yuv420p ${RECORDINGS_DIR}/${DEMO_NAME}.mp4"
