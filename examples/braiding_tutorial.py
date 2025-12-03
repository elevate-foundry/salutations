"""
Braiding Tutorial - Learn how to braid LLMs step by step.

This tutorial walks through:
1. Accessing hidden layers
2. Simple fusion
3. Multi-model braiding
4. Training fusion layers
"""

import torch
import torch.nn as nn
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ModelWrapper, BraidedLLM
from loguru import logger


# ============================================================================
# STEP 1: Access Hidden Layers from a Single Model
# ============================================================================

def step1_access_hidden_layers():
    """
    Learn how to access hidden layers from a single model.
    """
    logger.info("=" * 60)
    logger.info("STEP 1: Accessing Hidden Layers")
    logger.info("=" * 60)
    
    # Load a small model
    model = ModelWrapper(
        model_name="microsoft/Phi-3-mini-4k-instruct",
        role="example",
        quantization="8bit",
    )
    
    # Encode some text
    text = "The quick brown fox jumps over the lazy dog."
    inputs = model.encode(text)
    
    logger.info(f"\nInput text: {text}")
    logger.info(f"Input shape: {inputs['input_ids'].shape}")
    
    # Forward pass - get ALL hidden states
    output = model.forward(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
    )
    
    logger.info(f"\n✓ Model has {len(output.hidden_states)} layers")
    logger.info(f"✓ Each layer output shape: {output.hidden_states[0].shape}")
    logger.info(f"  Format: (batch_size, sequence_length, hidden_dimension)")
    
    # Look at specific layers
    logger.info("\n📊 Layer-by-layer analysis:")
    for i in [0, 5, 10, 15, -1]:
        if i == -1:
            layer = output.hidden_states[-1]
            logger.info(f"  Layer {len(output.hidden_states)-1} (final): {layer.shape}")
        else:
            layer = output.hidden_states[i]
            logger.info(f"  Layer {i}: {layer.shape}")
    
    # Key insight: You can extract ANY layer!
    layer_7 = model.get_layer_output(
        input_ids=inputs["input_ids"],
        layer_idx=7,
    )
    logger.info(f"\n✓ Extracted just layer 7: {layer_7.shape}")
    
    logger.success("\n✅ Step 1 Complete: You can now access any hidden layer!")
    return model, inputs, output


# ============================================================================
# STEP 2: Simple Fusion - Combine Two Layers
# ============================================================================

def step2_simple_fusion():
    """
    Learn how to fuse hidden states from different layers.
    """
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Simple Fusion")
    logger.info("=" * 60)
    
    model = ModelWrapper(
        model_name="microsoft/Phi-3-mini-4k-instruct",
        role="example",
        quantization="8bit",
    )
    
    text = "Machine learning is fascinating."
    inputs = model.encode(text)
    output = model.forward(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
    )
    
    # Get two different layers
    layer_5 = output.hidden_states[5]   # Middle layer
    layer_15 = output.hidden_states[15]  # Late layer
    
    logger.info(f"\nLayer 5 (concepts): {layer_5.shape}")
    logger.info(f"Layer 15 (reasoning): {layer_15.shape}")
    
    # Simple fusion: weighted average
    alpha = 0.6  # Weight for layer 5
    beta = 0.4   # Weight for layer 15
    
    fused = alpha * layer_5 + beta * layer_15
    
    logger.info(f"\n✓ Fused representation: {fused.shape}")
    logger.info(f"  Formula: {alpha} × layer_5 + {beta} × layer_15")
    
    # This is the CORE idea of braiding!
    logger.info("\n💡 Key Insight:")
    logger.info("  Instead of using just the final layer, we combine")
    logger.info("  different layers to get a richer representation.")
    
    logger.success("\n✅ Step 2 Complete: You understand basic fusion!")
    return fused


# ============================================================================
# STEP 3: Multi-Model Braiding
# ============================================================================

def step3_multi_model_braiding():
    """
    Learn how to braid multiple models together.
    """
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Multi-Model Braiding")
    logger.info("=" * 60)
    
    # Create two models (in practice, these would be different models)
    logger.info("\n📦 Loading two models...")
    
    model_a = ModelWrapper(
        model_name="microsoft/Phi-3-mini-4k-instruct",
        role="model_a",
        quantization="8bit",
    )
    
    model_b = ModelWrapper(
        model_name="microsoft/Phi-3-mini-4k-instruct",
        role="model_b",
        quantization="8bit",
    )
    
    # Same input for both
    text = "Explain neural networks."
    inputs_a = model_a.encode(text)
    inputs_b = model_b.encode(text)
    
    # Get hidden states from both
    logger.info(f"\n🔄 Processing: '{text}'")
    output_a = model_a.forward(
        input_ids=inputs_a["input_ids"],
        attention_mask=inputs_a["attention_mask"],
    )
    output_b = model_b.forward(
        input_ids=inputs_b["input_ids"],
        attention_mask=inputs_b["attention_mask"],
    )
    
    # Fuse at layer 10
    layer_idx = 10
    hidden_a = output_a.hidden_states[layer_idx]
    hidden_b = output_b.hidden_states[layer_idx]
    
    logger.info(f"\n📊 At layer {layer_idx}:")
    logger.info(f"  Model A output: {hidden_a.shape}")
    logger.info(f"  Model B output: {hidden_b.shape}")
    
    # Simple fusion
    fused = 0.5 * hidden_a + 0.5 * hidden_b
    
    logger.info(f"\n✓ Fused output: {fused.shape}")
    logger.info(f"  This combines knowledge from BOTH models!")
    
    # The magic: You can do this at MULTIPLE layers
    logger.info("\n🎯 Braiding Strategy:")
    logger.info("  Layer 0:  Fuse(Model_A[0], Model_B[0])")
    logger.info("  Layer 1-3: Continue with fused state")
    logger.info("  Layer 4:  Fuse(Model_A[4], Model_B[4])")
    logger.info("  Layer 5-7: Continue with fused state")
    logger.info("  ...")
    logger.info("  Final: Combined output from both models")
    
    logger.success("\n✅ Step 3 Complete: You understand multi-model braiding!")
    return fused


# ============================================================================
# STEP 4: Using BraidedLLM Class
# ============================================================================

def step4_braided_llm_class():
    """
    Learn how to use the BraidedLLM class for automatic braiding.
    """
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Using BraidedLLM Class")
    logger.info("=" * 60)
    
    # Configure models to braid
    model_configs = [
        {
            "model_name": "microsoft/Phi-3-mini-4k-instruct",
            "role": "reasoning",
            "quantization": "8bit",
        },
        {
            "model_name": "microsoft/Phi-3-mini-4k-instruct",
            "role": "creative",
            "quantization": "8bit",
        },
    ]
    
    logger.info("\n🏗️  Creating braided model...")
    logger.info(f"  Number of models: {len(model_configs)}")
    logger.info(f"  Fusion strategy: learned_weighted")
    
    # Create braided model
    braided = BraidedLLM(
        model_configs=model_configs,
        fusion_strategy="learned_weighted",  # Trainable weights
        fusion_layers=[0, 4, 8, 12],  # Fuse at these layers
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    
    logger.info(f"\n✓ Braided model created!")
    logger.info(f"  Fusion at layers: {braided.fusion_layer_indices}")
    logger.info(f"  Number of fusion modules: {len(braided.fusion_modules)}")
    
    # Generate with braiding
    prompt = "What is the meaning of life?"
    logger.info(f"\n🎨 Generating with braided model...")
    logger.info(f"  Prompt: '{prompt}'")
    
    response = braided.generate(
        prompt=prompt,
        max_new_tokens=50,
        use_braiding=True,
    )
    
    logger.info(f"\n📝 Response:\n{response}")
    
    # Show what's happening under the hood
    logger.info("\n🔍 What happened:")
    logger.info("  1. Both models processed the input")
    logger.info("  2. At layers 0, 4, 8, 12: Fusion combined their representations")
    logger.info("  3. Between fusion layers: Models continued with fused state")
    logger.info("  4. Final output: Combined knowledge from both models")
    
    logger.success("\n✅ Step 4 Complete: You can use BraidedLLM!")
    return braided


# ============================================================================
# STEP 5: Understanding Fusion Strategies
# ============================================================================

def step5_fusion_strategies():
    """
    Learn about different fusion strategies.
    """
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Fusion Strategies")
    logger.info("=" * 60)
    
    logger.info("\n📚 Three main fusion strategies:\n")
    
    # 1. Learned Weighted Fusion
    logger.info("1️⃣  LEARNED WEIGHTED FUSION (Simplest)")
    logger.info("   Formula: fused = α·model_A + β·model_B + γ·model_C")
    logger.info("   - α, β, γ are LEARNED parameters")
    logger.info("   - Normalized with softmax")
    logger.info("   - Fast and efficient")
    logger.info("   - Good starting point")
    logger.info("   Example:")
    logger.info("     Initial: fused = 0.33·A + 0.33·B + 0.33·C")
    logger.info("     After training: fused = 0.5·A + 0.3·B + 0.2·C")
    logger.info("     (Model A learned to be more important!)\n")
    
    # 2. Attention Fusion
    logger.info("2️⃣  ATTENTION FUSION (More Expressive)")
    logger.info("   Formula: fused = CrossAttention(query=A, key=B,C, value=B,C)")
    logger.info("   - Uses multi-head attention")
    logger.info("   - One model as query, others as context")
    logger.info("   - More parameters, more expressive")
    logger.info("   - Better for complex interactions")
    logger.info("   Example:")
    logger.info("     Model A attends to relevant parts of Models B & C")
    logger.info("     Different tokens can use different models!\n")
    
    # 3. Router Fusion
    logger.info("3️⃣  ROUTER FUSION (Most Dynamic)")
    logger.info("   Formula: weights = Router(input); fused = Σ(weights[i] · model_i)")
    logger.info("   - Router network decides weights based on INPUT")
    logger.info("   - Mixture-of-Experts style")
    logger.info("   - Different inputs use different models")
    logger.info("   - Most flexible")
    logger.info("   Example:")
    logger.info("     Input: 'Write code' → Router: 70% code_model, 30% others")
    logger.info("     Input: 'Explain physics' → Router: 80% science_model, 20% others\n")
    
    # Visual comparison
    logger.info("📊 When to use each:\n")
    logger.info("  Learned Weighted → Start here, fast, simple")
    logger.info("  Attention       → Need complex interactions")
    logger.info("  Router          → Want input-dependent fusion")
    
    logger.success("\n✅ Step 5 Complete: You understand fusion strategies!")


# ============================================================================
# STEP 6: Training Fusion Layers
# ============================================================================

def step6_training_fusion():
    """
    Learn how to train fusion layers.
    """
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Training Fusion Layers")
    logger.info("=" * 60)
    
    logger.info("\n🎯 Key Concept: Train ONLY fusion, freeze base models\n")
    
    # Create braided model
    model_configs = [
        {"model_name": "microsoft/Phi-3-mini-4k-instruct", "role": "a", "quantization": "8bit"},
        {"model_name": "microsoft/Phi-3-mini-4k-instruct", "role": "b", "quantization": "8bit"},
    ]
    
    braided = BraidedLLM(
        model_configs=model_configs,
        fusion_strategy="learned_weighted",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    
    # Count parameters BEFORE freezing
    total_params = sum(p.numel() for p in braided.parameters())
    logger.info(f"📊 Total parameters: {total_params:,}")
    
    # FREEZE base models
    logger.info("\n🔒 Freezing base model parameters...")
    for model in braided.models:
        for param in model.parameters():
            param.requires_grad = False
    
    # UNFREEZE fusion layers
    logger.info("🔓 Unfreezing fusion layer parameters...")
    for param in braided.fusion_modules.parameters():
        param.requires_grad = True
    
    # Count trainable parameters
    trainable_params = sum(p.numel() for p in braided.parameters() if p.requires_grad)
    logger.info(f"\n✓ Trainable parameters: {trainable_params:,}")
    logger.info(f"✓ Frozen parameters: {total_params - trainable_params:,}")
    logger.info(f"✓ Training only {100 * trainable_params / total_params:.2f}% of parameters!")
    
    logger.info("\n💡 Why this matters:")
    logger.info("  - Base models already trained (billions of tokens)")
    logger.info("  - We only learn HOW to combine them")
    logger.info("  - Much faster training")
    logger.info("  - Less data needed")
    logger.info("  - Can use smaller GPU")
    
    # Training loop (pseudo-code)
    logger.info("\n📝 Training loop (pseudo-code):")
    logger.info("""
    optimizer = AdamW(braided.fusion_modules.parameters())
    
    for batch in dataloader:
        # Forward pass (fusion layers active)
        output = braided.forward(batch['input_ids'])
        
        # Compute loss (e.g., language modeling)
        loss = compute_loss(output.logits, batch['labels'])
        
        # Backward (only fusion layers update)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    
    # Save just the fusion weights
    braided.save_fusion_layers('fusion.pt')
    """)
    
    logger.success("\n✅ Step 6 Complete: You understand fusion training!")


# ============================================================================
# STEP 7: Practical Example - Domain Specialization
# ============================================================================

def step7_practical_example():
    """
    Practical example: Combining specialized models.
    """
    logger.info("\n" + "=" * 60)
    logger.info("STEP 7: Practical Example - Domain Specialization")
    logger.info("=" * 60)
    
    logger.info("\n🎯 Use Case: Multi-Domain Expert System\n")
    
    logger.info("Scenario:")
    logger.info("  You want an AI that's good at:")
    logger.info("  - Writing code")
    logger.info("  - Explaining science")
    logger.info("  - Creative writing")
    
    logger.info("\n❌ Traditional Approach:")
    logger.info("  Train one huge model on all domains")
    logger.info("  Problems:")
    logger.info("    - Expensive")
    logger.info("    - May not excel at any one thing")
    logger.info("    - Hard to update one domain")
    
    logger.info("\n✅ Braiding Approach:")
    logger.info("  Use three specialized models:")
    
    example_config = """
    model_configs = [
        {
            "model_name": "codellama-7b",
            "role": "code",
            "quantization": "8bit",
        },
        {
            "model_name": "science-llm-7b",
            "role": "science",
            "quantization": "8bit",
        },
        {
            "model_name": "creative-llm-7b",
            "role": "creative",
            "quantization": "8bit",
        },
    ]
    
    braided = BraidedLLM(
        model_configs=model_configs,
        fusion_strategy="router",  # Dynamic routing!
        fusion_layers=[0, 4, 8, 12, 16, 20],
    )
    """
    
    logger.info(example_config)
    
    logger.info("\n🎨 How it works:")
    logger.info("  Query: 'Write a Python function'")
    logger.info("    → Router: 80% code model, 10% science, 10% creative")
    logger.info("  Query: 'Explain quantum mechanics'")
    logger.info("    → Router: 10% code, 80% science, 10% creative")
    logger.info("  Query: 'Write a poem about stars'")
    logger.info("    → Router: 5% code, 20% science, 75% creative")
    
    logger.info("\n✨ Benefits:")
    logger.info("  ✓ Each model stays specialized")
    logger.info("  ✓ Can update one without retraining all")
    logger.info("  ✓ Dynamic combination based on query")
    logger.info("  ✓ Best of all worlds")
    
    logger.success("\n✅ Step 7 Complete: You see practical applications!")


# ============================================================================
# Main Tutorial Runner
# ============================================================================

def run_tutorial():
    """Run the complete braiding tutorial."""
    
    logger.info("\n" + "=" * 60)
    logger.info("🎓 LLM BRAIDING TUTORIAL")
    logger.info("=" * 60)
    logger.info("\nThis tutorial will teach you how to braid LLMs step by step.\n")
    
    input("Press Enter to start Step 1...")
    step1_access_hidden_layers()
    
    input("\nPress Enter to continue to Step 2...")
    step2_simple_fusion()
    
    input("\nPress Enter to continue to Step 3...")
    step3_multi_model_braiding()
    
    input("\nPress Enter to continue to Step 4...")
    step4_braided_llm_class()
    
    input("\nPress Enter to continue to Step 5...")
    step5_fusion_strategies()
    
    input("\nPress Enter to continue to Step 6...")
    step6_training_fusion()
    
    input("\nPress Enter to continue to Step 7...")
    step7_practical_example()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 TUTORIAL COMPLETE!")
    logger.info("=" * 60)
    logger.info("\n📚 What you learned:")
    logger.info("  1. How to access hidden layers from any model")
    logger.info("  2. How to fuse representations")
    logger.info("  3. How to braid multiple models")
    logger.info("  4. How to use the BraidedLLM class")
    logger.info("  5. Different fusion strategies")
    logger.info("  6. How to train fusion layers")
    logger.info("  7. Practical applications")
    logger.info("\n🚀 Next steps:")
    logger.info("  - Try examples/test_braiding.py")
    logger.info("  - Experiment with different fusion strategies")
    logger.info("  - Train fusion layers on your data")
    logger.info("  - Build your own multi-domain expert!")
    logger.info("\n")


if __name__ == "__main__":
    run_tutorial()
