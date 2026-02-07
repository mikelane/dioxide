#!/usr/bin/env bash
# Scan Performance Demo — timing synced to narration segments
#
# Segment durations from ElevenLabs (see recordings/scan-performance_timing.json):
#   title:           6.2s
#   show_adapters:   8.2s
#   eager_scan:      8.1s
#   run_eager:       4.9s
#   lazy_intro:      6.7s
#   run_lazy:        4.8s
#   first_resolve:   6.3s
#   closing:         2.6s
#   TOTAL:          47.8s
#
# Code display: bat (syntax highlighting) piped through pv (flowing output).
# At 2000 B/s, files display over ~0.8-1.8s depending on size + ANSI overhead.

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$DEMO_DIR/../.." && pwd)"
PYTHON="$REPO_DIR/.venv/bin/python"
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

# ── title (6.2s) ──────────────────────────────────
echo -e "${BOLD}Scan Performance: Eager vs Lazy${RESET}"
echo -e "${DIM}A dioxide demo${RESET}"
sleep 6.2

# ── show_adapters (8.2s) ──────────────────────────
# bat output: ~2129 bytes at 2000 B/s ≈ 1.1s display
echo -e "\n${BLUE}━━━ An adapter with an expensive import ━━━${RESET}\n"
show_code "$DEMO_DIR/myapp/adapters/email.py"
sleep 7.1

# ── eager_scan (8.1s) ─────────────────────────────
# bat output: ~1690 bytes at 2000 B/s ≈ 0.85s display
echo -e "\n${BLUE}━━━ Eager scan: import everything upfront ━━━${RESET}\n"
show_code "$DEMO_DIR/eager_scan.py"
sleep 7.2

# ── run_eager (4.9s) ──────────────────────────────
# Python execution: ~1.3s (3 x 0.4s sleeps + overhead)
echo -e "\n${RED}${BOLD}━━━ Running eager scan... ━━━${RESET}\n"
cd "$DEMO_DIR"
PYTHONPATH="$DEMO_DIR" "$PYTHON" eager_scan.py
sleep 3.6

# ── lazy_intro (6.7s) ─────────────────────────────
# bat output: ~3588 bytes at 2000 B/s ≈ 1.8s display
echo -e "\n${BLUE}━━━ Lazy scan: defer imports until needed ━━━${RESET}\n"
show_code "$DEMO_DIR/lazy_scan.py"
sleep 4.9

# ── run_lazy (4.8s) ───────────────────────────────
# Python execution: ~0.5s (lazy scan + resolve one adapter)
echo -e "\n${GREEN}${BOLD}━━━ Running lazy scan... ━━━${RESET}\n"
cd "$DEMO_DIR"
PYTHONPATH="$DEMO_DIR" "$PYTHON" lazy_scan.py
sleep 4.3

# ── first_resolve (6.3s) ──────────────────────────
echo -e "\n${YELLOW}━━━ Eager: 1.2s for all 3 adapters${RESET}"
echo -e "${GREEN}${BOLD}━━━ Lazy:  0.001s scan + 0.4s for the one you need${RESET}\n"
sleep 6.3

# ── closing (2.6s + buffer for GIF timing loss) ──
echo -e "\n${BOLD}Lazy scanning: load what you need, when you need it.${RESET}"
echo -e "${DIM}dioxide.readthedocs.io${RESET}\n"
sleep 6.6
