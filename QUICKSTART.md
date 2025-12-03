# Salutations - Quick Start Guide

## Installation

### 1. Clone and Setup

```bash
cd /Users/ryanbarrett/salutations

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
- Create Python virtual environment
- Install dependencies
- Build MCP server
- Start Neo4j database
- Create necessary directories

### 2. Configure Environment

Edit `.env` file:

```bash
# Update these values
NEO4J_PASSWORD=your_secure_password
MODEL_A_PATH=meta-llama/Llama-3.1-8B  # Or your preferred model
MODEL_B_PATH=mistralai/Mistral-7B-v0.1
MODEL_C_PATH=microsoft/Phi-3-mini-4k-instruct
```

### 3. Verify Installation

```bash
source venv/bin/activate

# Test individual model wrapper
python examples/test_braiding.py

# Check Neo4j
open http://localhost:7474
# Login: neo4j / your_password
```

## Basic Usage

### Example 1: Simple Braided Inference

```python
from models import BraidedLLM

# Initialize braided model
model = BraidedLLM(
    model_configs=[
        {"model_name": "microsoft/Phi-3-mini-4k-instruct", "role": "reasoning", "quantization": "8bit"},
        {"model_name": "microsoft/Phi-3-mini-4k-instruct", "role": "code", "quantization": "8bit"},
    ],
    fusion_strategy="learned_weighted",
)

# Generate
response = model.generate(
    prompt="Explain quantum computing in simple terms.",
    max_new_tokens=200,
)

print(response)
```

### Example 2: With Memory

```python
from models import BraidedLLM
from memory import Neo4jClient, MemoryManager, init_schema

# Setup
neo4j = Neo4jClient()
init_schema(neo4j)
memory = MemoryManager(neo4j)

# Create conversation
conv_id = memory.create_conversation()

# Add messages
memory.add_message(conv_id, "user", "What is machine learning?")
memory.add_message(conv_id, "assistant", "Machine learning is...")

# Retrieve history
history = memory.get_conversation_history(conv_id)

# Semantic search
results = memory.semantic_search_messages("neural networks", top_k=5)
```

### Example 3: Full System with Tools

```python
from models import BraidedLLM
from memory import Neo4jClient, MemoryManager, init_schema
from tools import ToolExecutor
from orchestration import Coordinator

# Initialize all components
braided_model = BraidedLLM(
    model_configs=[
        {"model_name": "microsoft/Phi-3-mini-4k-instruct", "role": "reasoning", "quantization": "8bit"},
    ],
    fusion_strategy="learned_weighted",
)

neo4j = Neo4jClient()
init_schema(neo4j)
memory = MemoryManager(neo4j)
tools = ToolExecutor()

# Create coordinator
coordinator = Coordinator(
    braided_model=braided_model,
    memory_manager=memory,
    tool_executor=tools,
)

# Run query
result = coordinator.run(
    query="Search for recent advances in transformer architectures and summarize",
    use_memory=True,
    use_tools=True,
)

print(f"Answer: {result['answer']}")
print(f"Tool calls: {len(result['tool_calls'])}")
```

## Understanding Braiding

### What is Braiding?

Braiding combines multiple LLMs by fusing their hidden layer representations:

```
Input: "Explain quantum computing"
    ↓
Model A (Reasoning)     Model B (Science)     Model C (Code)
Layer 1: [h1_a]         Layer 1: [h1_b]       Layer 1: [h1_c]
    ↓                       ↓                     ↓
    └───────────────────────┴─────────────────────┘
                            ↓
                    Fusion Layer
                            ↓
                    Fused: [h1_fused]
                            ↓
                    Continue to Layer 2...
```

### Why Braid?

1. **Specialization**: Each model can focus on what it does best
2. **Complementary Knowledge**: Combine different training data/domains
3. **Emergent Capabilities**: Fusion can create new behaviors
4. **Flexibility**: Add/remove models without retraining

### Fusion Strategies

**Learned Weighted** (Simplest)
```python
fusion_strategy="learned_weighted"
# Learns: fused = 0.4·model_A + 0.3·model_B + 0.3·model_C
```

**Attention** (More Expressive)
```python
fusion_strategy="attention"
# Uses cross-attention to combine models
```

**Router** (Dynamic)
```python
fusion_strategy="router"
# Dynamically routes based on input
```

## Training Fusion Layers

### Prepare Data

Create `data/train.txt`:
```
First training example text.
Second training example text.
...
```

### Configure Training

Edit `config/fusion_config.yaml`:
```yaml
batch_size: 4
learning_rate: 5e-5
num_epochs: 3
fusion_layers: [0, 4, 8, 12]
```

### Run Training

```bash
python scripts/train_fusion.py
```

This trains only the fusion layers while keeping base models frozen.

### Load Trained Fusion

```python
model = BraidedLLM(...)
model.load_fusion_layers("checkpoints/fusion_final.pt")
```

## Working with Memory

### Store Knowledge

```python
# Entities
memory.create_entity("Python", "language", "Programming language")
memory.create_entity("Django", "framework", "Web framework")
memory.create_entity_relationship("Python", "Django", "HAS_FRAMEWORK")

# Documents
memory.store_document(
    url="https://example.com/article",
    title="AI Article",
    content="Full article text...",
)
```

### Query Knowledge Graph

```python
# Get entity with relationships
context = memory.get_entity_context("Python", max_depth=2)

# Semantic search
similar = memory.semantic_search_documents("machine learning", top_k=10)
```

### Visualize in Neo4j Browser

```cypher
// View all entities
MATCH (e:Entity) RETURN e LIMIT 25

// View conversation graph
MATCH (c:Conversation)-[:CONTAINS]->(m:Message)
RETURN c, m LIMIT 50

// Find related entities
MATCH path = (e:Entity {name: "Python"})-[*1..2]-(related)
RETURN path
```

## Using MCP Tools

### Start MCP Server

```bash
cd mcp
npm start
```

### Available Tools

```python
tools = ToolExecutor()

# Web search
result = tools.execute("web_search", {
    "query": "transformer architecture",
    "engine": "duckduckgo",
    "maxResults": 10
})

# Extract content
content = tools.execute("extract_content", {
    "url": "https://example.com"
})

# Screenshot
screenshot = tools.execute("screenshot", {
    "url": "https://example.com",
    "fullPage": True
})
```

## Accessing Hidden Layers

### Get All Hidden States

```python
from models import ModelWrapper

model = ModelWrapper("microsoft/Phi-3-mini-4k-instruct")
inputs = model.encode("Hello world")

output = model.forward(
    input_ids=inputs["input_ids"],
    attention_mask=inputs["attention_mask"],
)

# All layers
print(f"Number of layers: {len(output.hidden_states)}")
print(f"Layer 0 shape: {output.hidden_states[0].shape}")
print(f"Layer 5 shape: {output.hidden_states[5].shape}")
```

### Extract Specific Layer

```python
# Get just layer 10
layer_10 = model.get_layer_output(
    input_ids=inputs["input_ids"],
    layer_idx=10,
)

print(f"Layer 10 output: {layer_10.shape}")
# Shape: (batch, seq_len, hidden_dim)
```

### Custom Forward Pass

```python
# Get specific layers only
output = model.forward(
    input_ids=inputs["input_ids"],
    return_layer_indices=[0, 5, 10, 15],  # Only these layers
)

# Now output.hidden_states has only 4 tensors
```

## Common Patterns

### Pattern 1: Multi-Domain Expert System

```python
# Specialized models for different domains
models = [
    {"model_name": "codellama-7b", "role": "code"},
    {"model_name": "meditron-7b", "role": "medical"},
    {"model_name": "llama-3.1-8b", "role": "general"},
]

braided = BraidedLLM(models, fusion_strategy="router")
# Router will dynamically select based on query
```

### Pattern 2: RAG with Graph Memory

```python
def rag_query(query):
    # 1. Semantic search
    docs = memory.semantic_search_documents(query, top_k=5)
    
    # 2. Get entity context
    entities = extract_entities(query)  # Your NER
    context = [memory.get_entity_context(e) for e in entities]
    
    # 3. Generate with context
    prompt = build_prompt(query, docs, context)
    response = model.generate(prompt)
    
    return response
```

### Pattern 3: Iterative Tool Use

```python
def research_query(query):
    # Search web
    search_results = tools.execute("web_search", {"query": query})
    
    # Extract top results
    for result in search_results["results"][:3]:
        content = tools.execute("extract_content", {"url": result["link"]})
        memory.store_document(result["link"], result["title"], content)
    
    # Generate summary with memory
    summary = coordinator.run(f"Summarize findings about: {query}")
    
    return summary
```

## Troubleshooting

### Out of Memory

```python
# Use smaller models
model_configs = [
    {"model_name": "microsoft/Phi-3-mini-4k-instruct", "quantization": "8bit"},
]

# Reduce batch size
config["batch_size"] = 1

# Fuse less frequently
fusion_layers = [0, 8, 16]  # Instead of every 4 layers
```

### Neo4j Connection Issues

```bash
# Check if running
docker ps | grep neo4j

# Restart
docker-compose restart neo4j

# View logs
docker-compose logs neo4j
```

### MCP Server Not Responding

```bash
# Check if running
cd mcp
npm start

# Rebuild
npm run build
```

## Next Steps

1. **Read ARCHITECTURE.md** for detailed system design
2. **Experiment with fusion strategies** - try different approaches
3. **Add your own models** - specialize for your domain
4. **Build custom tools** - extend MCP server
5. **Train fusion layers** - optimize for your use case

## Resources

- Neo4j Browser: http://localhost:7474
- Project Structure: See README.md
- Architecture Details: See ARCHITECTURE.md
- Example Scripts: `examples/` directory

## Getting Help

Check the logs:
```bash
tail -f logs/salutations.log
```

Enable debug logging:
```python
from loguru import logger
logger.add("debug.log", level="DEBUG")
```
