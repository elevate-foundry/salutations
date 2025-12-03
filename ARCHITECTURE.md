# Salutations Architecture

## Overview

Salutations is a multi-LLM braiding system that combines multiple language models with full access to their hidden layers, integrated with web search via Playwright MCP and graph-based memory using Neo4j.

## Core Components

### 1. Model Layer (`models/`)

#### ModelWrapper (`model_wrapper.py`)
- Wraps individual LLMs with full hidden layer access
- Provides methods to extract representations from any layer
- Supports quantization (4-bit, 8-bit)
- Key features:
  - `forward()` - Get all hidden states
  - `get_layer_output()` - Extract specific layer
  - `generate()` - Text generation

#### Fusion Layers (`fusion_layers.py`)
Multiple strategies for combining model representations:

**LearnedWeightedFusion**
```python
fused = α·model_A + β·model_B + γ·model_C
```
- Learnable weights (α, β, γ)
- Normalized with softmax
- Simplest approach

**AttentionFusion**
```python
fused = CrossAttention(query=model_A, key=models_B_C, value=models_B_C)
```
- Multi-head cross-attention
- One model as query, others as context
- More expressive than weighted

**RouterFusion**
```python
weights = Router(input)
fused = Σ(weights[i] · expert_i(model_i))
```
- Dynamic routing based on input
- Mixture-of-Experts style
- Input-dependent fusion

**HierarchicalFusion**
- Binary tree fusion
- Progressively combines pairs
- Scalable to many models

#### BraidedLLM (`braided_model.py`)
Main class that orchestrates multiple models:

```python
braided = BraidedLLM(
    model_configs=[
        {"model_name": "llama-3.1-8B", "role": "reasoning"},
        {"model_name": "mistral-7B", "role": "search"},
        {"model_name": "phi-3", "role": "code"},
    ],
    fusion_strategy="learned_weighted",
    fusion_layers=[0, 4, 8, 12],  # Fuse at these layers
)
```

Key methods:
- `forward()` - Braided forward pass with fusion
- `generate()` - Text generation with braiding
- `save_fusion_layers()` - Save only fusion weights
- `load_fusion_layers()` - Load fusion weights

### 2. Memory Layer (`memory/`)

#### Neo4jClient (`neo4j_client.py`)
Low-level Neo4j operations:
- Connection management
- Cypher query execution
- Vector search support

#### MemoryManager (`memory_manager.py`)
High-level memory operations:

**Conversation Management**
```python
conv_id = memory.create_conversation()
memory.add_message(conv_id, role="user", content="Hello")
history = memory.get_conversation_history(conv_id)
```

**Entity & Knowledge Graph**
```python
memory.create_entity("Python", "language", "Programming language")
memory.create_entity_relationship("Python", "Django", "HAS_FRAMEWORK")
context = memory.get_entity_context("Python", max_depth=2)
```

**Document Storage**
```python
memory.store_document(
    url="https://example.com",
    title="Example",
    content="...",
)
```

**Semantic Search**
```python
results = memory.semantic_search_messages("machine learning", top_k=10)
docs = memory.semantic_search_documents("transformers", top_k=5)
```

#### Schema (`schema.py`)
Database schema with:
- Node types: Conversation, Message, Entity, Document
- Relationships: PART_OF, MENTIONS, REFERENCES, RELATED_TO
- Vector indexes for embeddings
- Constraints and indexes

### 3. MCP Server (`mcp/`)

Playwright-based MCP server for web interaction:

**Tools Available:**
- `web_search` - Search engines (Google, Bing, DuckDuckGo)
- `extract_content` - Extract page content
- `navigate` - Navigate and interact with pages
- `screenshot` - Capture screenshots

**Example:**
```typescript
{
  "tool": "web_search",
  "arguments": {
    "query": "transformer architecture",
    "engine": "duckduckgo",
    "maxResults": 10
  }
}
```

### 4. Tools Layer (`tools/`)

#### ToolExecutor (`tool_executor.py`)
Executes tools and manages MCP communication:

```python
executor = ToolExecutor()
result = executor.execute(
    tool_name="web_search",
    arguments={"query": "...", "engine": "duckduckgo"}
)
```

### 5. Orchestration Layer (`orchestration/`)

#### Coordinator (`coordinator.py`)
Main orchestrator that ties everything together:

```python
coordinator = Coordinator(
    braided_model=braided_model,
    memory_manager=memory_manager,
    tool_executor=tool_executor,
)

result = coordinator.run(
    query="Search for recent AI advances and summarize",
    use_memory=True,
    use_tools=True,
)
```

**Workflow:**
1. Retrieve relevant context from memory
2. Build prompt with context
3. Generate response with braided model
4. Parse tool calls if any
5. Execute tools
6. Store results in memory
7. Continue until final answer
8. Store conversation

## Data Flow

```
User Query
    ↓
Coordinator
    ↓
Memory Retrieval (semantic search)
    ↓
Prompt Construction
    ↓
Braided LLM
    ├─→ Model A (reasoning) ─┐
    ├─→ Model B (search)    ─┼─→ Fusion Layers → Output
    └─→ Model C (code)      ─┘
    ↓
Tool Call Detection
    ↓
Tool Execution (MCP)
    ↓
Memory Storage
    ↓
Final Response
```

## Hidden Layer Access

Each model provides access to all transformer layers:

```python
# Get all hidden states
output = model.forward(input_ids, return_hidden_states=True)
# output.hidden_states = tuple of (batch, seq_len, hidden_dim)

# Access specific layer
layer_5 = output.hidden_states[5]

# Fuse at specific layers
for layer_idx in fusion_layers:
    hidden_states = [model.hidden_states[layer_idx] for model in models]
    fused = fusion_layer(hidden_states)
```

## Training Fusion Layers

Only fusion layers are trainable, base models are frozen:

```python
# Freeze base models
for model in braided.models:
    for param in model.parameters():
        param.requires_grad = False

# Train fusion layers
for param in braided.fusion_modules.parameters():
    param.requires_grad = True

# Standard training loop
optimizer = AdamW(braided.fusion_modules.parameters())
```

## Neo4j Schema

```cypher
// Nodes
(:Conversation {id, timestamp, metadata})
(:Message {id, role, content, embedding, timestamp})
(:Entity {name, type, description, properties})
(:Document {url, title, content, embedding})

// Relationships
(:Message)-[:PART_OF]->(:Conversation)
(:Message)-[:MENTIONS]->(:Entity)
(:Entity)-[:RELATED_TO]->(:Entity)
(:Document)-[:REFERENCES]->(:Entity)

// Vector Indexes
message_embeddings (384-dim, cosine)
document_embeddings (384-dim, cosine)
```

## Configuration

### Environment Variables (`.env`)
```bash
# Models
MODEL_A_PATH=meta-llama/Llama-3.1-8B
MODEL_B_PATH=mistralai/Mistral-7B-v0.1
MODEL_C_PATH=microsoft/Phi-3-mini-4k-instruct

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# MCP
MCP_SERVER_PORT=3000

# Braiding
FUSION_STRATEGY=learned_weighted
```

### Fusion Config (`config/fusion_config.yaml`)
```yaml
batch_size: 4
learning_rate: 5e-5
num_epochs: 3
fusion_strategy: learned_weighted
fusion_layers: [0, 4, 8, 12, 16, 20]
```

## Extension Points

### Adding New Models
```python
model_configs.append({
    "model_name": "new-model-name",
    "role": "specialized_task",
    "quantization": "8bit",
})
```

### Custom Fusion Strategy
```python
class CustomFusion(FusionLayer):
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        # Your custom fusion logic
        return fused_output
```

### New Tools
```python
# In tool_executor.py
def _execute_custom_tool(self, arguments):
    # Tool implementation
    return result
```

### Custom Memory Queries
```python
# In memory_manager.py
def custom_graph_query(self, params):
    query = """
    MATCH (pattern)
    WHERE conditions
    RETURN results
    """
    return self.client.execute_query(query, params)
```

## Performance Considerations

1. **Model Loading**: Use quantization (8-bit recommended) to reduce memory
2. **Fusion Frequency**: Don't fuse at every layer (every 4th is good)
3. **Batch Size**: Adjust based on GPU memory
4. **Context Length**: Limit retrieved context to avoid overwhelming prompt
5. **Caching**: Enable layer caching for repeated queries

## Next Steps

1. **Fine-tune fusion layers** on domain-specific data
2. **Add more specialized models** for different tasks
3. **Implement advanced routing** based on query analysis
4. **Expand tool library** with more MCP tools
5. **Build evaluation suite** to measure braiding effectiveness
