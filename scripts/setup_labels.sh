#!/bin/bash
# scripts/setup_labels.sh - Apply new label taxonomy to dioxide repository
#
# This script implements the label cleanup plan from docs/PM_GITHUB_AUDIT.md
# Run with: ./scripts/setup_labels.sh

set -e  # Exit on error

REPO="mikelane/dioxide"

echo "========================================="
echo "Dioxide Label Management Script"
echo "========================================="
echo ""
echo "This script will:"
echo "  1. Delete 21 deprecated/duplicate labels"
echo "  2. Create/update 25 well-organized labels"
echo "  3. Apply semantic color coding"
echo ""
read -p "Proceed? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Function to create/update label
create_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  echo "  ✓ $name"
  gh label create "$name" \
    --repo "$REPO" \
    --color "$color" \
    --description "$description" \
    --force 2>/dev/null || true  # Update if exists, ignore errors
}

# Function to delete label
delete_label() {
  local name="$1"

  echo "  ✗ $name"
  gh label delete "$name" --repo "$REPO" --yes 2>/dev/null || true  # Ignore if doesn't exist
}

echo ""
echo "Step 1/3: Deleting deprecated labels..."
echo "========================================="

delete_label "documentation"
delete_label "duplicate"
delete_label "enhancement"
delete_label "invalid"
delete_label "question"
delete_label "wontfix"
delete_label "type: story"
delete_label "type: documentation"
delete_label "type: enhancement"
delete_label "0.0.1-alpha"
delete_label "0.0.2-alpha"
delete_label "v0.2.0"
delete_label "critical"
delete_label "feature"
delete_label "python"
delete_label "rust"
delete_label "quality"
delete_label "testing"
delete_label "type-safety"
delete_label "ci-cd"
delete_label "devops"
delete_label "infrastructure"
delete_label "dx"
delete_label "breaking-change"
delete_label "area: ci-cd"  # Will recreate with correct format
delete_label "status: needs-review"  # Will recreate with correct format
delete_label "nice-to-have"
delete_label "example"
delete_label "ci"

echo ""
echo "Step 2/3: Creating TYPE labels..."
echo "========================================="

create_label "type: feature" "0E8A16" "New feature or enhancement"
create_label "type: bug" "D73A4A" "Bug or defect"
create_label "type: docs" "0075CA" "Documentation improvements"
create_label "type: task" "1D76DB" "Development task or chore"
create_label "type: test" "FBCA04" "Testing improvements"
create_label "type: spike" "9C27B0" "Research/investigation task"

echo ""
echo "Creating AREA labels..."
echo "========================================="

create_label "area: core" "D4C5F9" "Core container/DI logic"
create_label "area: python" "3776AB" "Python API layer"
create_label "area: rust" "DEA584" "Rust implementation"
create_label "area: ci-cd" "4A90E2" "CI/CD pipelines"
create_label "area: docs" "0075CA" "Documentation"
create_label "area: testing" "FBCA04" "Test infrastructure"
create_label "area: dx" "FF6B6B" "Developer experience"

echo ""
echo "Creating PRIORITY labels..."
echo "========================================="

create_label "priority: critical" "B60205" "Critical/breaking issues"
create_label "priority: high" "D93F0B" "High priority"
create_label "priority: medium" "FF9800" "Medium priority"
create_label "priority: low" "BFDADC" "Low priority"

echo ""
echo "Creating STATUS labels..."
echo "========================================="

create_label "status: blocked" "000000" "Blocked by other work"
create_label "status: needs-review" "FFA500" "Waiting for review"
create_label "status: needs-decision" "9C27B0" "Needs architecture/design decision"

echo ""
echo "Creating SCOPE labels..."
echo "========================================="

create_label "scope: breaking-change" "B60205" "Breaking API changes"
create_label "scope: mlp-core" "0E8A16" "Core MLP feature (v0.1.0-beta)"

echo ""
echo "Creating WORKFLOW labels..."
echo "========================================="

create_label "workflow: good-first-issue" "7057ff" "Good for newcomers"
create_label "workflow: help-wanted" "008672" "Extra attention needed"
create_label "workflow: post-mlp" "D4C5F9" "Deferred to post-MLP (v0.2.0+)"

echo ""
echo "Step 3/3: Cleanup complete!"
echo "========================================="
echo ""
echo "Label Summary:"
echo "  ✓ 6 TYPE labels created"
echo "  ✓ 7 AREA labels created"
echo "  ✓ 4 PRIORITY labels created"
echo "  ✓ 3 STATUS labels created"
echo "  ✓ 2 SCOPE labels created"
echo "  ✓ 3 WORKFLOW labels created"
echo "  ─────────────────────────"
echo "  ✓ 25 labels total"
echo ""
echo "Next steps:"
echo "  1. Review labels at: https://github.com/$REPO/labels"
echo "  2. Run ./scripts/assign_milestones.sh to bulk-assign milestones"
echo "  3. Update existing issues with new labels"
echo ""
