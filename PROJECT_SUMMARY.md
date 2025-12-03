# Salutations - Project Summary

## What You Have

A complete **multi-LLM braiding system** with:

✅ **Full hidden layer access** to all transformer layers  
✅ **Multiple fusion strategies** (weighted, attention, router)  
✅ **Playwright MCP server** for web search and scraping  
✅ **Neo4j graph database** for memory and knowledge graphs  
✅ **Orchestration layer** that ties everything together  
✅ **Training pipeline** for fusion layers  
✅ **Example scripts** and documentation  

## Project Structure

```
salutations/
├── models/                    # 🧠 LLM braiding core
│   ├── model_wrapper.py       # Individual model with layer access
│   ├── braided_model.py       # Multi-model braiding
│   └── fusion_layers.py       # Fusion strategies
│
├── memory/                    # 🗄️ Graph database memory
│   ├── neo4j_client.py        # Neo4j connection
│   ├── memory_manager.py      # High-level memory ops
│   └── schema.py              # Database schema
│
├── mcp/                       # 🌐 Playwright MCP server
│   └── src/index.ts           # Web search & scraping tools
│
├── tools/                     # 🔧 Tool execution
│   └── tool_executor.py       # MCP tool integration
│
├── orchestration/             # 🎯 Main coordinator
│   └── coordinator.py         # Ties models + memory + tools
│
├── examples/                  # 📚 Usage examples
│   ├── basic_usage.py         # Full system example
│   └── test_braiding.py       # Test braiding functionality
│
├── scripts/                   # ⚙️ Setup & training
│   ├── setup.sh               # Installation script
│   └── train_fusion.py        # Train fusion layers
│
├── config/                    # ⚙️ Configuration
│   └── fusion_config.yaml     # Training config
│
├── README.md                  # Main documentation
├── ARCHITECTURE.md            # Detailed architecture
├── QUICKSTART.md              # Quick start guide
└── requirements.txt           # Python dependencies
```

## Key Features

### 1. Multi-LLM Braiding

**Access all hidden layers:**
```python
output = model.forward(input_ids)
# output.hidden_states = tuple of all layer outputs
layer_5 = output.hidden_states[5]  # (batch, seq_len, hidden_dim)
```

**Combine multiple models:**
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

**Fusion happens at specified layers:**
```
Layer 0:  [Model A] [Model B] [Model C]
              ↓         ↓         ↓
          Fusion Layer (learned weights)
              ↓
          [Fused representation]
              ↓
Layer 1-3: Continue with fused state
              ↓
Layer 4:  Fusion again...
```

### 2. Fusion Strategies

**Learned Weighted Fusion**
- Trainable weights: `α·A + β·B + γ·C`
- Simplest, most efficient
- Good starting point

**Attention Fusion**
- Cross-attention between models
- More expressive
- Better for complex interactions

**Router Fusion**
- Dynamic routing based on input
- Mixture-of-Experts style
- Input-dependent combination

**Hierarchical Fusion**
- Progressive binary tree fusion
- Scalable to many models

### 3. Graph Memory (Neo4j)

**Store conversations:**
```python
conv_id = memory.create_conversation()
memory.add_message(conv_id, "user", "Hello")
history = memory.get_conversation_history(conv_id)
```

**Build knowledge graph:**
```python
memory.create_entity("Python", "language")
memory.create_entity("Django", "framework")
memory.create_entity_relationship("Python", "Django", "HAS_FRAMEWORK")
```

**Semantic search:**
```python
# Vector similarity search
results = memory.semantic_search_messages("machine learning", top_k=10)
docs = memory.semantic_search_documents("transformers", top_k=5)
```

**Graph traversal:**
```python
# Get entity with relationships
context = memory.get_entity_context("Python", max_depth=2)
```

### 4. Web Search (MCP)

**Playwright-based tools:**
- `web_search` - Search Google, Bing, DuckDuckGo
- `extract_content` - Extract page content
- `navigate` - Navigate and interact
- `screenshot` - Capture screenshots

**Usage:**
```python
tools = ToolExecutor()
results = tools.execute("web_search", {
    "query": "transformer architecture",
    "engine": "duckduckgo"
})
```

### 5. Orchestration

**Coordinates everything:**
```python
coordinator = Coordinator(
    braided_model=model,
    memory_manager=memory,
    tool_executor=tools,
)

result = coordinator.run(
    query="Search for AI advances and summarize",
    use_memory=True,
    use_tools=True,
)
```

**Workflow:**
1. Retrieve context from memory (semantic search)
2. Build prompt with context
3. Generate with braided model
4. Parse tool calls
5. Execute tools (web search, etc.)
6. Store results in memory
7. Continue until final answer

## Training Fusion Layers

**Only train fusion, freeze base models:**
```python
# Base models frozen
for model in braided.models:
    for param in model.parameters():
        param.requires_grad = False

# Fusion layers trainable
for param in braided.fusion_modules.parameters():
    param.requires_grad = True

# Train
optimizer = AdamW(braided.fusion_modules.parameters())
# ... training loop ...
```

**Save/load fusion weights:**
```python
# Save (only fusion layers, not full models)
braided.save_fusion_layers("fusion.pt")

# Load
braided.load_fusion_layers("fusion.pt")
```

## Use Cases

### 1. Multi-Domain Expert System
Combine specialized models:
- Medical model for health queries
- Code model for programming
- General model for everything else
- Router fusion dynamically selects

### 2. RAG with Knowledge Graph
- Store documents in Neo4j with embeddings
- Build entity relationships
- Semantic search for relevant context
- Generate with braided models

### 3. Research Assistant
- Web search via MCP
- Extract and store content
- Build knowledge graph
- Summarize with multiple perspectives

### 4. Code Generation
- Reasoning model for logic
- Code model for syntax
- Search model for documentation
- Fuse for better code generation

## Getting Started

### Quick Start (5 minutes)

```bash
# 1. Setup
cd /Users/ryanbarrett/salutations
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Edit config
nano .env  # Set passwords, model paths

# 4. Test
python examples/test_braiding.py
```

### Next Steps

1. **Read QUICKSTART.md** - Detailed usage examples
2. **Read ARCHITECTURE.md** - System design details
3. **Experiment** - Try different fusion strategies
4. **Train** - Fine-tune fusion layers on your data
5. **Extend** - Add custom models, tools, memory queries

## Technical Highlights

### Why This Approach?

**Full Layer Access**
- Not just final outputs
- Access intermediate representations
- Enable layer-wise fusion
- More control than API-based approaches

**Trainable Fusion**
- Learn optimal combination
- Adapt to your domain
- Small parameter count (only fusion layers)
- Fast training

**Graph Memory**
- Relationships matter
- Semantic + structural search
- Knowledge accumulation
- Multi-hop reasoning

**MCP Integration**
- Standard protocol
- Easy to extend
- Playwright for web interaction
- Tool calling support

### Performance Tips

1. **Use quantization** (8-bit recommended)
2. **Fuse every 4th layer** (not every layer)
3. **Limit context** (top-k semantic search)
4. **Batch efficiently** (adjust for GPU memory)
5. **Cache layers** (for repeated queries)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                            │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Coordinator                             │
│  - Memory retrieval (semantic search)                    │
│  - Prompt construction                                   │
│  - Tool orchestration                                    │
└────────────────────┬────────────────────────────────────┘
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Model A    │ │   Model B    │ │   Model C    │
│  (Reasoning) │ │   (Search)   │ │    (Code)    │
│              │ │              │ │              │
│ Layer 0 ─────┼─┼─ Layer 0 ───┼─┼─ Layer 0     │
│      ↓       │ │      ↓       │ │      ↓       │
│ [Fusion Layer at Layer 0]     │ │              │
│      ↓       │ │      ↓       │ │      ↓       │
│ Layer 1-3    │ │ Layer 1-3    │ │ Layer 1-3    │
│      ↓       │ │      ↓       │ │      ↓       │
│ [Fusion Layer at Layer 4]     │ │              │
│      ↓       │ │      ↓       │ │      ↓       │
│   ...        │ │   ...        │ │   ...        │
└──────────────┘ └──────────────┘ └──────────────┘
        │            │            │
        └────────────┼────────────┘
                     ↓
        ┌────────────────────────┐
        │   Fused Output         │
        │   (Logits)             │
        └────────────┬───────────┘
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Neo4j       │ │ Playwright   │ │   Vector     │
│  Graph DB    │ │ MCP Server   │ │   Search     │
│              │ │              │ │              │
│ - Entities   │ │ - Search     │ │ - Embeddings │
│ - Relations  │ │ - Scraping   │ │ - Similarity │
│ - Memory     │ │ - Navigate   │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## What Makes This Unique

1. **Full Hidden Layer Access** - Not just API calls, full model control
2. **Trainable Fusion** - Learn how to combine models optimally
3. **Graph Memory** - Relationships + semantics, not just vector search
4. **MCP Integration** - Standard protocol for tools
5. **Modular Design** - Easy to extend and customize

## Files to Read

1. **QUICKSTART.md** - Start here for usage
2. **ARCHITECTURE.md** - Deep dive into design
3. **README.md** - Overview and setup
4. **examples/test_braiding.py** - See it in action

## Support & Development

- Check logs: `tail -f logs/salutations.log`
- Neo4j browser: http://localhost:7474
- Debug mode: Set `LOG_LEVEL=DEBUG` in `.env`

---

**You now have a complete multi-LLM braiding system with search and memory!** 🎉

Start with `QUICKSTART.md` and experiment with different fusion strategies.
