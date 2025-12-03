# Salutations - Multi-LLM Braiding System

An autonomous AI system that learns to braid multiple LLMs together with search capabilities and graph-based memory.

## 🌟 Features

- **Multi-LLM Braiding** - Combine multiple models with full hidden layer access
- **Meta-Learning Agent** - AI that learns to braid LLMs automatically
- **Self-Bootstrapping** - Agent can configure and run itself
- **Playwright MCP** - Web automation and search
- **Neo4j Memory** - Graph-based memory with semantic search
- **SOC 2 Automation** - Generate compliance evidence automatically

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/salutations.git
cd salutations

# Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Activate environment
source venv/bin/activate

# Try the meta-braiding demo
python examples/show_meta_braiding.py
```

## 🧠 What is Braiding?

Braiding combines multiple LLMs by fusing their hidden layer representations:

```
Model A → [Layer 0, Layer 4, Layer 8, ...]
Model B → [Layer 0, Layer 4, Layer 8, ...]
Model C → [Layer 0, Layer 4, Layer 8, ...]
    ↓         ↓         ↓
  Fusion    Fusion    Fusion
    ↓         ↓         ↓
Combined knowledge from all models
```

## 🤖 Meta-Learning

The agent learns to braid automatically:

```python
from models.meta_braider import MetaBraider

# Agent decides how to braid for any task
meta_braider = MetaBraider(model_pool)
decision = meta_braider.forward(task)
braided = meta_braider.create_braided_model(decision)

# Agent learns from feedback
meta_braider.learn_from_feedback(task, decision, performance)
```

## 📚 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started quickly
- [BRAIDING_GUIDE.md](BRAIDING_GUIDE.md) - Complete braiding guide
- [META_BRAIDING.md](META_BRAIDING.md) - Meta-learning approach
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CHEATSHEET.md](CHEATSHEET.md) - Quick reference

## 🎯 Use Cases

### 1. Multi-Domain Expert System
Combine specialized models (code, medical, legal) and let the agent route dynamically.

### 2. SOC 2 Compliance Automation
Generate audit evidence automatically with web automation.

### 3. Self-Improving Assistant
Agent learns from user feedback and continuously improves.

## 🛠️ Architecture

```
┌─────────────────────────────────────────┐
│         Meta-Braider Agent              │
│  (Learns optimal braiding strategies)   │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│         Braided LLM System              │
│  Model A + Model B + Model C            │
└────────────────┬────────────────────────┘
                 ↓
        ┌────────┼────────┐
        ↓        ↓        ↓
    ┌──────┐ ┌──────┐ ┌──────┐
    │ MCP  │ │Neo4j │ │Tools │
    └──────┘ └──────┘ └──────┘
```

## 🔧 Components

- **models/** - LLM wrappers, braiding, fusion strategies, meta-learner
- **memory/** - Neo4j integration, semantic search
- **mcp/** - Playwright MCP server for web automation
- **orchestration/** - Coordinator that ties everything together
- **tools/** - Tool execution layer
- **examples/** - Demos and tutorials

## 📖 Examples

### Basic Braiding
```python
from models import BraidedLLM

braided = BraidedLLM(
    model_configs=[
        {"model_name": "llama-3.1-8B", "role": "reasoning"},
        {"model_name": "codellama-7b", "role": "code"},
    ],
    fusion_strategy="learned_weighted",
)

response = braided.generate("Write a sorting algorithm")
```

### Self-Bootstrapping
```python
from examples.self_bootstrapping_agent import SelfBootstrappingAgent

agent = SelfBootstrappingAgent(project_root)
agent.bootstrap_and_run(task)  # Agent sets itself up and runs!
```

### SOC 2 Evidence Generation
```python
# Agent automatically:
# 1. Analyzes compliance requirements
# 2. Generates automation code
# 3. Captures evidence screenshots
# 4. Verifies controls worked
```

## 🎓 Learning Resources

- **Interactive Tutorial**: `python examples/braiding_tutorial.py`
- **Meta-Braiding Demo**: `python examples/show_meta_braiding.py`
- **Self-Bootstrapping**: `python examples/self_bootstrapping_agent.py`

## 🤝 Contributing

This is an autonomous system that improves itself! Contributions welcome.

## 📄 License

MIT

## 🌟 Key Innovation

**An AI agent that teaches itself to braid LLMs!**

The meta-braider observes tasks, tries different braiding strategies, learns from results, and continuously improves. No manual configuration needed - the agent figures it out.

---

Built with ❤️ by autonomous AI agents
