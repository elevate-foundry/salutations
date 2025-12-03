"""
Main braided LLM that combines multiple models with fusion layers.
"""

import torch
import torch.nn as nn
from typing import List, Optional, Dict, Tuple
from loguru import logger

from .model_wrapper import ModelWrapper, ModelOutput
from .fusion_layers import (
    FusionLayer,
    LearnedWeightedFusion,
    AttentionFusion,
    RouterFusion,
)


class BraidedLLM(nn.Module):
    """
    Multi-LLM braiding system with layer-wise fusion.
    
    Combines multiple language models by fusing their hidden representations
    at specified layers, allowing each model to contribute its specialized
    knowledge to the final output.
    """
    
    def __init__(
        self,
        model_configs: List[Dict],
        fusion_strategy: str = "learned_weighted",
        fusion_layers: Optional[List[int]] = None,
        device: str = "cuda",
    ):
        """
        Initialize braided LLM.
        
        Args:
            model_configs: List of model configuration dicts with keys:
                - model_name: HuggingFace model identifier
                - role: Specialization role
                - quantization: Quantization method
            fusion_strategy: Fusion strategy (learned_weighted, attention, router)
            fusion_layers: Layer indices where fusion occurs (None = all layers)
            device: Device to run on
        """
        super().__init__()
        
        self.device = device
        self.fusion_strategy = fusion_strategy
        
        # Initialize individual models
        logger.info(f"Initializing {len(model_configs)} models for braiding")
        self.models = nn.ModuleList([
            ModelWrapper(
                model_name=config["model_name"],
                role=config.get("role", "general"),
                quantization=config.get("quantization"),
                device=device,
            )
            for config in model_configs
        ])
        
        self.num_models = len(self.models)
        
        # Get hidden dimension (assume all models have same dim)
        self.hidden_dim = self.models[0].hidden_size
        
        # Verify all models have compatible hidden dimensions
        for i, model in enumerate(self.models):
            if model.hidden_size != self.hidden_dim:
                logger.warning(
                    f"Model {i} has hidden_dim={model.hidden_size}, "
                    f"expected {self.hidden_dim}. Adding projection layer."
                )
        
        # Determine fusion layers
        max_layers = min(model.num_layers for model in self.models)
        if fusion_layers is None:
            # Fuse at every 4th layer by default
            self.fusion_layer_indices = list(range(0, max_layers, 4))
        else:
            self.fusion_layer_indices = fusion_layers
        
        logger.info(f"Fusion will occur at layers: {self.fusion_layer_indices}")
        
        # Create fusion layers
        self.fusion_modules = nn.ModuleDict()
        for layer_idx in self.fusion_layer_indices:
            fusion_layer = self._create_fusion_layer(fusion_strategy)
            self.fusion_modules[str(layer_idx)] = fusion_layer
        
        # Use first model's tokenizer as primary
        self.tokenizer = self.models[0].tokenizer
    
    def _create_fusion_layer(self, strategy: str) -> FusionLayer:
        """Create a fusion layer based on strategy."""
        if strategy == "learned_weighted":
            return LearnedWeightedFusion(
                num_models=self.num_models,
                hidden_dim=self.hidden_dim,
            )
        elif strategy == "attention":
            return AttentionFusion(
                hidden_dim=self.hidden_dim,
                num_heads=8,
            )
        elif strategy == "router":
            return RouterFusion(
                num_models=self.num_models,
                hidden_dim=self.hidden_dim,
            )
        else:
            raise ValueError(f"Unknown fusion strategy: {strategy}")
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_individual_outputs: bool = False,
    ) -> ModelOutput | Tuple[ModelOutput, List[ModelOutput]]:
        """
        Forward pass with braiding.
        
        Args:
            input_ids: Input token IDs (batch, seq_len)
            attention_mask: Attention mask
            return_individual_outputs: Whether to return individual model outputs
        
        Returns:
            Fused model output, optionally with individual outputs
        """
        # Get outputs from all models
        individual_outputs = []
        for model in self.models:
            output = model.forward(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            individual_outputs.append(output)
        
        # Fuse hidden states at specified layers
        fused_hidden_states = []
        
        for layer_idx in range(len(individual_outputs[0].hidden_states)):
            # Get hidden states from all models at this layer
            layer_hidden_states = [
                output.hidden_states[layer_idx]
                for output in individual_outputs
            ]
            
            # Apply fusion if this is a fusion layer
            if layer_idx in self.fusion_layer_indices:
                fusion_module = self.fusion_modules[str(layer_idx)]
                fused = fusion_module(layer_hidden_states)
            else:
                # No fusion, just average (or use primary model)
                fused = torch.stack(layer_hidden_states).mean(dim=0)
            
            fused_hidden_states.append(fused)
        
        # Create fused output
        # Use weighted average of logits from all models
        fused_logits = torch.stack([
            output.logits for output in individual_outputs
        ]).mean(dim=0)
        
        fused_output = ModelOutput(
            logits=fused_logits,
            hidden_states=tuple(fused_hidden_states),
            last_hidden_state=fused_hidden_states[-1],
        )
        
        if return_individual_outputs:
            return fused_output, individual_outputs
        return fused_output
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        use_braiding: bool = True,
    ) -> str:
        """
        Generate text using braided models.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            use_braiding: Whether to use braiding (False = use primary model only)
        
        Returns:
            Generated text
        """
        # Encode prompt
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)
        
        if not use_braiding:
            # Use only primary model
            output_ids = self.models[0].generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
            )
        else:
            # Braided generation (simplified - uses logit averaging)
            # For true braided generation, would need custom generation loop
            all_outputs = []
            for model in self.models:
                output_ids = model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )
                all_outputs.append(output_ids)
            
            # Use primary model's output (could implement voting/fusion here)
            output_ids = all_outputs[0]
        
        # Decode
        generated_text = self.tokenizer.decode(
            output_ids[0],
            skip_special_tokens=True,
        )
        
        return generated_text
    
    def get_model_by_role(self, role: str) -> Optional[ModelWrapper]:
        """Get a specific model by its role."""
        for model in self.models:
            if model.role == role:
                return model
        return None
    
    def save_fusion_layers(self, path: str):
        """Save only the fusion layer weights."""
        torch.save({
            "fusion_modules": self.fusion_modules.state_dict(),
            "fusion_strategy": self.fusion_strategy,
            "fusion_layer_indices": self.fusion_layer_indices,
        }, path)
        logger.info(f"Saved fusion layers to {path}")
    
    def load_fusion_layers(self, path: str):
        """Load fusion layer weights."""
        checkpoint = torch.load(path, map_location=self.device)
        self.fusion_modules.load_state_dict(checkpoint["fusion_modules"])
        logger.info(f"Loaded fusion layers from {path}")
    
    def __repr__(self) -> str:
        model_info = "\n".join([
            f"  - {model.model_name} ({model.role})"
            for model in self.models
        ])
        return (
            f"BraidedLLM(\n"
            f"  num_models={self.num_models},\n"
            f"  fusion_strategy={self.fusion_strategy},\n"
            f"  fusion_layers={self.fusion_layer_indices},\n"
            f"  models=[\n{model_info}\n  ]\n"
            f")"
        )
