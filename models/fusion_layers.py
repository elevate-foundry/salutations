"""
Fusion layers for braiding multiple LLM hidden states.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple
from abc import ABC, abstractmethod


class FusionLayer(nn.Module, ABC):
    """Base class for fusion strategies."""
    
    @abstractmethod
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Fuse hidden states from multiple models.
        
        Args:
            hidden_states: List of hidden states from different models
                          Each tensor shape: (batch, seq_len, hidden_dim)
        
        Returns:
            Fused hidden state: (batch, seq_len, hidden_dim)
        """
        pass


class LearnedWeightedFusion(FusionLayer):
    """
    Learned weighted fusion: α·model_A + β·model_B + γ·model_C
    
    Weights are learned parameters that can be trained to optimize
    the contribution of each model.
    """
    
    def __init__(self, input_dims: List[int], output_dim: int, normalize: bool = True):
        """
        Initialize learned weighted fusion.
        
        Args:
            input_dims: List of input dimensions from each model
            output_dim: Output dimension
            normalize: Whether to normalize weights with softmax
        """
        super().__init__()
        
        self.num_models = len(input_dims)
        self.input_dims = input_dims
        self.output_dim = output_dim
        self.normalize = normalize
        
        # Learnable weights for each model
        self.weights = nn.Parameter(torch.ones(self.num_models) / self.num_models)
        
        # Projection layers to align dimensions if needed
        self.projections = nn.ModuleList([
            nn.Linear(in_dim, output_dim) if in_dim != output_dim else nn.Identity()
            for in_dim in input_dims
        ])
    
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Fuse hidden states with learned weights.
        
        Args:
            hidden_states: List of tensors (batch, hidden_dim) or (batch, seq_len, hidden_dim)
        
        Returns:
            Fused tensor with output_dim
        """
        assert len(hidden_states) == self.num_models, \
            f"Expected {self.num_models} models, got {len(hidden_states)}"
        
        # Normalize weights if requested
        if self.normalize:
            weights = torch.softmax(self.weights, dim=0)
        else:
            weights = self.weights
        
        # Project each input to output dimension and apply weighted sum
        fused = None
        for i, (hidden, weight, projection) in enumerate(zip(hidden_states, weights, self.projections)):
            projected = projection(hidden)
            if fused is None:
                fused = weight * projected
            else:
                fused += weight * projected
        
        return fused


class AttentionFusion(FusionLayer):
    """
    Cross-attention based fusion.
    
    Uses one model as query and others as key/value for attention-based fusion.
    """
    
    def __init__(
        self,
        input_dims: List[int],
        output_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        """
        Initialize attention fusion.
        
        Args:
            input_dims: List of input dimensions from each model
            output_dim: Output dimension
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        super().__init__()
        
        self.num_models = len(input_dims)
        self.input_dims = input_dims
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.head_dim = output_dim // num_heads
        
        assert output_dim % num_heads == 0, "output_dim must be divisible by num_heads"
        
        # Projections to align input dimensions
        self.projections = nn.ModuleList([
            nn.Linear(in_dim, output_dim) if in_dim != output_dim else nn.Identity()
            for in_dim in input_dims
        ])
        
        # Multi-head attention
        self.attention = nn.MultiheadAttention(
            embed_dim=output_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        
        # Layer norm
        self.layer_norm = nn.LayerNorm(output_dim)
        
        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(output_dim, output_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(output_dim * 4, output_dim),
            nn.Dropout(dropout),
        )
        
        self.ffn_layer_norm = nn.LayerNorm(output_dim)
    
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Fuse hidden states using cross-attention.
        
        Args:
            hidden_states: List of tensors (batch, seq_len, hidden_dim)
        
        Returns:
            Fused tensor (batch, seq_len, hidden_dim)
        """
        # Project inputs to same dimension
        projected_states = [proj(h) for h, proj in zip(hidden_states, self.projections)]
        
        # Use first model as query, concatenate others as key/value
        query = projected_states[0]
        
        if len(projected_states) > 1:
            # Concatenate other models along sequence dimension
            key_value = torch.cat(projected_states[1:], dim=-2) if projected_states[0].dim() == 3 else torch.cat(projected_states[1:], dim=0)
        else:
            key_value = query
        
        # Self-attention with residual
        attn_output, _ = self.attention(query, key_value, key_value)
        hidden = self.layer_norm(query + attn_output)
        
        # Feed-forward with residual
        ffn_output = self.ffn(hidden)
        output = self.ffn_layer_norm(hidden + ffn_output)
        
        return output


class RouterFusion(FusionLayer):
    """
    Router-based fusion with dynamic model selection.
    
    A router network decides how much each model should contribute
    based on the input.
    """
    
    def __init__(
        self,
        input_dims: List[int],
        output_dim: int,
        num_experts: int = None,
        top_k: int = 2,
        router_hidden_dim: int = 256,
        temperature: float = 1.0,
    ):
        """
        Initialize router fusion.
        
        Args:
            input_dims: List of input dimensions from each model
            output_dim: Output dimension
            num_experts: Number of experts (defaults to number of models)
            top_k: Number of top experts to use
            router_hidden_dim: Hidden dimension for router network
            temperature: Temperature for softmax routing
        """
        super().__init__()
        
        self.num_models = len(input_dims)
        self.input_dims = input_dims
        self.output_dim = output_dim
        self.num_experts = num_experts or self.num_models
        self.top_k = min(top_k, self.num_experts)
        self.temperature = temperature
        
        # Projections to align input dimensions
        self.input_projections = nn.ModuleList([
            nn.Linear(in_dim, output_dim) if in_dim != output_dim else nn.Identity()
            for in_dim in input_dims
        ])
        
        # Router network
        self.router = nn.Sequential(
            nn.Linear(output_dim, router_hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(router_hidden_dim, self.num_experts),
        )
        
        # Optional expert-specific projections
        self.expert_projections = nn.ModuleList([
            nn.Linear(output_dim, output_dim)
            for _ in range(self.num_experts)
        ])
        
        # Final projection
        self.output_projection = nn.Linear(output_dim, output_dim)
    
    def forward(
        self,
        hidden_states: List[torch.Tensor],
        return_routing_weights: bool = False,
    ) -> torch.Tensor | Tuple[torch.Tensor, torch.Tensor]:
        """
        Fuse hidden states using learned routing.
        
        Args:
            hidden_states: List of tensors (batch, seq_len, hidden_dim)
            return_routing_weights: Whether to return routing weights
        
        Returns:
            Fused tensor (batch, seq_len, hidden_dim)
            Optionally routing weights (batch, seq_len, num_models)
        """
        assert len(hidden_states) == self.num_models
        
        # Project inputs
        projected_states = [proj(h) for h, proj in zip(hidden_states, self.input_projections)]
        
        # Handle both 2D and 3D tensors
        if projected_states[0].dim() == 3:
            batch_size, seq_len, _ = projected_states[0].shape
        else:
            batch_size = projected_states[0].shape[0]
            seq_len = 1  # Treat as single sequence
        
        # Compute routing weights based on average of all models
        avg_hidden = torch.stack(projected_states).mean(dim=0)
        routing_logits = self.router(avg_hidden)  # (batch, seq_len, num_models)
        routing_weights = F.softmax(routing_logits / self.temperature, dim=-1)
        
        # Apply expert projections and combine (simplified for now)
        output = torch.zeros_like(projected_states[0])
        for i in range(min(self.num_models, self.num_experts)):
            expert_output = self.expert_projections[i](projected_states[i])
            # Expand routing weights to match hidden dimensions
            if projected_states[0].dim() == 3:
                weights = routing_weights[..., i:i+1]  # (batch, seq_len, 1)
            else:
                weights = routing_weights[:, i:i+1]  # (batch, 1)
            output += weights * expert_output
        
        # Final projection
        output = self.output_projection(output)
        
        if return_routing_weights:
            return output, routing_weights
        return output


class HierarchicalFusion(FusionLayer):
    """
    Hierarchical fusion that combines models in stages.
    
    Useful when you have many models and want to fuse them progressively.
    """
    
    def __init__(
        self,
        input_dims: List[int],
        output_dim: int,
        num_layers: int = 2,
        fusion_at_each_layer: bool = True,
    ):
        """
        Initialize hierarchical fusion.
        
        Args:
            input_dims: List of input dimensions from each model
            output_dim: Output dimension
            num_layers: Number of fusion layers
            fusion_at_each_layer: Whether to fuse at each layer or just at the end
        """
        super().__init__()
        
        self.num_models = len(input_dims)
        self.input_dims = input_dims
        self.output_dim = output_dim
        self.num_layers = num_layers
        self.fusion_at_each_layer = fusion_at_each_layer
        
        # Input projections
        self.input_projections = nn.ModuleList([
            nn.Linear(in_dim, output_dim) if in_dim != output_dim else nn.Identity()
            for in_dim in input_dims
        ])
        
        # Create fusion layers for hierarchical processing
        self.fusion_layers = nn.ModuleList()
        for i in range(num_layers):
            if i == 0:
                # First layer: combine all models
                self.fusion_layers.append(
                    LearnedWeightedFusion([output_dim] * self.num_models, output_dim)
                )
            else:
                # Subsequent layers: refine the fusion
                self.fusion_layers.append(
                    AttentionFusion([output_dim], output_dim)
                )
    
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Fuse hidden states hierarchically.
        
        Args:
            hidden_states: List of tensors (batch, hidden_dim) or (batch, seq_len, hidden_dim)
        
        Returns:
            Fused tensor with output_dim
        """
        # Project inputs first
        projected_states = [proj(h) for h, proj in zip(hidden_states, self.input_projections)]
        
        # Apply fusion layers
        if self.num_layers == 1:
            # Single layer fusion
            return self.fusion_layers[0](projected_states)
        else:
            # Multi-layer fusion
            fused = self.fusion_layers[0](projected_states)
            for layer in self.fusion_layers[1:]:
                fused = layer([fused])
            return fused
