#!/bin/bash
# Build script for Autonomous Git

set -e

echo "🦀 Building Autonomous Git..."
echo

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed"
    echo "Install from: https://rustup.rs/"
    exit 1
fi

echo "📦 Building release binary..."
cargo build --release

echo
echo "✅ Build complete!"
echo
echo "Binary location: target/release/agit"
echo "Size: $(du -h target/release/agit | cut -f1)"
echo
echo "To install:"
echo "  sudo cp target/release/agit /usr/local/bin/"
echo
echo "To test:"
echo "  ./target/release/agit check"
echo
