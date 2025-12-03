# Complete Guide to LLM Braiding

## What is Braiding?

**Braiding** is the process of combining multiple language models by fusing their internal representations (hidden states) at various layers, rather than just combining their final outputs.

### Traditional vs Braiding

```
TRADITIONAL APPROACH:
Input → Model A → Output A ┐
Input → Model B → Output B ├→ Combine outputs
Input → Model C → Output C ┘

BRAIDING APPROACH:
Input → Model A [Layer 0] ┐
Input → Model B [Layer 0] ├→ FUSE → Continue
Input → Model C [Layer 0] ┘
        ↓
        [Layers 1-3 with fused state]
        ↓
        Model A [Layer 4] ┐
        Model B [Layer 4] ├→ FUSE → Continue
        Model C [Layer 4] ┘
        ↓
        ... (repeat)
        ↓
        Final combined output
```

## Core Concepts

### 1. Hidden States

Every transformer layer produces a hidden state:

```python
# Shape: (batch_size, sequence_length, hidden_dimension)
# Example: (1, 20, 4096)

Layer 0:  [0.1, 0.3, -0.2, ...]  # Token embeddings
Layer 1:  [0.2, 0.1, 0.4, ...]   # Basic patterns
Layer 5:  [0.5, -0.1, 0.3, ...]  # Concepts
Layer 10: [0.3, 0.4, -0.2, ...]  # Relationships
Layer 20: [0.1, 0.2, 0.5, ...]   # Task reasoning
```

Each layer learns progressively more abstract representations.

### 2. Fusion

Combining hidden states from multiple models:

```python
# Simple weighted fusion
fused = 0.5 * model_A_hidden + 0.5 * model_B_hidden

# Learned weighted fusion
fused = alpha * model_A_hidden + beta * model_B_hidden
# where alpha and beta are learned parameters

# Attention fusion
fused = Attention(query=model_A, key=model_B, value=model_B)

# Router fusion
weights = Router(input)
fused = weights[0] * model_A + weights[1] * model_B
```

### 3. Layer Selection

You don't need to fuse at every layer:

```python
# Fuse every 4 layers (recommended)
fusion_layers = [0, 4, 8, 12, 16, 20]

# Fuse only at key points
fusion_layers = [0, 10, 20]  # Early, middle, late

# Fuse frequently
fusion_layers = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
```

**Rule of thumb**: More fusion = more interaction but slower inference.

## Step-by-Step Tutorial

### Step 1: Access Hidden Layers

```python
from models import ModelWrapper

# Load model
model = ModelWrapper(
    model_name="microsoft/Phi-3-mini-4k-instruct",
    quantization="8bit",
)

# Encode input
inputs = model.encode("Hello world")

# Get ALL hidden states
output = model.forward(
    input_ids=inputs["input_ids"],
    attention_mask=inputs["attention_mask"],
)

# Access any layer
layer_0 = output.hidden_states[0]   # First layer
layer_10 = output.hidden_states[10] # Middle layer
layer_last = output.hidden_states[-1] # Final layer

print(f"Number of layers: {len(output.hidden_states)}")
print(f"Shape of each: {layer_0.shape}")
```

### Step 2: Simple Fusion

```python
# Get hidden states from two models
model_a = ModelWrapper("model-a")
model_b = ModelWrapper("model-b")

inputs = model_a.encode("Explain quantum computing")

output_a = model_a.forward(input_ids=inputs["input_ids"])
output_b = model_b.forward(input_ids=inputs["input_ids"])

# Fuse at layer 10
hidden_a = output_a.hidden_states[10]
hidden_b = output_b.hidden_states[10]

# Simple average
fused = 0.5 * hidden_a + 0.5 * hidden_b

# Or weighted
fused = 0.7 * hidden_a + 0.3 * hidden_b
```

### Step 3: Multi-Layer Braiding

```python
from models import BraidedLLM

# Configure models
model_configs = [
    {"model_name": "llama-3.1-8B", "role": "reasoning"},
    {"model_name": "mistral-7B", "role": "knowledge"},
    {"model_name": "phi-3", "role": "code"},
]

# Create braided model
braided = BraidedLLM(
    model_configs=model_configs,
    fusion_strategy="learned_weighted",
    fusion_layers=[0, 4, 8, 12, 16, 20],
)

# Generate
response = braided.generate(
    prompt="Write a Python function to sort a list",
    max_new_tokens=200,
)
```

### Step 4: Train Fusion Layers

```python
import torch
from torch.optim import AdamW

# Freeze base models
for model in braided.models:
    for param in model.parameters():
        param.requires_grad = False

# Unfreeze fusion layers
for param in braided.fusion_modules.parameters():
    param.requires_grad = True

# Setup optimizer (only fusion parameters)
optimizer = AdamW(
    braided.fusion_modules.parameters(),
    lr=5e-5,
)

# Training loop
for batch in dataloader:
    # Forward
    output = braided.forward(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
    )
    
    # Compute loss
    loss = compute_loss(output.logits, batch["labels"])
    
    # Backward (only fusion layers update)
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()

# Save fusion weights
braided.save_fusion_layers("fusion_weights.pt")
```

## Fusion Strategies Explained

### 1. Learned Weighted Fusion

**Best for**: Starting point, simple cases

```python
class LearnedWeightedFusion:
    def __init__(self, num_models):
        # Learnable weights
        self.weights = nn.Parameter(torch.ones(num_models) / num_models)
    
    def forward(self, hidden_states):
        # Normalize weights
        weights = F.softmax(self.weights, dim=0)
        
        # Weighted sum
        fused = sum(w * h for w, h in zip(weights, hidden_states))
        return fused
```

**Example**:
- Initial: `fused = 0.33·A + 0.33·B + 0.33·C`
- After training: `fused = 0.5·A + 0.3·B + 0.2·C`
- Model A learned to be more important!

**Pros**: Fast, simple, few parameters  
**Cons**: Same weights for all inputs

### 2. Attention Fusion

**Best for**: Complex interactions, when models should attend to each other

```python
class AttentionFusion:
    def __init__(self, hidden_dim, num_heads=8):
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
        )
    
    def forward(self, hidden_states):
        # Use first model as query
        query = hidden_states[0]
        
        # Others as key/value
        key_value = torch.cat(hidden_states[1:], dim=1)
        
        # Cross-attention
        fused, _ = self.attention(query, key_value, key_value)
        return fused
```

**Example**:
- Token "quantum" attends more to physics model
- Token "algorithm" attends more to CS model
- Different tokens use different models!

**Pros**: More expressive, token-level fusion  
**Cons**: More parameters, slower

### 3. Router Fusion

**Best for**: Dynamic selection, mixture-of-experts style

```python
class RouterFusion:
    def __init__(self, num_models, hidden_dim):
        # Router network
        self.router = nn.Sequential(
            nn.Linear(hidden_dim, 256),
            nn.ReLU(),
            nn.Linear(256, num_models),
        )
    
    def forward(self, hidden_states):
        # Compute routing weights based on input
        avg_hidden = torch.stack(hidden_states).mean(dim=0)
        routing_weights = F.softmax(self.router(avg_hidden), dim=-1)
        
        # Weighted combination
        fused = sum(w * h for w, h in zip(routing_weights, hidden_states))
        return fused
```

**Example**:
- Input: "Write code" → 80% code model, 20% others
- Input: "Explain physics" → 80% science model, 20% others
- Routing is INPUT-DEPENDENT!

**Pros**: Most flexible, input-dependent  
**Cons**: Most parameters, most complex

## Common Patterns

### Pattern 1: Domain Specialization

```python
# Three specialized models
models = [
    {"model_name": "codellama-7b", "role": "code"},
    {"model_name": "meditron-7b", "role": "medical"},
    {"model_name": "llama-3.1-8b", "role": "general"},
]

braided = BraidedLLM(
    model_configs=models,
    fusion_strategy="router",  # Dynamic routing
)

# Router automatically selects based on query
response = braided.generate("Write a Python function")  # Uses code model
response = braided.generate("Explain diabetes")  # Uses medical model
```

### Pattern 2: Size Diversity

```python
# Combine different sized models
models = [
    {"model_name": "llama-3.1-70B", "role": "reasoning"},  # Large, smart
    {"model_name": "phi-3-mini", "role": "fast"},  # Small, quick
]

braided = BraidedLLM(
    model_configs=models,
    fusion_strategy="router",
)

# Router can use large model for hard queries, small for easy ones
```

### Pattern 3: Training Diversity

```python
# Models trained on different data
models = [
    {"model_name": "model-2023-data", "role": "recent"},
    {"model_name": "model-books", "role": "knowledge"},
    {"model_name": "model-code", "role": "technical"},
]

# Combine different knowledge sources
braided = BraidedLLM(model_configs=models)
```

## Best Practices

### 1. Start Simple

```python
# Begin with 2 models, learned weighted fusion
models = [
    {"model_name": "model-a", "role": "a"},
    {"model_name": "model-b", "role": "b"},
]

braided = BraidedLLM(
    model_configs=models,
    fusion_strategy="learned_weighted",
    fusion_layers=[0, 8, 16],  # Just 3 fusion points
)
```

### 2. Use Quantization

```python
# 8-bit quantization saves memory
models = [
    {"model_name": "llama-3.1-8B", "quantization": "8bit"},
    {"model_name": "mistral-7B", "quantization": "8bit"},
]
```

### 3. Fuse Strategically

```python
# Don't fuse at every layer
fusion_layers = [0, 4, 8, 12, 16, 20]  # Good
# fusion_layers = [0, 1, 2, 3, 4, ...]  # Too much!

# Fuse at key points
fusion_layers = [0, 10, 20]  # Early, middle, late
```

### 4. Train on Domain Data

```python
# Fine-tune fusion on your specific use case
train_texts = [
    "Your domain-specific text 1",
    "Your domain-specific text 2",
    # ...
]

# Train fusion layers
train_fusion_layers(braided, train_texts)
```

### 5. Monitor Performance

```python
# Compare braided vs individual models
individual_score = evaluate(model_a)
braided_score = evaluate(braided)

print(f"Individual: {individual_score}")
print(f"Braided: {braided_score}")
print(f"Improvement: {braided_score - individual_score}")
```

## Troubleshooting

### Out of Memory

```python
# Use smaller models
models = [
    {"model_name": "phi-3-mini", "quantization": "8bit"},
]

# Fuse less frequently
fusion_layers = [0, 8, 16]  # Instead of [0, 4, 8, 12, 16, 20]

# Reduce batch size
batch_size = 1
```

### Slow Inference

```python
# Fuse less frequently
fusion_layers = [0, 10, 20]

# Use fewer models
model_configs = model_configs[:2]  # Just 2 models

# Use smaller models
models = [
    {"model_name": "phi-3-mini"},  # 3.8B params
    {"model_name": "phi-3-small"},  # 7B params
]
```

### Poor Results

```python
# Train fusion layers
train_fusion_layers(braided, your_data)

# Try different fusion strategy
fusion_strategy = "attention"  # Instead of "learned_weighted"

# Adjust fusion frequency
fusion_layers = [0, 2, 4, 6, 8, 10]  # More frequent
```

## Advanced Topics

### Custom Fusion Layer

```python
from models.fusion_layers import FusionLayer

class CustomFusion(FusionLayer):
    def __init__(self, num_models, hidden_dim):
        super().__init__()
        # Your custom architecture
        self.custom_layer = nn.Linear(hidden_dim * num_models, hidden_dim)
    
    def forward(self, hidden_states):
        # Your custom fusion logic
        concatenated = torch.cat(hidden_states, dim=-1)
        fused = self.custom_layer(concatenated)
        return fused

# Use it
braided = BraidedLLM(
    model_configs=models,
    fusion_strategy="custom",  # Will use your CustomFusion
)
```

### Layer-Specific Fusion

```python
# Different fusion strategies at different layers
braided.fusion_modules["0"] = LearnedWeightedFusion(...)  # Early layers
braided.fusion_modules["10"] = AttentionFusion(...)  # Middle layers
braided.fusion_modules["20"] = RouterFusion(...)  # Late layers
```

### Conditional Braiding

```python
# Only braid for certain types of queries
def smart_generate(query):
    if is_complex(query):
        # Use braiding for complex queries
        return braided.generate(query, use_braiding=True)
    else:
        # Use single model for simple queries
        return braided.models[0].generate(query)
```

## Resources

- **Tutorial**: Run `python examples/braiding_tutorial.py`
- **Tests**: Run `python examples/test_braiding.py`
- **Training**: Run `python scripts/train_fusion.py`
- **Architecture**: See `ARCHITECTURE.md`
- **Quick Start**: See `QUICKSTART.md`

## Summary

**Braiding = Combining models at hidden layer level**

Key steps:
1. Access hidden layers from each model
2. Fuse at specified layers
3. Continue with fused representation
4. Train only fusion layers (base models frozen)

Benefits:
- Combine specialized models
- Emergent capabilities
- Efficient training
- Flexible and modular

Start with `learned_weighted` fusion, 2 models, fuse every 4 layers. Experiment from there!
