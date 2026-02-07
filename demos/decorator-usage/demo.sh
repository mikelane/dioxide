#!/usr/bin/env bash
# Decorator Usage Demo — timing synced to narration segments
#
# Segment durations from ElevenLabs (see recordings/decorator-usage_timing.json):
#   title:              5.3s
#   show_ports:         8.3s
#   show_service:       8.7s
#   show_prod_adapters: 12.7s
#   show_test_adapters:  7.7s
#   run_prod:            7.7s
#   run_test:            8.0s
#   closing:             7.5s
#   TOTAL:              66.0s
#
# Code display: bat (syntax highlighting) piped through pv (flowing output).
# At 2000 B/s, files display over ~1.0-2.4s depending on size + ANSI overhead.

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

# ── title (5.3s) ─────────────────────────────────
echo -e "${BOLD}Two Decorators, One Rule${RESET}"
echo -e "${DIM}A dioxide demo${RESET}"
sleep 5.3

# ── show_ports (8.3s) ────────────────────────────
# bat output: ~2121 bytes at 2000 B/s ≈ 1.0s display
echo -e "\n${BLUE}━━━ The ports: what your app needs ━━━${RESET}\n"
show_code "$DEMO_DIR/ports.py"
sleep 7.3

# ── show_service (8.7s) ──────────────────────────
# bat output: ~3585 bytes at 2000 B/s ≈ 1.7s display
echo -e "\n${BLUE}━━━ @service — business logic (never changes) ━━━${RESET}\n"
show_code "$DEMO_DIR/service.py"
sleep 7.0

# ── show_prod_adapters (12.7s) ───────────────────
# bat output: ~3597 bytes at 2000 B/s ≈ 1.7s display
echo -e "\n${BLUE}━━━ @adapter.for_() — production infrastructure ━━━${RESET}\n"
show_code "$DEMO_DIR/adapters_prod.py"
sleep 11.0

# ── show_test_adapters (7.7s) ────────────────────
# bat output: ~4963 bytes at 2000 B/s ≈ 2.4s display
echo -e "\n${BLUE}━━━ @adapter.for_() — test fakes ━━━${RESET}\n"
show_code "$DEMO_DIR/adapters_test.py"
sleep 5.3

# ── run_prod (7.7s) ──────────────────────────────
# bat output: ~2189 bytes at 2000 B/s ≈ 1.0s display + command ~0.8s
echo -e "\n${GREEN}${BOLD}━━━ Production profile ━━━${RESET}\n"
show_code "$DEMO_DIR/run_prod.py"
echo ""
cd "$DEMO_DIR"
uv run python run_prod.py
sleep 5.9

# ── run_test (8.0s) ──────────────────────────────
# bat output: ~3613 bytes at 2000 B/s ≈ 1.8s display + command ~0.8s
echo -e "\n${YELLOW}${BOLD}━━━ Test profile ━━━${RESET}\n"
show_code "$DEMO_DIR/run_test.py"
echo ""
cd "$DEMO_DIR"
uv run python run_test.py
sleep 5.4

# ── closing (7.5s + 8.5s buffer for GIF frame rounding loss) ──
echo -e "\n${BOLD}@service for logic.  @adapter.for_() for infrastructure.${RESET}"
echo -e "${DIM}dioxide.readthedocs.io${RESET}\n"
sleep 16.0
