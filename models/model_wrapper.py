"""
Wrapper for individual LLMs with full hidden layer access.
"""

import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class ModelOutput:
    """Output from model forward pass with hidden states."""
    logits: torch.Tensor
    hidden_states: Tuple[torch.Tensor, ...]  # All layer outputs
    attentions: Optional[Tuple[torch.Tensor, ...]] = None
    last_hidden_state: Optional[torch.Tensor] = None


class ModelWrapper(nn.Module):
    """
    Wrapper for a single LLM that provides access to all hidden layers.
    
    This wrapper enables:
    - Access to intermediate layer representations
    - Layer-wise interventions
    - Custom forward passes for braiding
    """
    
    def __init__(
        self,
        model_name: str,
        role: str = "general",
        quantization: Optional[str] = None,
        device: str = "cuda",
        device_map: str = "auto",
        trust_remote_code: bool = True,
    ):
        """
        Initialize model wrapper.
        
        Args:
            model_name: HuggingFace model identifier
            role: Specialization role (reasoning, search, code, etc.)
            quantization: Quantization method (4bit, 8bit, or None)
            device: Device to load model on
            device_map: Device mapping strategy
            trust_remote_code: Whether to trust remote code
        """
        super().__init__()
        
        self.model_name = model_name
        self.role = role
        self.device = device
        
        logger.info(f"Loading {model_name} with role: {role}")
        
        # Configure quantization
        quantization_config = None
        if quantization == "4bit":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        elif quantization == "8bit":
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
            )
        
        # Load model with hidden states enabled
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            output_hidden_states=True,
            output_attentions=True,
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=trust_remote_code,
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.num_layers = len(self.model.model.layers) if hasattr(self.model, 'model') else len(self.model.transformer.h)
        logger.info(f"Model loaded with {self.num_layers} layers")
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_layer_indices: Optional[List[int]] = None,
    ) -> ModelOutput:
        """
        Forward pass with access to hidden states.
        
        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            return_layer_indices: Specific layer indices to return (None = all)
        
        Returns:
            ModelOutput with logits and hidden states
        """
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
            output_attentions=True,
        )
        
        hidden_states = outputs.hidden_states
        
        # Filter to specific layers if requested
        if return_layer_indices is not None:
            hidden_states = tuple(
                hidden_states[i] for i in return_layer_indices
            )
        
        return ModelOutput(
            logits=outputs.logits,
            hidden_states=hidden_states,
            attentions=outputs.attentions,
            last_hidden_state=outputs.hidden_states[-1],
        )
    
    def get_layer_output(
        self,
        input_ids: torch.Tensor,
        layer_idx: int,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Get output from a specific layer.
        
        Args:
            input_ids: Input token IDs
            layer_idx: Layer index to extract
            attention_mask: Attention mask
        
        Returns:
            Hidden state from specified layer
        """
        output = self.forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_layer_indices=[layer_idx],
        )
        return output.hidden_states[0]
    
    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs,
    ) -> torch.Tensor:
        """
        Generate text using the model.
        
        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
        
        Returns:
            Generated token IDs
        """
        return self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
            **kwargs,
        )
    
    def encode(self, text: str) -> Dict[str, torch.Tensor]:
        """Encode text to token IDs."""
        return self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)
    
    def decode(self, token_ids: torch.Tensor) -> str:
        """Decode token IDs to text."""
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)
    
    @property
    def hidden_size(self) -> int:
        """Get hidden dimension size."""
        return self.model.config.hidden_size
    
    def __repr__(self) -> str:
        return f"ModelWrapper(model={self.model_name}, role={self.role}, layers={self.num_layers})"
