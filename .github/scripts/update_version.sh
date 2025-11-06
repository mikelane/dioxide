#!/bin/bash
set -e

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Updating version to $NEW_VERSION"

# Install cargo-edit if not present
if ! command -v cargo-set-version &> /dev/null; then
    cargo install cargo-edit
fi

# Update Cargo.toml (maturin reads from here)
cargo set-version "$NEW_VERSION"

echo "Version updated successfully"
