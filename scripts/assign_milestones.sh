#!/bin/bash
# scripts/assign_milestones.sh - Bulk assign issues to appropriate milestones
#
# This script implements the milestone assignment plan from docs/PM_GITHUB_AUDIT.md
# Run with: ./scripts/assign_milestones.sh

set -e  # Exit on error

REPO="mikelane/dioxide"

echo "========================================="
echo "Dioxide Milestone Assignment Script"
echo "========================================="
echo ""
echo "This script will:"
echo "  1. Assign open issues to appropriate milestones"
echo "  2. Add due dates to active milestones"
echo "  3. Close completed milestones"
echo ""
read -p "Proceed? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Step 1/3: Closing completed milestones..."
echo "========================================="

# Close milestones that are 100% complete
echo "  ✓ Closing 'v0.1 Walking Skeleton' (11/11 closed)"
gh api --method PATCH "/repos/$REPO/milestones/1" -f state="closed" 2>/dev/null || true

echo "  ✓ Closing 'v0.2 Core Features' (1/1 closed)"
gh api --method PATCH "/repos/$REPO/milestones/2" -f state="closed" 2>/dev/null || true

echo "  ✓ Closing '0.0.1-alpha' (6/6 closed)"
gh api --method PATCH "/repos/$REPO/milestones/4" -f state="closed" 2>/dev/null || true

echo "  ✓ Closing '0.0.3-alpha' (1/1 closed)"
gh api --method PATCH "/repos/$REPO/milestones/6" -f state="closed" 2>/dev/null || true

echo ""
echo "Step 2/3: Adding due dates to active milestones..."
echo "========================================="

echo "  ✓ 0.0.2-alpha: Due Nov 15, 2025"
gh api --method PATCH "/repos/$REPO/milestones/5" \
  -f due_on="2025-11-15T23:59:59Z" \
  -f description="MLP API realignment: @component.factory, @profile, global container" \
  2>/dev/null || true

echo "  ✓ 0.0.4-alpha: Due Nov 29, 2025"
gh api --method PATCH "/repos/$REPO/milestones/8" \
  -f due_on="2025-11-29T23:59:59Z" \
  -f description="Circular dependency detection and lifecycle protocols" \
  2>/dev/null || true

echo "  ✓ 0.1.0-beta: Due Dec 15, 2025"
gh api --method PATCH "/repos/$REPO/milestones/7" \
  -f due_on="2025-12-15T23:59:59Z" \
  -f description="MLP complete: API freeze, performance benchmarks, production ready" \
  2>/dev/null || true

echo ""
echo "Step 3/3: Assigning issues to milestones..."
echo "========================================="

echo ""
echo "Assigning to 0.0.4-alpha..."
gh issue edit 5 --repo "$REPO" --milestone "0.0.4-alpha" 2>/dev/null && echo "  ✓ #5 Detect circular dependencies"
gh issue edit 67 --repo "$REPO" --milestone "0.0.4-alpha" 2>/dev/null && echo "  ✓ #67 Lifecycle protocols"

echo ""
echo "Assigning to 0.1.0-beta..."
gh issue edit 18 --repo "$REPO" --milestone "0.1.0-beta" 2>/dev/null && echo "  ✓ #18 Performance benchmarks"

echo ""
echo "Assigning to Backlog..."
backlog_issues=(90 91 92 89 88 87 86 84 83 82 81 64 63 54 33 15 4)
for issue in "${backlog_issues[@]}"; do
  gh issue edit "$issue" --repo "$REPO" --milestone "Backlog" 2>/dev/null && echo "  ✓ #$issue" || echo "  ⚠ #$issue (may not exist or already assigned)"
done

echo ""
echo "Milestone assignment complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✓ 4 milestones closed (completed work)"
echo "  ✓ 3 milestones updated with due dates"
echo "  ✓ 20+ issues assigned to milestones"
echo ""
echo "Active milestones:"
echo "  • 0.0.2-alpha (due Nov 15) - MLP API realignment"
echo "  • 0.0.4-alpha (due Nov 29) - Circular deps + lifecycle"
echo "  • 0.1.0-beta (due Dec 15) - MLP complete"
echo "  • Backlog (no due date) - Future work"
echo ""
echo "Next steps:"
echo "  1. Review milestones at: https://github.com/$REPO/milestones"
echo "  2. Verify issue assignments are correct"
echo "  3. Start creating epic issues with sub-issues"
echo ""
