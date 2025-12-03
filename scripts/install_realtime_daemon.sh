#!/bin/bash
# Install Real-Time Git Daemon for Autonomous Coding
# Checks every 1 second for instant commits

set -e

echo "⚡ Real-Time Git Daemon Installer"
echo "================================="
echo ""
echo "🤖 Optimized for autonomous coding"
echo "   Checks every 1 second"
echo "   Commits instantly when ready"
echo ""

# Get repo path
REPO_PATH="${1:-$(pwd)}"

echo "📁 Repository: $REPO_PATH"
echo ""

# Check if repo exists
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

echo "🔧 Installing real-time daemon..."
echo ""

# Install with 1-second interval
python examples/git_daemon.py \
  --install \
  --repo "$REPO_PATH" \
  --interval 1 \
  --threshold 0.6

echo ""
echo "✅ Real-time daemon installed!"
echo ""
echo "⚡ Configuration:"
echo "   Check interval: 1 second (instant!)"
echo "   Commit threshold: 0.6 (optimized for AI agents)"
echo ""
echo "📋 Commands:"
echo "   Start:   launchctl start com.salutations.git-daemon"
echo "   Stop:    launchctl stop com.salutations.git-daemon"
echo "   Logs:    tail -f $REPO_PATH/.git/daemon.log"
echo ""
echo "🎉 Git is now REAL-TIME! Commits happen instantly."
