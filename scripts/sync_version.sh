#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VERSION=$1

# Update Cargo.toml
cargo set-version "$VERSION"

# Maturin will read version from Cargo.toml automatically
echo "Version synchronized to $VERSION"
