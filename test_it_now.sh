#!/bin/bash
# Test It Now - Automated testing in under 5 minutes

set -e

echo "========================================================================"
echo "🚀 AUTOMATED TESTING SETUP"
echo "========================================================================"
echo ""

# Check if URL provided
if [ -z "$1" ]; then
    echo "❌ Error: No URL provided"
    echo ""
    echo "Usage:"
    echo "  ./test_it_now.sh https://your-app.com"
    echo "  ./test_it_now.sh https://your-app.com --soc2"
    echo ""
    exit 1
fi

URL=$1
SOC2_FLAG=$2

echo "🎯 Target: $URL"
echo ""

# Step 1: Check dependencies
echo "📦 Step 1: Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
echo "   ✓ Python found: $(python3 --version)"

# Step 2: Install Python packages
echo ""
echo "📦 Step 2: Installing Python packages..."
pip3 install -q playwright pyotp loguru 2>&1 | grep -v "already satisfied" || true
echo "   ✓ Packages installed"

# Step 3: Install Playwright browsers
echo ""
echo "📦 Step 3: Installing Playwright browsers..."
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    python3 -m playwright install chromium
    echo "   ✓ Chromium installed"
else
    echo "   ✓ Chromium already installed"
fi

# Step 4: Run tests
echo ""
echo "========================================================================"
echo "🧪 RUNNING AUTOMATED TESTS"
echo "========================================================================"
echo ""

if [ "$SOC2_FLAG" = "--soc2" ]; then
    python3 examples/automated_testing_agent.py --url "$URL" --soc2
else
    python3 examples/automated_testing_agent.py --url "$URL"
fi

# Step 5: Show results
echo ""
echo "========================================================================"
echo "✅ TESTING COMPLETE"
echo "========================================================================"
echo ""
echo "📁 Evidence saved in: ./evidence/"
echo ""
echo "View results:"
echo "  ls evidence/"
echo "  cat evidence/TEST_REPORT_*.json"
echo ""
echo "Next steps:"
echo "  1. Review the evidence folder"
echo "  2. Check the test report"
echo "  3. Fix any failed tests"
echo "  4. Add to CI/CD (see README_TESTING.md)"
echo ""
echo "🚀 You now have automated testing!"
echo "========================================================================"
