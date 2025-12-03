"""
Meta-Braider: An agent that learns to braid LLMs.

This agent learns:
1. Which models to combine
2. Which layers to fuse at
3. What fusion strategy to use
4. Optimal fusion parameters

The agent can then apply this knowledge to braid new LLMs.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .model_wrapper import ModelWrapper
from .braided_model import BraidedLLM
from .fusion_layers import FusionLayer


@dataclass
class BraidingDecision:
    """Decision made by the meta-braider."""
    model_weights: torch.Tensor  # Which models to use
    layer_selection: List[int]   # Which layers to fuse at
    fusion_strategy: str         # Which fusion strategy
    fusion_params: Dict[str, Any]  # Fusion hyperparameters


class MetaBraider(nn.Module):
    """
    An agent that learns to braid LLMs.
    
    The agent observes:
    - Model characteristics (size, domain, architecture)
    - Task requirements
    - Available compute
    
    The agent decides:
    - Which models to combine
    - Where to fuse (which layers)
    - How to fuse (fusion strategy)
    - Fusion hyperparameters
    """
    
    def __init__(
        self,
        model_pool: List[Dict[str, Any]],
        hidden_dim: int = 512,
        num_layers: int = 3,
    ):
        """
        Initialize meta-braider.
        
        Args:
            model_pool: Pool of available models to choose from
            hidden_dim: Hidden dimension for agent network
            num_layers: Number of transformer layers in agent
        """
        super().__init__()
        
        self.model_pool = model_pool
        self.num_models = len(model_pool)
        self.hidden_dim = hidden_dim
        
        # Model encoder: Encode model characteristics
        self.model_encoder = nn.Sequential(
            nn.Linear(self._get_model_feature_dim(), hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        
        # Task encoder: Encode task requirements
        self.task_encoder = nn.Sequential(
            nn.Linear(self._get_task_feature_dim(), hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        
        # Decision transformer: Learn braiding decisions
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=8,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True,
        )
        self.decision_transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )
        
        # Decision heads
        self.model_selector = nn.Linear(hidden_dim, self.num_models)  # Which models
        self.layer_selector = nn.Linear(hidden_dim, 32)  # Which layers (max 32)
        self.strategy_selector = nn.Linear(hidden_dim, 3)  # Which strategy
        self.param_predictor = nn.Linear(hidden_dim, 16)  # Fusion params
        
        logger.info(f"MetaBraider initialized with {self.num_models} models in pool")
    
    def _get_model_feature_dim(self) -> int:
        """Get dimension of model feature vector."""
        # Features: size, num_layers, hidden_dim, domain (one-hot), etc.
        return 10  # Simplified
    
    def _get_task_feature_dim(self) -> int:
        """Get dimension of task feature vector."""
        # Features: task type, complexity, required capabilities, etc.
        return 8  # Simplified
    
    def encode_model(self, model_info: Dict[str, Any]) -> torch.Tensor:
        """
        Encode model characteristics into feature vector.
        
        Args:
            model_info: Model metadata
        
        Returns:
            Feature vector
        """
        # Extract features
        features = []
        
        # Size (normalized)
        size = model_info.get("size", 7e9) / 1e10  # Normalize by 10B
        features.append(size)
        
        # Number of layers (normalized)
        num_layers = model_info.get("num_layers", 32) / 50
        features.append(num_layers)
        
        # Hidden dimension (normalized)
        hidden_dim = model_info.get("hidden_dim", 4096) / 8192
        features.append(hidden_dim)
        
        # Domain (one-hot: general, code, science, medical, creative)
        domain = model_info.get("domain", "general")
        domain_map = {"general": 0, "code": 1, "science": 2, "medical": 3, "creative": 4}
        domain_idx = domain_map.get(domain, 0)
        domain_onehot = [0.0] * 5
        domain_onehot[domain_idx] = 1.0
        features.extend(domain_onehot)
        
        # Quantization
        quant = 1.0 if model_info.get("quantization") else 0.0
        features.append(quant)
        
        # Training data recency (0-1)
        recency = model_info.get("recency", 0.5)
        features.append(recency)
        
        return torch.tensor(features, dtype=torch.float32)
    
    def encode_task(self, task_info: Dict[str, Any]) -> torch.Tensor:
        """
        Encode task requirements into feature vector.
        
        Args:
            task_info: Task metadata
        
        Returns:
            Feature vector
        """
        features = []
        
        # Task type (one-hot: qa, generation, code, reasoning, creative)
        task_type = task_info.get("type", "qa")
        type_map = {"qa": 0, "generation": 1, "code": 2, "reasoning": 3, "creative": 4}
        type_idx = type_map.get(task_type, 0)
        type_onehot = [0.0] * 5
        type_onehot[type_idx] = 1.0
        features.extend(type_onehot)
        
        # Complexity (0-1)
        complexity = task_info.get("complexity", 0.5)
        features.append(complexity)
        
        # Required capabilities (multi-hot)
        capabilities = task_info.get("capabilities", [])
        cap_vector = [
            1.0 if "reasoning" in capabilities else 0.0,
            1.0 if "knowledge" in capabilities else 0.0,
        ]
        features.extend(cap_vector)
        
        return torch.tensor(features, dtype=torch.float32)
    
    def forward(
        self,
        task_info: Dict[str, Any],
        compute_budget: float = 1.0,
    ) -> BraidingDecision:
        """
        Decide how to braid models for a given task.
        
        Args:
            task_info: Task requirements
            compute_budget: Available compute (0-1)
        
        Returns:
            Braiding decision
        """
        batch_size = 1
        
        # Encode all models in pool
        model_features = []
        for model_info in self.model_pool:
            feat = self.encode_model(model_info)
            model_features.append(feat)
        
        model_features = torch.stack(model_features).unsqueeze(0)  # (1, num_models, feat_dim)
        model_embeddings = self.model_encoder(model_features)  # (1, num_models, hidden_dim)
        
        # Encode task
        task_feat = self.encode_task(task_info).unsqueeze(0).unsqueeze(0)  # (1, 1, feat_dim)
        task_embedding = self.task_encoder(task_feat)  # (1, 1, hidden_dim)
        
        # Combine: [task, model1, model2, ..., modelN]
        combined = torch.cat([task_embedding, model_embeddings], dim=1)  # (1, 1+num_models, hidden_dim)
        
        # Decision transformer
        decision_features = self.decision_transformer(combined)  # (1, 1+num_models, hidden_dim)
        
        # Extract task-level decision (first token)
        task_decision = decision_features[:, 0, :]  # (1, hidden_dim)
        
        # Model selection: Which models to use
        model_logits = self.model_selector(task_decision)  # (1, num_models)
        model_weights = torch.sigmoid(model_logits)  # (1, num_models)
        
        # Consider compute budget
        model_weights = model_weights * compute_budget
        
        # Layer selection: Which layers to fuse at
        layer_logits = self.layer_selector(task_decision)  # (1, 32)
        layer_probs = torch.sigmoid(layer_logits)
        
        # Select top-k layers
        k = max(3, int(compute_budget * 8))  # More compute = more fusion points
        top_k_layers = torch.topk(layer_probs, k=k, dim=-1).indices[0].tolist()
        top_k_layers = sorted([l * 2 for l in top_k_layers])  # Scale to actual layer indices
        
        # Strategy selection: Which fusion strategy
        strategy_logits = self.strategy_selector(task_decision)  # (1, 3)
        strategy_idx = torch.argmax(strategy_logits, dim=-1).item()
        strategies = ["learned_weighted", "attention", "router"]
        selected_strategy = strategies[strategy_idx]
        
        # Fusion parameters
        fusion_params_raw = self.param_predictor(task_decision)  # (1, 16)
        fusion_params = {
            "temperature": torch.sigmoid(fusion_params_raw[0, 0]).item(),
            "dropout": torch.sigmoid(fusion_params_raw[0, 1]).item() * 0.3,
            "num_heads": int(torch.sigmoid(fusion_params_raw[0, 2]).item() * 16) + 1,
        }
        
        decision = BraidingDecision(
            model_weights=model_weights[0],
            layer_selection=top_k_layers,
            fusion_strategy=selected_strategy,
            fusion_params=fusion_params,
        )
        
        logger.info(f"MetaBraider decision:")
        logger.info(f"  Models: {model_weights[0].tolist()}")
        logger.info(f"  Layers: {top_k_layers}")
        logger.info(f"  Strategy: {selected_strategy}")
        logger.info(f"  Params: {fusion_params}")
        
        return decision
    
    def create_braided_model(
        self,
        decision: BraidingDecision,
        device: str = "cuda",
    ) -> BraidedLLM:
        """
        Create a braided model based on the decision.
        
        Args:
            decision: Braiding decision from forward pass
            device: Device to load models on
        
        Returns:
            Configured BraidedLLM
        """
        # Select models based on weights (top-k)
        k = 3  # Use top 3 models
        top_k_indices = torch.topk(decision.model_weights, k=k).indices.tolist()
        
        selected_models = [
            self.model_pool[idx] for idx in top_k_indices
        ]
        
        logger.info(f"Creating braided model with {len(selected_models)} models")
        
        # Create braided model
        braided = BraidedLLM(
            model_configs=selected_models,
            fusion_strategy=decision.fusion_strategy,
            fusion_layers=decision.layer_selection,
            device=device,
        )
        
        return braided
    
    def learn_from_feedback(
        self,
        task_info: Dict[str, Any],
        decision: BraidingDecision,
        performance: float,
        optimizer: torch.optim.Optimizer,
    ):
        """
        Learn from task performance feedback.
        
        Args:
            task_info: Task that was performed
            decision: Decision that was made
            performance: Performance score (0-1, higher is better)
            optimizer: Optimizer for updating parameters
        """
        # Compute reward
        reward = performance
        
        # Recompute decision
        new_decision = self.forward(task_info)
        
        # Compute loss: Encourage decisions that led to good performance
        # This is a simplified reinforcement learning approach
        
        # Model selection loss
        model_loss = -torch.log(new_decision.model_weights + 1e-8) * reward
        model_loss = model_loss.mean()
        
        # Total loss
        loss = model_loss
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        logger.info(f"MetaBraider learned from feedback: reward={reward:.3f}, loss={loss.item():.3f}")


class MetaBraiderTrainer:
    """
    Trainer for the meta-braider agent.
    
    Trains the agent to make good braiding decisions by:
    1. Trying different braiding configurations
    2. Evaluating performance
    3. Learning from feedback
    """
    
    def __init__(
        self,
        meta_braider: MetaBraider,
        eval_dataset: List[Dict[str, Any]],
        learning_rate: float = 1e-4,
    ):
        """
        Initialize trainer.
        
        Args:
            meta_braider: MetaBraider agent
            eval_dataset: Dataset for evaluation
            learning_rate: Learning rate
        """
        self.meta_braider = meta_braider
        self.eval_dataset = eval_dataset
        self.optimizer = torch.optim.Adam(
            meta_braider.parameters(),
            lr=learning_rate,
        )
        
        logger.info("MetaBraiderTrainer initialized")
    
    def train_episode(self, task: Dict[str, Any]) -> float:
        """
        Train on a single task episode.
        
        Args:
            task: Task to train on
        
        Returns:
            Performance score
        """
        # Get braiding decision
        decision = self.meta_braider.forward(task["info"])
        
        # Create braided model
        braided = self.meta_braider.create_braided_model(decision)
        
        # Evaluate on task
        performance = self.evaluate_braided_model(braided, task)
        
        # Learn from feedback
        self.meta_braider.learn_from_feedback(
            task_info=task["info"],
            decision=decision,
            performance=performance,
            optimizer=self.optimizer,
        )
        
        return performance
    
    def evaluate_braided_model(
        self,
        braided: BraidedLLM,
        task: Dict[str, Any],
    ) -> float:
        """
        Evaluate braided model on task.
        
        Args:
            braided: Braided model
            task: Task to evaluate on
        
        Returns:
            Performance score (0-1)
        """
        # Simplified evaluation
        # In practice, would run actual inference and compute metrics
        
        # Placeholder: Random performance for demonstration
        import random
        performance = random.random()
        
        logger.info(f"Evaluated braided model: performance={performance:.3f}")
        
        return performance
    
    def train(self, num_episodes: int = 100):
        """
        Train meta-braider for multiple episodes.
        
        Args:
            num_episodes: Number of training episodes
        """
        logger.info(f"Training MetaBraider for {num_episodes} episodes")
        
        for episode in range(num_episodes):
            # Sample random task
            task = self.eval_dataset[episode % len(self.eval_dataset)]
            
            # Train episode
            performance = self.train_episode(task)
            
            if (episode + 1) % 10 == 0:
                logger.info(f"Episode {episode + 1}/{num_episodes}: performance={performance:.3f}")
        
        logger.success("MetaBraider training complete!")
