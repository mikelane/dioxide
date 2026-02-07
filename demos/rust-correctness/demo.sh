#!/usr/bin/env bash
# Rust Backend Correctness Demo — timing synced to narration segments
#
# Segment durations from ElevenLabs (see recordings/rust-correctness_timing.json):
#   title:           7.8s
#   show_missing:    7.8s
#   run_missing:    10.2s
#   show_circular:   7.8s
#   run_circular:   11.8s
#   show_correct:    7.7s
#   closing:         3.9s
#   TOTAL:          56.9s
#
# Code display: bat (syntax highlighting) piped through pv (flowing output).
# At 2000 B/s, files display over ~2.4-3.5s depending on size + ANSI overhead.

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'

# Display code with syntax highlighting and flowing output
show_code() {
    bat --style=plain --theme="Monokai Extended" --language=python --color=always "$1" \
        | pv -qL 2000
}

clear

# -- title (7.8s) --
echo -e "${BOLD}Rust Backend Correctness Guarantees${RESET}"
echo -e "${DIM}A dioxide demo${RESET}"
sleep 7.8

# -- show_missing (7.8s) --
# bat output: ~4779 bytes at 2000 B/s = ~2.4s display
echo -e "\n${BLUE}--- Missing Binding ---${RESET}\n"
show_code "$DEMO_DIR/missing_binding.py"
sleep 5.4

# -- run_missing (10.2s) --
# python ~0.8s
echo -e "\n${RED}${BOLD}--- Running... ---${RESET}\n"
python3 "$DEMO_DIR/missing_binding.py" 2>&1 | tail -8 || true
sleep 9.4

# -- show_circular (7.8s) --
# bat output: ~4863 bytes at 2000 B/s = ~2.4s display
echo -e "\n${BLUE}--- Circular Dependency ---${RESET}\n"
show_code "$DEMO_DIR/circular_dep.py"
sleep 5.4

# -- run_circular (11.8s) --
# python ~0.8s
echo -e "\n${RED}${BOLD}--- Running... ---${RESET}\n"
python3 "$DEMO_DIR/circular_dep.py" 2>&1 | tail -8 || true
sleep 11.0

# -- show_correct (7.7s) --
# bat output: ~6926 bytes at 2000 B/s = ~3.5s display + python ~0.1s
echo -e "\n${GREEN}${BOLD}--- Correct Wiring ---${RESET}\n"
show_code "$DEMO_DIR/correct_wiring.py"
echo ""
python3 "$DEMO_DIR/correct_wiring.py" 2>&1
sleep 4.1

# -- closing (3.9s + buffer for GIF timing loss) --
echo -e "\n${BOLD}Fail fast. Fail at startup. Powered by Rust.${RESET}"
echo -e "${DIM}dioxide.readthedocs.io${RESET}\n"
sleep 7.9
