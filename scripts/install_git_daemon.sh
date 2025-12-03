#!/bin/bash
# Install Git Daemon as system service

set -e

echo "🤖 Git Daemon Installer"
echo "======================="
echo ""

# Get repo path
REPO_PATH="${1:-$(pwd)}"

echo "📁 Repository: $REPO_PATH"
echo ""

# Check if repo exists
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "❌ Error: Not a git repository"
    echo "   Run from a git repo or provide path:"
    echo "   ./install_git_daemon.sh /path/to/repo"
    exit 1
fi

echo "🔧 Installing Git Daemon..."
echo ""

# Install service
python examples/git_daemon.py --install --repo "$REPO_PATH"

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Quick commands:"
echo "   Start:   launchctl start com.salutations.git-daemon"
echo "   Stop:    launchctl stop com.salutations.git-daemon"
echo "   Logs:    tail -f $REPO_PATH/.git/daemon.log"
echo ""
echo "🎉 Git is now autonomous! Just write code."
