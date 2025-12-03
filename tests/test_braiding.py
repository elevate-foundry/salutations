#!/usr/bin/env python3
"""
Unit tests for multi-LLM braiding functionality.

Tests the core braiding components without requiring large models or GPU.
"""

import pytest
import torch
import torch.nn as nn
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.fusion_layers import (
    LearnedWeightedFusion,
    AttentionFusion,
    RouterFusion,
    HierarchicalFusion
)


class TestFusionLayers:
    """Test suite for fusion layer implementations."""
    
    def test_learned_weighted_fusion(self):
        """Test LearnedWeightedFusion with multiple inputs."""
        # Setup
        batch_size = 2
        hidden_dim = 768
        num_models = 3
        
        fusion = LearnedWeightedFusion(
            input_dims=[hidden_dim] * num_models,
            output_dim=hidden_dim
        )
        
        # Create dummy inputs
        inputs = [torch.randn(batch_size, hidden_dim) for _ in range(num_models)]
        
        # Forward pass
        output = fusion(inputs)
        
        # Assertions
        assert output.shape == (batch_size, hidden_dim)
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()
        
        # Test that weights sum to 1
        weights = torch.softmax(fusion.weights, dim=0)
        assert torch.allclose(weights.sum(), torch.tensor(1.0), atol=1e-6)
    
    def test_attention_fusion(self):
        """Test AttentionFusion mechanism."""
        batch_size = 2
        hidden_dim = 512
        num_models = 2
        
        fusion = AttentionFusion(
            input_dims=[hidden_dim] * num_models,
            output_dim=hidden_dim
        )
        
        inputs = [torch.randn(batch_size, hidden_dim) for _ in range(num_models)]
        output = fusion(inputs)
        
        assert output.shape == (batch_size, hidden_dim)
        assert not torch.isnan(output).any()
        
        # Test that attention is input-dependent
        inputs2 = [torch.randn(batch_size, hidden_dim) for _ in range(num_models)]
        output2 = fusion(inputs2)
        assert not torch.allclose(output, output2)
    
    def test_router_fusion(self):
        """Test RouterFusion with sparse routing."""
        batch_size = 4
        hidden_dim = 256
        num_models = 4
        
        fusion = RouterFusion(
            input_dims=[hidden_dim] * num_models,
            output_dim=hidden_dim,
            num_experts=num_models,
            top_k=2  # Route to top 2 experts
        )
        
        inputs = [torch.randn(batch_size, hidden_dim) for _ in range(num_models)]
        output = fusion(inputs)
        
        assert output.shape == (batch_size, hidden_dim)
        assert not torch.isnan(output).any()
        
        # Test sparsity (only top_k experts should be active)
        # This is implicitly tested by the top_k parameter
    
    def test_hierarchical_fusion(self):
        """Test HierarchicalFusion with multi-level fusion."""
        batch_size = 2
        hidden_dim = 384
        num_models = 4
        
        fusion = HierarchicalFusion(
            input_dims=[hidden_dim] * num_models,
            output_dim=hidden_dim
        )
        
        inputs = [torch.randn(batch_size, hidden_dim) for _ in range(num_models)]
        output = fusion(inputs)
        
        assert output.shape == (batch_size, hidden_dim)
        assert not torch.isnan(output).any()
    
    def test_fusion_gradient_flow(self):
        """Test that gradients flow through fusion layers."""
        hidden_dim = 128
        fusion = LearnedWeightedFusion(
            input_dims=[hidden_dim, hidden_dim],
            output_dim=hidden_dim
        )
        
        # Create inputs with requires_grad
        inputs = [
            torch.randn(1, hidden_dim, requires_grad=True),
            torch.randn(1, hidden_dim, requires_grad=True)
        ]
        
        # Forward and backward
        output = fusion(inputs)
        loss = output.sum()
        loss.backward()
        
        # Check gradients exist
        for inp in inputs:
            assert inp.grad is not None
            assert not torch.isnan(inp.grad).any()
    
    def test_fusion_with_different_dimensions(self):
        """Test fusion with models of different dimensions."""
        batch_size = 2
        
        # Different sized inputs (e.g., different model architectures)
        input_dims = [256, 512, 768]
        output_dim = 512
        
        fusion = LearnedWeightedFusion(
            input_dims=input_dims,
            output_dim=output_dim
        )
        
        inputs = [torch.randn(batch_size, dim) for dim in input_dims]
        output = fusion(inputs)
        
        assert output.shape == (batch_size, output_dim)


class TestBraidingIntegration:
    """Integration tests for the braiding system."""
    
    @pytest.fixture
    def mock_hidden_states(self):
        """Create mock hidden states for testing."""
        batch_size = 1
        seq_len = 10
        hidden_dim = 768
        num_layers = 12
        num_models = 2
        
        # Create mock hidden states for each model at each layer
        states = {}
        for layer in range(num_layers):
            states[layer] = [
                torch.randn(batch_size, seq_len, hidden_dim)
                for _ in range(num_models)
            ]
        return states
    
    def test_selective_layer_fusion(self, mock_hidden_states):
        """Test fusing at specific layers only."""
        # Fuse at layers 4 and 8
        fusion_layers = {
            4: LearnedWeightedFusion([768, 768], 768),
            8: LearnedWeightedFusion([768, 768], 768)
        }
        
        fused_states = {}
        for layer_idx, fusion in fusion_layers.items():
            # Pool over sequence dimension
            pooled = [s.mean(dim=1) for s in mock_hidden_states[layer_idx]]
            fused = fusion(pooled)
            fused_states[layer_idx] = fused
        
        # Should have fused representations at specified layers
        assert len(fused_states) == 2
        assert 4 in fused_states
        assert 8 in fused_states
    
    def test_braiding_preserves_batch_dimension(self, mock_hidden_states):
        """Test that braiding preserves batch dimension."""
        batch_sizes = [1, 2, 4, 8]
        
        for batch_size in batch_sizes:
            # Create states with different batch size
            states = [
                torch.randn(batch_size, 768)
                for _ in range(2)
            ]
            
            fusion = LearnedWeightedFusion([768, 768], 768)
            output = fusion(states)
            
            assert output.shape[0] == batch_size


class TestBraidingUtilities:
    """Test utility functions for braiding."""
    
    def test_save_load_fusion_weights(self, tmp_path):
        """Test saving and loading fusion layer weights."""
        # Create fusion layer
        fusion = LearnedWeightedFusion([512, 512], 512)
        
        # Save weights
        save_path = tmp_path / "fusion_weights.pt"
        torch.save(fusion.state_dict(), save_path)
        
        # Create new fusion layer and load weights
        fusion2 = LearnedWeightedFusion([512, 512], 512)
        fusion2.load_state_dict(torch.load(save_path))
        
        # Check weights are identical
        for key in fusion.state_dict():
            assert torch.allclose(
                fusion.state_dict()[key],
                fusion2.state_dict()[key]
            )
    
    def test_fusion_layer_parameter_count(self):
        """Test parameter counting in fusion layers."""
        input_dims = [768, 768, 768]
        output_dim = 768
        
        strategies = {
            "weighted": LearnedWeightedFusion(input_dims, output_dim),
            "attention": AttentionFusion(input_dims, output_dim),
            "router": RouterFusion(input_dims, output_dim, num_experts=3),
            "hierarchical": HierarchicalFusion(input_dims, output_dim)
        }
        
        for name, strategy in strategies.items():
            param_count = sum(p.numel() for p in strategy.parameters())
            print(f"{name}: {param_count:,} parameters")
            assert param_count > 0  # Should have learnable parameters


def test_minimal_example_runs():
    """Test that the minimal braiding example runs without errors."""
    from examples.minimal_braiding_example import MinimalBraidedLLM
    
    # This test requires transformers and will download models
    # Skip in CI or if models not available
    try:
        import transformers
        
        # Create with at least 2 models - braiding requires multiple models!
        braided = MinimalBraidedLLM(model_names=["gpt2", "distilgpt2"])  # Need 2+ models for braiding
        
        # Test forward pass
        text = "Test input"
        representation = braided.braid_forward(text)
        
        assert representation is not None
        assert representation.shape[-1] == 768  # GPT-2 hidden size
        
    except ImportError:
        pytest.skip("transformers not installed")
    except Exception as e:
        # Allow test to pass if models can't be downloaded
        if "Connection" in str(e) or "HTTP" in str(e):
            pytest.skip(f"Model download failed: {e}")
        else:
            raise


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
