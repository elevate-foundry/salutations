"""
Test script for braiding functionality with hidden layer access.
"""

import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import BraidedLLM, ModelWrapper
from loguru import logger


def test_model_wrapper():
    """Test individual model wrapper."""
    logger.info("Testing ModelWrapper...")
    
    # Use a small model for testing
    model = ModelWrapper(
        model_name="microsoft/Phi-3-mini-4k-instruct",
        role="test",
        quantization="8bit",
    )
    
    # Test encoding
    text = "Hello, how are you?"
    inputs = model.encode(text)
    
    logger.info(f"Input shape: {inputs['input_ids'].shape}")
    
    # Test forward pass with hidden states
    output = model.forward(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
    )
    
    logger.info(f"Number of layers: {len(output.hidden_states)}")
    logger.info(f"Hidden state shape: {output.hidden_states[0].shape}")
    logger.info(f"Logits shape: {output.logits.shape}")
    
    # Test specific layer extraction
    layer_5_output = model.get_layer_output(
        input_ids=inputs["input_ids"],
        layer_idx=5,
    )
    logger.info(f"Layer 5 output shape: {layer_5_output.shape}")
    
    logger.success("ModelWrapper test passed!")
    return model


def test_braided_model():
    """Test braided model with multiple LLMs."""
    logger.info("Testing BraidedLLM...")
    
    # Use smaller models for testing
    model_configs = [
        {
            "model_name": "microsoft/Phi-3-mini-4k-instruct",
            "role": "reasoning",
            "quantization": "8bit",
        },
        {
            "model_name": "microsoft/Phi-3-mini-4k-instruct",
            "role": "code",
            "quantization": "8bit",
        },
    ]
    
    braided = BraidedLLM(
        model_configs=model_configs,
        fusion_strategy="learned_weighted",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    
    logger.info(f"Braided model:\n{braided}")
    
    # Test forward pass
    text = "Explain quantum computing in simple terms."
    inputs = braided.tokenizer(
        text,
        return_tensors="pt",
        padding=True,
    ).to(braided.device)
    
    logger.info("Running braided forward pass...")
    output, individual_outputs = braided.forward(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        return_individual_outputs=True,
    )
    
    logger.info(f"Fused output hidden states: {len(output.hidden_states)} layers")
    logger.info(f"Individual model outputs: {len(individual_outputs)}")
    
    # Test generation
    logger.info("Testing braided generation...")
    response = braided.generate(
        prompt="What is machine learning?",
        max_new_tokens=100,
        use_braiding=True,
    )
    
    logger.info(f"Generated response:\n{response}")
    
    # Test fusion layer saving/loading
    logger.info("Testing fusion layer save/load...")
    braided.save_fusion_layers("/tmp/test_fusion.pt")
    braided.load_fusion_layers("/tmp/test_fusion.pt")
    
    logger.success("BraidedLLM test passed!")
    return braided


def test_fusion_strategies():
    """Test different fusion strategies."""
    logger.info("Testing fusion strategies...")
    
    strategies = ["learned_weighted", "attention", "router"]
    
    for strategy in strategies:
        logger.info(f"\nTesting {strategy} fusion...")
        
        model_configs = [
            {
                "model_name": "microsoft/Phi-3-mini-4k-instruct",
                "role": "model_a",
                "quantization": "8bit",
            },
            {
                "model_name": "microsoft/Phi-3-mini-4k-instruct",
                "role": "model_b",
                "quantization": "8bit",
            },
        ]
        
        braided = BraidedLLM(
            model_configs=model_configs,
            fusion_strategy=strategy,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        
        # Quick test
        response = braided.generate(
            prompt="Hello!",
            max_new_tokens=20,
        )
        
        logger.info(f"{strategy} response: {response[:100]}...")
        logger.success(f"{strategy} fusion works!")


if __name__ == "__main__":
    logger.info("Starting braiding tests...\n")
    
    # Test individual wrapper
    test_model_wrapper()
    
    print("\n" + "="*60 + "\n")
    
    # Test braided model
    test_braided_model()
    
    print("\n" + "="*60 + "\n")
    
    # Test fusion strategies
    test_fusion_strategies()
    
    logger.success("\nAll tests passed!")
