#!/bin/bash

# Setup script for Salutations multi-LLM braiding system

set -e

echo "🚀 Setting up Salutations..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Setup MCP server
echo "🌐 Setting up MCP server..."
cd mcp
npm install
npm run build
cd ..

# Setup environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p checkpoints
mkdir -p data

# Start Neo4j with Docker
echo "🗄️  Starting Neo4j..."
docker-compose up -d neo4j

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to start..."
sleep 10

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run example: python examples/test_braiding.py"
echo ""
echo "Neo4j browser: http://localhost:7474"
echo "Default credentials: neo4j / your_password_here"
