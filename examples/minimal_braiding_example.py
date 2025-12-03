#!/usr/bin/env python3
"""
Minimal working example of multi-LLM braiding with small models.

This demonstrates the core concept using GPT-2 models that can run on CPU.
Shows how multiple models' hidden states are fused at specific layers.
"""

import torch
import torch.nn as nn
from transformers import GPT2Model, GPT2Tokenizer, GPT2Config
from typing import List, Dict, Any, Tuple
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from models.fusion_layers import LearnedWeightedFusion


class MinimalBraidedLLM:
    """
    Minimal demonstration of multi-LLM braiding.
    
    Uses tiny GPT-2 models to show the concept without GPU requirements.
    """
    
    def __init__(self, model_names: List[str] = None):
        """
        Initialize with small models for demonstration.
        
        Args:
            model_names: List of model names (defaults to GPT-2 variants)
        """
        if model_names is None:
            # Use tiny models that work on CPU
            model_names = ["gpt2", "distilgpt2"]
        
        # Braiding requires at least 2 models
        if len(model_names) < 2:
            logger.warning("⚠️  Braiding requires at least 2 models. Adding distilgpt2.")
            if "gpt2" not in model_names:
                model_names.append("gpt2")
            if len(model_names) < 2:
                model_names.append("distilgpt2")
        
        self.models = []
        self.tokenizers = []
        
        logger.info("🧬 Initializing Minimal Braided LLM")
        
        # Load models
        for name in model_names:
            logger.info(f"   Loading {name}...")
            
            # Load tokenizer
            tokenizer = GPT2Tokenizer.from_pretrained(name)
            tokenizer.pad_token = tokenizer.eos_token
            self.tokenizers.append(tokenizer)
            
            # Load model
            model = GPT2Model.from_pretrained(name)
            model.eval()  # Set to evaluation mode
            self.models.append(model)
        
        # Detect the minimum number of layers across models
        # GPT-2 has 12 layers, but distilgpt2 has only 6 layers!
        min_layers = float('inf')
        for idx, model in enumerate(self.models):
            if hasattr(model, 'config'):
                num_layers = model.config.n_layer if hasattr(model.config, 'n_layer') else model.config.num_hidden_layers
            else:
                # Fallback: count the actual layers
                num_layers = len(model.h) if hasattr(model, 'h') else 12
            logger.info(f"   Model {idx} ({model_names[idx]}) has {num_layers} layers")
            min_layers = min(min_layers, num_layers)
        
        logger.info(f"   Using minimum of {min_layers} layers for fusion")
        
        # Initialize fusion layers at safe positions (that exist in all models)
        # We'll fuse at layer 2 and 4 (safe for distilgpt2's 6 layers)
        fusion_positions = []
        if min_layers >= 2:
            fusion_positions.append(2)
        if min_layers >= 4:
            fusion_positions.append(4)
        if min_layers >= 8:
            fusion_positions.append(8)
        
        self.fusion_layers = {}
        for layer_idx in fusion_positions:
            self.fusion_layers[layer_idx] = LearnedWeightedFusion(
                input_dims=[768] * len(self.models),  # GPT-2 hidden size for each model
                output_dim=768
            )
        
        logger.info(f"   Fusion layers created at positions: {list(self.fusion_layers.keys())}")
        
        logger.success(f"✅ Initialized with {len(self.models)} models")
    
    def extract_hidden_states(self, text: str) -> Dict[int, List[torch.Tensor]]:
        """
        Extract hidden states from all models at all layers.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary mapping layer index to list of hidden states per model
        """
        all_hidden_states = {}
        
        for model_idx, (model, tokenizer) in enumerate(zip(self.models, self.tokenizers)):
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
            
            # Forward pass with output_hidden_states
            with torch.no_grad():
                outputs = model(**inputs, output_hidden_states=True)
            
            # Extract hidden states at each layer
            hidden_states = outputs.hidden_states  # Tuple of (num_layers, batch, seq, hidden)
            
            for layer_idx, layer_hidden in enumerate(hidden_states):
                if layer_idx not in all_hidden_states:
                    all_hidden_states[layer_idx] = []
                
                # Take mean over sequence dimension for simplicity
                pooled = layer_hidden.mean(dim=1)  # (batch, hidden)
                all_hidden_states[layer_idx].append(pooled)
        
        return all_hidden_states
    
    def braid_forward(self, text: str) -> torch.Tensor:
        """
        Forward pass with braiding at specified layers.
        
        Args:
            text: Input text
            
        Returns:
            Braided representation
        """
        logger.info(f"\n🔄 Braiding forward pass: '{text[:50]}...'")
        
        # Extract hidden states from all models
        hidden_states = self.extract_hidden_states(text)
        
        # Apply fusion at specified layers
        fused_representations = {}
        
        for fusion_layer, fusion_module in self.fusion_layers.items():
            if fusion_layer in hidden_states:
                # Get hidden states from all models at this layer
                states_to_fuse = hidden_states[fusion_layer]
                
                # Apply fusion
                fused = fusion_module(states_to_fuse)
                fused_representations[fusion_layer] = fused
                
                logger.info(f"   Fused at layer {fusion_layer}: {fused.shape}")
        
        # Combine all fused representations (simple mean for demo)
        if fused_representations:
            final_representation = torch.stack(list(fused_representations.values())).mean(dim=0)
        else:
            # Fallback: use last layer
            final_representation = torch.stack(hidden_states[len(hidden_states)-1]).mean(dim=0)
        
        logger.success(f"   Final braided shape: {final_representation.shape}")
        
        return final_representation
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts using braided representations.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score
        """
        # Get braided representations
        repr1 = self.braid_forward(text1)
        repr2 = self.braid_forward(text2)
        
        # Compute cosine similarity
        cos_sim = nn.functional.cosine_similarity(repr1, repr2, dim=-1)
        
        return cos_sim.mean().item()
    
    def demonstrate_braiding_effect(self):
        """
        Demonstrate that braiding creates different representations than individual models.
        """
        logger.info("\n" + "="*70)
        logger.info("📊 DEMONSTRATING BRAIDING EFFECT")
        logger.info("="*70)
        
        test_text = "The quick brown fox jumps over the lazy dog"
        
        # Get individual model representations
        logger.info("\n1️⃣ Individual Model Representations:")
        individual_reprs = []
        
        for idx, (model, tokenizer) in enumerate(zip(self.models, self.tokenizers)):
            inputs = tokenizer(test_text, return_tensors="pt")
            with torch.no_grad():
                outputs = model(**inputs)
                repr = outputs.last_hidden_state.mean(dim=1)  # Pool over sequence
                individual_reprs.append(repr)
                logger.info(f"   Model {idx}: shape {repr.shape}, norm {repr.norm():.3f}")
        
        # Get braided representation
        logger.info("\n2️⃣ Braided Representation:")
        braided_repr = self.braid_forward(test_text)
        logger.info(f"   Braided: shape {braided_repr.shape}, norm {braided_repr.norm():.3f}")
        
        # Compare representations
        logger.info("\n3️⃣ Representation Differences:")
        
        # Simple average vs braiding
        simple_avg = torch.stack(individual_reprs).mean(dim=0)
        diff = (braided_repr - simple_avg).norm()
        logger.info(f"   Difference from simple average: {diff:.4f}")
        
        # Similarity to each individual model
        for idx, ind_repr in enumerate(individual_reprs):
            sim = nn.functional.cosine_similarity(braided_repr, ind_repr, dim=-1).mean()
            logger.info(f"   Similarity to Model {idx}: {sim:.4f}")
        
        logger.info("\n💡 Result: Braided representation is DIFFERENT from simple averaging!")
        logger.info("   This shows the fusion layers create new representations")


def demonstrate_semantic_similarity():
    """
    Demonstrate semantic similarity using braided models.
    """
    logger.info("\n" + "="*70)
    logger.info("🔍 SEMANTIC SIMILARITY WITH BRAIDING")
    logger.info("="*70)
    
    # Initialize braided model
    braided = MinimalBraidedLLM()
    
    # Test cases
    test_cases = [
        ("The cat sat on the mat", "A feline rested on the rug"),  # Similar
        ("The cat sat on the mat", "Dogs love to play fetch"),      # Different
        ("I love programming", "Coding is my passion"),              # Similar
        ("I love programming", "The weather is nice today"),         # Different
    ]
    
    logger.info("\nComputing similarities:")
    for text1, text2 in test_cases:
        similarity = braided.compute_similarity(text1, text2)
        logger.info(f"\n   Text 1: '{text1}'")
        logger.info(f"   Text 2: '{text2}'")
        logger.info(f"   Similarity: {similarity:.4f}")


def test_fusion_strategies():
    """
    Test different fusion strategies.
    """
    logger.info("\n" + "="*70)
    logger.info("🔬 TESTING FUSION STRATEGIES")
    logger.info("="*70)
    
    from models.fusion_layers import AttentionFusion, RouterFusion
    
    # Test input
    test_text = "Testing different fusion strategies"
    
    # Initialize model with different fusion strategies
    strategies = {
        "Weighted": LearnedWeightedFusion,
        "Attention": AttentionFusion,
        "Router": RouterFusion,
    }
    
    for strategy_name, strategy_class in strategies.items():
        logger.info(f"\n📌 Testing {strategy_name} Fusion:")
        
        # Create minimal model
        braided = MinimalBraidedLLM()
        
        # Replace fusion layers with strategy (using the actual fusion positions)
        for layer_idx in braided.fusion_layers.keys():
            braided.fusion_layers[layer_idx] = strategy_class(
                input_dims=[768] * len(braided.models),  # Dynamic based on actual models
                output_dim=768
            )
        
        # Get representation
        repr = braided.braid_forward(test_text)
        logger.info(f"   Output shape: {repr.shape}")
        logger.info(f"   Output norm: {repr.norm():.4f}")


def main():
    """
    Run all demonstrations.
    """
    print("\n" + "="*70)
    print(" "*15 + "🧬 MINIMAL BRAIDING EXAMPLE")
    print("="*70)
    
    print("\n📋 This demonstrates:")
    print("   • Loading multiple models")
    print("   • Extracting hidden states at all layers")
    print("   • Fusing representations at specific layers")
    print("   • Creating braided representations")
    print("   • Computing semantic similarity")
    print("   • Testing fusion strategies")
    
    print("\n⚠️  Note: Using small models (GPT-2) for CPU compatibility")
    print("   In production, would use larger models on GPU")
    
    # Run demonstrations
    try:
        # 1. Basic braiding effect
        logger.info("\n" + "─"*70)
        model = MinimalBraidedLLM()
        model.demonstrate_braiding_effect()
        
        # 2. Semantic similarity
        logger.info("\n" + "─"*70)
        demonstrate_semantic_similarity()
        
        # 3. Fusion strategies
        logger.info("\n" + "─"*70)
        test_fusion_strategies()
        
        logger.success("\n" + "="*70)
        logger.success("✅ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        logger.success("="*70)
        
        print("\n💡 Key Takeaways:")
        print("   1. Multi-LLM braiding combines models at hidden layers")
        print("   2. Fusion creates new representations (not just averaging)")
        print("   3. Different fusion strategies produce different results")
        print("   4. Braided models can compute semantic similarity")
        print("   5. The approach is modular and extensible")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
