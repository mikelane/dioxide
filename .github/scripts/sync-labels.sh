#!/usr/bin/env bash
# sync-labels.sh - Synchronize GitHub labels with canonical definitions
# Usage: ./sync-labels.sh [--dry-run]

set -euo pipefail

REPO="mikelane/dioxide"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

# Label definitions: name|color|description
# Color format: 6-digit hex code (without #)
declare -a TYPE_LABELS=(
    "type: bug|d73a4a|Something isn't working"
    "type: feature|a2eeef|New feature or request"
    "type: enhancement|84b6eb|Improvement to existing feature"
    "type: docs|0075ca|Documentation improvements"
    "type: refactor|fbca04|Code restructuring without behavior change"
    "type: security|b60205|Security vulnerability or concern"
    "type: performance|5319e7|Performance optimization"
    "type: question|d876e3|Question or support request"
)

declare -a PRIORITY_LABELS=(
    "priority: critical|b60205|Blocking production, security vulnerability"
    "priority: high|ff9800|Important for next release"
    "priority: medium|fbca04|Should be addressed soon"
    "priority: low|bfdadc|Nice to have"
)

declare -a STATUS_LABELS=(
    "status: triage|ededed|Needs review and categorization"
    "status: blocked|000000|Cannot proceed, waiting on dependency"
    "status: in-progress|c2e0c6|Actively being worked on"
    "status: needs-review|1d76db|Implementation ready for review"
    "status: waiting-on-author|e99695|Waiting for issue author response"
    "status: stale|fef2c0|No activity for extended period"
)

declare -a AREA_LABELS=(
    "area: core|d4c5f9|Core container/graph implementation"
    "area: python|3776ab|Python bindings and API"
    "area: rust|dea584|Rust implementation"
    "area: api|c5def5|API design and endpoints"
    "area: cli|0e8a16|Command-line interface"
    "area: ui|7057ff|User interface"
    "area: infrastructure|ededed|CI/CD, deployment, infrastructure"
    "area: testing|fbca04|Test infrastructure and coverage"
    "area: lifecycle|d4c5f9|Lifecycle management"
)

declare -a META_LABELS=(
    "good-first-issue|7057ff|Good for newcomers"
    "help-wanted|008672|Extra attention needed"
    "duplicate|cfd3d7|Already reported elsewhere"
    "wontfix|ffffff|Will not be addressed"
    "needs-reproduction|fef2c0|Cannot reproduce the issue"
    "breaking-change|d73a4a|Will require major version bump"
    "dependencies|0366d6|Dependency updates"
)

# Function to create or update a label
sync_label() {
    local name="$1"
    local color="$2"
    local description="$3"

    if [[ "$DRY_RUN" == true ]]; then
        echo "  📝 Would sync: $name (#$color) - $description"
        return
    fi

    # Check if label exists
    if gh label list --repo "$REPO" --json name --jq '.[].name' | grep -Fxq "$name"; then
        # Update existing label
        gh label edit "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null || {
            echo "  ⚠️  Failed to update label: $name"
            return 1
        }
        echo "  ✓ Updated: $name"
    else
        # Create new label
        gh label create "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null || {
            echo "  ⚠️  Failed to create label: $name"
            return 1
        }
        echo "  + Created: $name"
    fi
}

# Function to process label array
process_labels() {
    local -n labels=$1
    local category=$2

    echo ""
    echo "📋 Processing $category labels..."
    for label_def in "${labels[@]}"; do
        IFS='|' read -r name color description <<< "$label_def"
        sync_label "$name" "$color" "$description"
    done
}

# Main execution
echo "🏷️  Synchronizing labels for $REPO"

process_labels TYPE_LABELS "Type"
process_labels PRIORITY_LABELS "Priority"
process_labels STATUS_LABELS "Status"
process_labels AREA_LABELS "Area"
process_labels META_LABELS "Meta"

echo ""
if [[ "$DRY_RUN" == true ]]; then
    echo "🔍 Dry run complete. Run without --dry-run to apply changes."
else
    echo "✅ Label synchronization complete!"
fi

echo ""
echo "📊 Current label count: $(gh label list --repo "$REPO" --json name --jq '. | length')"
