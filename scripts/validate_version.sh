#!/usr/bin/env bash
# Validate that Cargo.toml version matches git tag
# This script mimics the CI validation logic for local testing

set -euo pipefail

# Get version from Cargo.toml
CARGO_VERSION=$(grep '^version = ' Cargo.toml | head -1 | cut -d'"' -f2)

# Get version from git tag (if on a tag)
if git describe --exact-match --tags HEAD 2>/dev/null; then
    GIT_TAG=$(git describe --exact-match --tags HEAD)
    TAG_VERSION="${GIT_TAG#v}"  # Remove 'v' prefix

    echo "Cargo.toml version: $CARGO_VERSION"
    echo "Git tag version:    $TAG_VERSION"

    if [ "$CARGO_VERSION" != "$TAG_VERSION" ]; then
        echo ""
        echo "❌ ERROR: Version mismatch detected!"
        echo ""
        echo "  Cargo.toml:  $CARGO_VERSION"
        echo "  Git tag:     $TAG_VERSION"
        echo ""
        echo "This mismatch would cause building the wrong version."
        echo "Please update Cargo.toml to match the git tag before releasing."
        echo ""
        echo "To fix:"
        echo "  1. Update version in Cargo.toml to $TAG_VERSION"
        echo "  2. Commit the change"
        echo "  3. Move the git tag: git tag -f $GIT_TAG"
        echo "  4. Force push the tag: git push -f origin $GIT_TAG"
        exit 1
    fi

    echo "✅ Version validation passed: $CARGO_VERSION"
else
    echo "Not on a git tag, skipping version validation"
    echo "Current Cargo.toml version: $CARGO_VERSION"
fi
