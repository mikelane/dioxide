#!/usr/bin/env bash
# Mock-to-Fake Migration Demo — timing synced to narration segments
#
# Segment durations from ElevenLabs (see recordings/mock-to-fake_timing.json):
#   title:           4.4s
#   show_service:    6.4s
#   show_mock_test:  7.2s
#   explain_refactor:10.2s
#   mock_breaks:     11.5s
#   show_dioxide:    9.7s
#   show_fake_test:  5.9s
#   fake_survives:   4.8s
#   closing:         4.0s
#   TOTAL:          64.0s
#
# Code display: bat (syntax highlighting) piped through pv (flowing output).
# At 2000 B/s, files display over ~1.7-2.7s depending on size + ANSI overhead.

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

# ── title (4.4s) ────────────────────────────────
echo -e "${BOLD}Mock → Fake: Why Fakes Survive Refactoring${RESET}"
echo -e "${DIM}A dioxide demo${RESET}"
sleep 4.4

# ── show_service (6.4s) ─────────────────────────
# bat output: ~3743 bytes at 2000 B/s ≈ 1.9s display
echo -e "\n${BLUE}━━━ A service coupled to smtplib ━━━${RESET}\n"
show_code "$DEMO_DIR/before/app.py"
sleep 4.5

# ── show_mock_test (7.2s) ───────────────────────
# bat output: ~3312 bytes at 2000 B/s ≈ 1.7s display + pytest ~0.8s
echo -e "\n${BLUE}━━━ Its mock-based test ━━━${RESET}\n"
show_code "$DEMO_DIR/before/test_app.py"
echo ""
cd "$DEMO_DIR/before"
python -m pytest test_app.py -v --no-header --tb=no 2>&1 | tail -3
sleep 4.7

# ── explain_refactor (10.2s) ────────────────────
# bat output: ~4180 bytes at 2000 B/s ≈ 2.1s display
echo -e "\n${BLUE}━━━ Refactoring: SMTP → HTTP API ━━━${RESET}\n"
echo -e "${YELLOW}Same behavior, different transport:${RESET}\n"
show_code "$DEMO_DIR/after/app.py"
sleep 8.1

# ── mock_breaks (11.5s) ─────────────────────────
# pytest ~0.8s
echo -e "\n${RED}${BOLD}━━━ Running mock test against refactored code... ━━━${RESET}\n"
cd "$DEMO_DIR/after"
python -m pytest test_app.py -v --tb=short 2>&1 | tail -12 || true
sleep 10.7

# ── show_dioxide (9.7s) ─────────────────────────
# bat output: ~3696 bytes at 2000 B/s ≈ 1.8s display
echo -e "\n${BLUE}━━━ The dioxide way: depend on ports ━━━${RESET}\n"
show_code "$DEMO_DIR/before/dioxide_app.py"
sleep 7.9

# ── show_fake_test (5.9s) ───────────────────────
# bat output: ~5366 bytes at 2000 B/s ≈ 2.7s display
echo -e "\n${BLUE}━━━ Test with a fake ━━━${RESET}\n"
show_code "$DEMO_DIR/before/test_dioxide_app.py"
sleep 3.2

# ── fake_survives (4.8s) ────────────────────────
# pytest ~0.8s
echo -e "\n${GREEN}${BOLD}━━━ Same refactoring. Same test. ━━━${RESET}\n"
cd "$DEMO_DIR/after"
python -m pytest test_dioxide_app.py -v --no-header --tb=no 2>&1 | tail -3
sleep 4.0

# ── closing (4.0s + buffer for GIF timing loss) ──
echo -e "\n${BOLD}Mocks couple to HOW.  Fakes couple to WHAT.${RESET}"
echo -e "${DIM}dioxide.readthedocs.io${RESET}\n"
sleep 8.0
