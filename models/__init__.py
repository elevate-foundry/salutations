"""
Multi-LLM braiding models with full hidden layer access.
"""

from .model_wrapper import ModelWrapper
from .braided_model import BraidedLLM
from .fusion_layers import (
    LearnedWeightedFusion,
    AttentionFusion,
    RouterFusion
)

__all__ = [
    "ModelWrapper",
    "BraidedLLM",
    "LearnedWeightedFusion",
    "AttentionFusion",
    "RouterFusion",
]
