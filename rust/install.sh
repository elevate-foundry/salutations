#!/bin/bash
# Installation script for Autonomous Git

set -e

echo "🚀 Installing Autonomous Git..."
echo

# Build if not already built
if [ ! -f "target/release/agit" ]; then
    echo "📦 Building first..."
    ./build.sh
fi

# Install binary
echo "📥 Installing binary to /usr/local/bin..."
sudo cp target/release/agit /usr/local/bin/

# Verify installation
if command -v agit &> /dev/null; then
    echo
    echo "✅ Installation complete!"
    echo
    echo "Installed version:"
    agit --version || echo "  agit v0.1.0"
    echo
    echo "Quick start:"
    echo "  agit check          # Check current fitness"
    echo "  agit run            # Run agent"
    echo "  agit install        # Install as service"
    echo
else
    echo "❌ Installation failed"
    exit 1
fi
