#!/bin/bash
# Live-reload documentation server for local development
#
# Usage:
#   ./scripts/docs-serve.sh [--no-open]
#
# Features:
#   - Auto-rebuilds on changes to docs/, python/dioxide/ files
#   - Live reloads browser on rebuild
#   - Opens browser automatically (use --no-open to disable)
#   - Serves at http://localhost:8000
#
# Requirements:
#   uv sync --group docs

set -euo pipefail

# Default: open browser
OPEN_BROWSER="--open-browser"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --no-open)
            OPEN_BROWSER=""
            shift
            ;;
    esac
done

echo "Starting documentation server with live reload..."
echo "Watching: docs/, python/dioxide/"
echo "Server: http://localhost:8000"
echo ""

uv run sphinx-autobuild docs docs/_build/html \
    --port 8000 \
    $OPEN_BROWSER \
    --watch python/dioxide \
    --ignore "*.pyc" \
    --ignore "__pycache__" \
    --ignore ".git" \
    --ignore "docs/_build"
