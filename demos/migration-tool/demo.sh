#!/usr/bin/env bash
# Migration Experience Demo — timing synced to narration segments
#
# Segment durations from ElevenLabs (see recordings/migration-tool_timing.json):
#   title:           3.7s
#   show_v1:         8.6s
#   upgrade_fails:   6.0s
#   show_migration:  8.5s
#   show_v2:         9.9s
#   tests_pass:      4.0s
#   closing:         6.8s
#   TOTAL:          47.6s
#
# Code display: bat (syntax highlighting) piped through pv (flowing output).
# At 2000 B/s, files display over ~0.6-2.8s depending on size + ANSI overhead.

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

# ── title (3.7s) ────────────────────────────────
echo -e "${BOLD}Migration Experience: rivet_di v1 → dioxide v2${RESET}"
echo -e "${DIM}A dioxide demo${RESET}"
sleep 3.7

# ── show_v1 (8.6s) ─────────────────────────────
# bat output: ~5580 bytes at 2000 B/s ≈ 2.8s display
echo -e "\n${BLUE}━━━ Your v1 app (rivet_di) ━━━${RESET}\n"
show_code "$DEMO_DIR/v1_app.py"
sleep 5.8

# ── upgrade_fails (6.0s) ────────────────────────
# python import attempt ~0.5s
echo -e "\n${RED}${BOLD}━━━ Upgrading to dioxide v2... ━━━${RESET}\n"
echo -e "${YELLOW}$ python -c \"from rivet_di import container\"${RESET}"
python -c "from rivet_di import container" 2>&1 || true
sleep 5.5

# ── show_migration (8.5s) ───────────────────────
# bat output: ~1209 bytes at 2000 B/s ≈ 0.6s display
echo -e "\n${BLUE}━━━ The migration guide ━━━${RESET}\n"
show_code "$DEMO_DIR/migration_diff.py"
sleep 7.9

# ── show_v2 (9.9s) ─────────────────────────────
# bat output: ~5436 bytes at 2000 B/s ≈ 2.7s display
echo -e "\n${BLUE}━━━ After migration (dioxide v2) ━━━${RESET}\n"
show_code "$DEMO_DIR/v2_app.py"
sleep 7.2

# ── tests_pass (4.0s) ──────────────────────────
# pytest ~0.8s
echo -e "\n${GREEN}${BOLD}━━━ Running tests... ━━━${RESET}\n"
cd "$DEMO_DIR"
python -m pytest test_v2_app.py -v --no-header --tb=no 2>&1 | tail -4
sleep 3.2

# ── closing (6.8s + buffer for GIF timing loss) ──
echo -e "\n${BOLD}We break APIs when we have to.${RESET}"
echo -e "${BOLD}But we never break your trust.${RESET}"
echo -e "${DIM}dioxide.readthedocs.io${RESET}\n"
sleep 10.3
