# Salutations - Multi-LLM Braiding System

A language model system that braids multiple LLMs together with search capabilities via Playwright MCP and graph-based memory using Neo4j.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
│              (Request routing, tool selection)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Model A    │    │   Model B    │    │   Model C    │
│  (Reasoning) │    │   (Search)   │    │    (Code)    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ↓
                  ┌──────────────────┐
                  │  Braiding Layer  │
                  │  (Fusion Logic)  │
                  └──────────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Playwright   │    │    Neo4j     │    │   Vector     │
│ MCP Server   │    │  Graph DB    │    │    Store     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Key Features

- **Multi-LLM Braiding**: Combine multiple models with access to all hidden layers
- **Meta-Braiding**: Agent that learns to braid LLMs automatically
- **Layer-wise Fusion**: Intelligent fusion of representations across models
- **Web Search**: Playwright-based MCP server for search and scraping
- **Graph Memory**: Neo4j for relationship-aware memory storage
- **Tool Calling**: Dynamic tool selection and execution

## Project Structure

```
salutations/
├── models/              # LLM model wrappers and braiding logic
├── mcp/                 # Playwright MCP server
├── memory/              # Neo4j integration and graph operations
├── orchestration/       # Request routing and coordination
├── tools/               # Tool definitions and executors
├── api/                 # FastAPI server
├── config/              # Configuration files
├── tests/               # Test suite
└── notebooks/           # Experimentation notebooks
```

## Setup

### Prerequisites
- Python 3.10+
- CUDA-capable GPU (recommended for local inference)
- Neo4j database
- Node.js 18+ (for MCP server)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install MCP server dependencies
cd mcp
npm install
cd ..

# Set up Neo4j
docker-compose up -d neo4j
```

### Configuration

Copy `.env.example` to `.env` and configure:
```bash
# Model paths
MODEL_A_PATH=meta-llama/Llama-3.1-8B
MODEL_B_PATH=mistralai/Mistral-7B-v0.1
MODEL_C_PATH=microsoft/Phi-3-mini-4k-instruct

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# MCP Server
MCP_SERVER_PORT=3000
```

## Usage

### Start the system
```bash
# Start Neo4j
docker-compose up -d neo4j

# Start MCP server
cd mcp && npm start &

# Start API server
python -m api.server
```

### Example: Braided Inference
```python
from models.braided_model import BraidedLLM
from orchestration.coordinator import Coordinator

# Initialize braided model
model = BraidedLLM(
    models=["llama-3.1-8B", "mistral-7B", "phi-3"],
    fusion_strategy="learned_weighted"
)

# Create coordinator with tools
coordinator = Coordinator(
    model=model,
    tools=["web_search", "neo4j_memory"]
)

# Run inference
response = coordinator.run(
    "Search for recent advances in transformer architectures and summarize"
)
```

## Braiding Strategies

### 1. Learned Weighted Fusion
```python
# Trainable weights for each model's contribution
hidden = α·model_A + β·model_B + γ·model_C
```

### 2. Attention-based Fusion
```python
# Cross-attention between model hidden states
fused = CrossAttention(query=model_A, key=model_B, value=model_C)
```

### 3. Router-based Selection
```python
# Dynamic routing based on input
router = Router(input)
weights = softmax(router.logits)
hidden = Σ(weights[i] · model_i)
```

## Meta-Braiding

Train an agent to automatically learn how to braid LLMs:

```python
from models.meta_braider import MetaBraider

# Create agent with model pool
meta_braider = MetaBraider(model_pool=[...])

# Agent decides how to braid for a task
decision = meta_braider.forward(task_info)

# Create braided model from decision
braided = meta_braider.create_braided_model(decision)

# Agent learns from feedback
meta_braider.learn_from_feedback(task_info, decision, performance)
```

See [META_BRAIDING.md](META_BRAIDING.md) for details.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started quickly
- **[BRAIDING_GUIDE.md](BRAIDING_GUIDE.md)** - Complete braiding guide
- **[META_BRAIDING.md](META_BRAIDING.md)** - Meta-learning approach
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[CHEATSHEET.md](CHEATSHEET.md)** - Quick reference

## Development

### Running Tests
```bash
pytest tests/
```

### Training Fusion Layers
```bash
python scripts/train_fusion.py --config config/fusion_config.yaml
```

### Meta-Braiding Example
```bash
python examples/meta_braiding_example.py
```

## License

MIT
