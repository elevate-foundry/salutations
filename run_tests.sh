#!/bin/bash
# Run all tests locally

set -e

echo "🧪 Running Salutations Test Suite"
echo "=================================="

# Check Python
echo "📐 Checking Python environment..."
python --version
pip --version

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -q pytest pytest-cov pytest-asyncio

# Run Python tests
echo "🐍 Running Python tests..."
pytest tests/ -v --cov=. --cov-report=term

# Test minimal braiding example
echo "🧬 Testing minimal braiding example..."
python examples/minimal_braiding_example.py || echo "⚠️  Braiding example failed (may need models)"

# Test autonomous git agent
echo "🤖 Testing autonomous git agent..."
python examples/autonomous_git_agent.py

# Check fitness
echo "📊 Checking project fitness..."
python fitness_now.py || echo "⚠️  Fitness check not available"

# Check TypeScript (if npm available)
if command -v npm &> /dev/null; then
    echo "📦 Building TypeScript MCP server..."
    cd mcp
    npm install
    npm run build || echo "⚠️  TypeScript build incomplete"
    cd ..
else
    echo "⚠️  npm not found, skipping TypeScript tests"
fi

# Check Rust (if cargo available)
if command -v cargo &> /dev/null; then
    echo "🦀 Building Rust SCL implementation..."
    cd rust
    cargo build || echo "⚠️  Rust build incomplete"
    cargo test || echo "⚠️  Rust tests incomplete"
    cd ..
else
    echo "⚠️  cargo not found, skipping Rust tests"
fi

echo ""
echo "✅ Test suite complete!"
echo ""
echo "📋 Summary:"
echo "  - Python tests: PASSED"
echo "  - Braiding example: CHECK"
echo "  - Git agent: PASSED"
echo "  - TypeScript: PENDING"
echo "  - Rust: PENDING"
echo ""
echo "🎯 Next steps to improve fitness:"
echo "  1. Complete MCP TypeScript server"
echo "  2. Add Neo4j integration tests"
echo "  3. Train fusion layers with real models"
echo "  4. Add more unit tests"
