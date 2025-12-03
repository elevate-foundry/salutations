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
    
    def __init__(self, num_models: int, hidden_dim: int, normalize: bool = True):
        """
        Initialize learned weighted fusion.
        
        Args:
            num_models: Number of models to fuse
            hidden_dim: Hidden dimension size
            normalize: Whether to normalize weights with softmax
        """
        super().__init__()
        
        self.num_models = num_models
        self.hidden_dim = hidden_dim
        self.normalize = normalize
        
        # Learnable weights for each model
        self.weights = nn.Parameter(torch.ones(num_models) / num_models)
        
        # Optional projection layer to align dimensions
        self.projection = nn.Linear(hidden_dim, hidden_dim)
    
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Fuse hidden states with learned weights.
        
        Args:
            hidden_states: List of tensors (batch, seq_len, hidden_dim)
        
        Returns:
            Fused tensor (batch, seq_len, hidden_dim)
        """
        assert len(hidden_states) == self.num_models, \
            f"Expected {self.num_models} hidden states, got {len(hidden_states)}"
        
        # Normalize weights if requested
        if self.normalize:
            weights = F.softmax(self.weights, dim=0)
        else:
            weights = self.weights
        
        # Weighted sum
        fused = sum(w * h for w, h in zip(weights, hidden_states))
        
        # Optional projection
        fused = self.projection(fused)
        
        return fused


class AttentionFusion(FusionLayer):
    """
    Cross-attention based fusion.
    
    Uses one model as query and others as key/value for attention-based fusion.
    """
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        """
        Initialize attention fusion.
        
        Args:
            hidden_dim: Hidden dimension size
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        
        assert hidden_dim % num_heads == 0, "hidden_dim must be divisible by num_heads"
        
        # Multi-head attention
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        
        # Layer norm
        self.layer_norm = nn.LayerNorm(hidden_dim)
        
        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout),
        )
        
        self.ffn_layer_norm = nn.LayerNorm(hidden_dim)
    
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Fuse hidden states using cross-attention.
        
        Args:
            hidden_states: List of tensors (batch, seq_len, hidden_dim)
        
        Returns:
            Fused tensor (batch, seq_len, hidden_dim)
        """
        # Use first model as query, concatenate others as key/value
        query = hidden_states[0]
        
        if len(hidden_states) > 1:
            # Concatenate other models along sequence dimension
            key_value = torch.cat(hidden_states[1:], dim=1)
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
        num_models: int,
        hidden_dim: int,
        router_hidden_dim: int = 256,
        temperature: float = 1.0,
    ):
        """
        Initialize router fusion.
        
        Args:
            num_models: Number of models to route between
            hidden_dim: Hidden dimension size
            router_hidden_dim: Hidden dimension for router network
            temperature: Temperature for softmax routing
        """
        super().__init__()
        
        self.num_models = num_models
        self.hidden_dim = hidden_dim
        self.temperature = temperature
        
        # Router network
        self.router = nn.Sequential(
            nn.Linear(hidden_dim, router_hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(router_hidden_dim, num_models),
        )
        
        # Optional expert-specific projections
        self.expert_projections = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim)
            for _ in range(num_models)
        ])
        
        # Final projection
        self.output_projection = nn.Linear(hidden_dim, hidden_dim)
    
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
        
        batch_size, seq_len, _ = hidden_states[0].shape
        
        # Compute routing weights based on average of all models
        avg_hidden = torch.stack(hidden_states).mean(dim=0)
        routing_logits = self.router(avg_hidden)  # (batch, seq_len, num_models)
        routing_weights = F.softmax(routing_logits / self.temperature, dim=-1)
        
        # Apply expert projections
        projected_states = [
            proj(h) for proj, h in zip(self.expert_projections, hidden_states)
        ]
        
        # Weighted combination
        # routing_weights: (batch, seq_len, num_models)
        # projected_states: list of (batch, seq_len, hidden_dim)
        stacked = torch.stack(projected_states, dim=-1)  # (batch, seq_len, hidden_dim, num_models)
        routing_weights_expanded = routing_weights.unsqueeze(2)  # (batch, seq_len, 1, num_models)
        
        fused = (stacked * routing_weights_expanded).sum(dim=-1)  # (batch, seq_len, hidden_dim)
        
        # Final projection
        output = self.output_projection(fused)
        
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
        num_models: int,
        hidden_dim: int,
        fusion_strategy: str = "attention",
    ):
        """
        Initialize hierarchical fusion.
        
        Args:
            num_models: Number of models to fuse
            hidden_dim: Hidden dimension size
            fusion_strategy: Strategy for each fusion stage (attention, weighted)
        """
        super().__init__()
        
        self.num_models = num_models
        self.hidden_dim = hidden_dim
        
        # Create fusion layers for hierarchical combination
        self.fusion_layers = nn.ModuleList()
        
        # Binary tree fusion
        num_stages = (num_models - 1).bit_length()
        for _ in range(num_stages):
            if fusion_strategy == "attention":
                layer = AttentionFusion(hidden_dim)
            else:
                layer = LearnedWeightedFusion(2, hidden_dim)
            self.fusion_layers.append(layer)
    
    def forward(self, hidden_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Fuse hidden states hierarchically.
        
        Args:
            hidden_states: List of tensors (batch, seq_len, hidden_dim)
        
        Returns:
            Fused tensor (batch, seq_len, hidden_dim)
        """
        current_states = list(hidden_states)
        
        # Progressively fuse pairs
        for fusion_layer in self.fusion_layers:
            if len(current_states) == 1:
                break
            
            next_states = []
            for i in range(0, len(current_states), 2):
                if i + 1 < len(current_states):
                    # Fuse pair
                    fused = fusion_layer([current_states[i], current_states[i + 1]])
                    next_states.append(fused)
                else:
                    # Odd one out, carry forward
                    next_states.append(current_states[i])
            
            current_states = next_states
        
        return current_states[0]
