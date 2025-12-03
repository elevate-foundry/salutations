# LLM Braiding Cheat Sheet

## Quick Start

```python
from models import BraidedLLM

# 1. Configure models
models = [
    {"model_name": "llama-3.1-8B", "role": "reasoning", "quantization": "8bit"},
    {"model_name": "mistral-7B", "role": "knowledge", "quantization": "8bit"},
]

# 2. Create braided model
braided = BraidedLLM(
    model_configs=models,
    fusion_strategy="learned_weighted",
    fusion_layers=[0, 4, 8, 12],
)

# 3. Generate
response = braided.generate("Your prompt here", max_new_tokens=200)
```

## Access Hidden Layers

```python
from models import ModelWrapper

model = ModelWrapper("microsoft/Phi-3-mini-4k-instruct")
inputs = model.encode("Hello world")
output = model.forward(input_ids=inputs["input_ids"])

# All layers
all_layers = output.hidden_states  # Tuple of tensors

# Specific layer
layer_10 = output.hidden_states[10]  # Shape: (batch, seq_len, hidden_dim)

# Just one layer
layer_5 = model.get_layer_output(input_ids=inputs["input_ids"], layer_idx=5)
```

## Fusion Strategies

```python
# Learned Weighted (simplest)
fusion_strategy="learned_weighted"
# Formula: fused = α·A + β·B + γ·C (α, β, γ learned)

# Attention (more expressive)
fusion_strategy="attention"
# Formula: fused = CrossAttention(query=A, key=B,C, value=B,C)

# Router (most dynamic)
fusion_strategy="router"
# Formula: weights = Router(input); fused = Σ(weights[i] · model_i)
```

## Training Fusion Layers

```python
# 1. Freeze base models
for model in braided.models:
    for param in model.parameters():
        param.requires_grad = False

# 2. Unfreeze fusion
for param in braided.fusion_modules.parameters():
    param.requires_grad = True

# 3. Train
optimizer = AdamW(braided.fusion_modules.parameters(), lr=5e-5)

for batch in dataloader:
    output = braided.forward(input_ids=batch["input_ids"])
    loss = compute_loss(output.logits, batch["labels"])
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()

# 4. Save
braided.save_fusion_layers("fusion.pt")
```

## Memory (Neo4j)

```python
from memory import Neo4jClient, MemoryManager, init_schema

# Setup
neo4j = Neo4jClient()
init_schema(neo4j)
memory = MemoryManager(neo4j)

# Conversations
conv_id = memory.create_conversation()
memory.add_message(conv_id, "user", "Hello")
history = memory.get_conversation_history(conv_id)

# Entities
memory.create_entity("Python", "language", "Programming language")
memory.create_entity_relationship("Python", "Django", "HAS_FRAMEWORK")

# Search
results = memory.semantic_search_messages("machine learning", top_k=10)
docs = memory.semantic_search_documents("transformers", top_k=5)
```

## Tools (MCP)

```python
from tools import ToolExecutor

tools = ToolExecutor()

# Web search
results = tools.execute("web_search", {
    "query": "transformer architecture",
    "engine": "duckduckgo",
    "maxResults": 10
})

# Extract content
content = tools.execute("extract_content", {
    "url": "https://example.com"
})
```

## Full System

```python
from models import BraidedLLM
from memory import Neo4jClient, MemoryManager, init_schema
from tools import ToolExecutor
from orchestration import Coordinator

# Initialize
braided = BraidedLLM(model_configs=models)
neo4j = Neo4jClient()
init_schema(neo4j)
memory = MemoryManager(neo4j)
tools = ToolExecutor()

# Coordinate
coordinator = Coordinator(
    braided_model=braided,
    memory_manager=memory,
    tool_executor=tools,
)

# Run
result = coordinator.run(
    query="Search for AI advances and summarize",
    use_memory=True,
    use_tools=True,
)
```

## Common Patterns

### Pattern 1: Domain Experts
```python
models = [
    {"model_name": "codellama-7b", "role": "code"},
    {"model_name": "meditron-7b", "role": "medical"},
    {"model_name": "llama-3.1-8b", "role": "general"},
]
braided = BraidedLLM(models, fusion_strategy="router")
```

### Pattern 2: Size Diversity
```python
models = [
    {"model_name": "llama-3.1-70B", "role": "smart"},
    {"model_name": "phi-3-mini", "role": "fast"},
]
braided = BraidedLLM(models, fusion_strategy="router")
```

### Pattern 3: RAG with Memory
```python
# Store documents
memory.store_document(url, title, content)

# Retrieve context
docs = memory.semantic_search_documents(query, top_k=5)

# Generate with context
prompt = build_prompt(query, docs)
response = braided.generate(prompt)
```

## Configuration

### Environment (.env)
```bash
MODEL_A_PATH=meta-llama/Llama-3.1-8B
MODEL_B_PATH=mistralai/Mistral-7B-v0.1
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password
FUSION_STRATEGY=learned_weighted
```

### Training (config/fusion_config.yaml)
```yaml
batch_size: 4
learning_rate: 5e-5
num_epochs: 3
fusion_strategy: learned_weighted
fusion_layers: [0, 4, 8, 12, 16, 20]
```

## Troubleshooting

### Out of Memory
```python
# Use 8-bit quantization
{"quantization": "8bit"}

# Fuse less frequently
fusion_layers = [0, 8, 16]

# Smaller batch size
batch_size = 1
```

### Slow Inference
```python
# Fewer fusion points
fusion_layers = [0, 10, 20]

# Fewer models
model_configs = model_configs[:2]

# Smaller models
{"model_name": "phi-3-mini"}
```

### Poor Results
```python
# Train fusion layers
python scripts/train_fusion.py

# Try different strategy
fusion_strategy = "attention"

# More fusion points
fusion_layers = [0, 2, 4, 6, 8, 10]
```

## Commands

```bash
# Setup
./scripts/setup.sh

# Activate environment
source venv/bin/activate

# Test braiding
python examples/test_braiding.py

# Run tutorial
python examples/braiding_tutorial.py

# Train fusion
python scripts/train_fusion.py

# Start Neo4j
docker-compose up -d neo4j

# Start MCP server
cd mcp && npm start
```

## File Structure

```
models/
  model_wrapper.py      # Individual model with layer access
  braided_model.py      # Multi-model braiding
  fusion_layers.py      # Fusion strategies

memory/
  neo4j_client.py       # Neo4j connection
  memory_manager.py     # High-level memory ops
  schema.py             # Database schema

orchestration/
  coordinator.py        # Main coordinator

tools/
  tool_executor.py      # MCP tool execution
```

## Key Concepts

**Hidden States**: Internal representations at each layer  
**Fusion**: Combining hidden states from multiple models  
**Braiding**: Multi-layer fusion throughout the network  
**Trainable Fusion**: Only fusion layers train, base models frozen  

## Resources

- Tutorial: `examples/braiding_tutorial.py`
- Guide: `BRAIDING_GUIDE.md`
- Architecture: `ARCHITECTURE.md`
- Quick Start: `QUICKSTART.md`
- Neo4j: http://localhost:7474
