"""
Training script for fusion layers.

This script trains the fusion layers to optimize how multiple models
are combined, while keeping the base models frozen.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup
import sys
from pathlib import Path
from tqdm import tqdm
from loguru import logger
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import BraidedLLM


class TextDataset(Dataset):
    """Simple text dataset for training."""
    
    def __init__(self, texts, tokenizer, max_length=512):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
        }


def train_fusion_layers(
    braided_model: BraidedLLM,
    train_texts: list,
    config: dict,
):
    """
    Train fusion layers while keeping base models frozen.
    
    Args:
        braided_model: BraidedLLM instance
        train_texts: List of training texts
        config: Training configuration
    """
    device = braided_model.device
    
    # Freeze base models
    logger.info("Freezing base model parameters...")
    for model in braided_model.models:
        for param in model.parameters():
            param.requires_grad = False
    
    # Only train fusion layers
    logger.info("Enabling fusion layer training...")
    for param in braided_model.fusion_modules.parameters():
        param.requires_grad = True
    
    # Count trainable parameters
    trainable_params = sum(
        p.numel() for p in braided_model.parameters() if p.requires_grad
    )
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    # Create dataset and dataloader
    dataset = TextDataset(
        texts=train_texts,
        tokenizer=braided_model.tokenizer,
        max_length=config.get("max_length", 512),
    )
    
    dataloader = DataLoader(
        dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=True,
        num_workers=config.get("num_workers", 2),
    )
    
    # Optimizer and scheduler
    optimizer = AdamW(
        braided_model.fusion_modules.parameters(),
        lr=config.get("learning_rate", 5e-5),
        weight_decay=config.get("weight_decay", 0.01),
    )
    
    num_epochs = config.get("num_epochs", 3)
    num_training_steps = len(dataloader) * num_epochs
    num_warmup_steps = int(0.1 * num_training_steps)
    
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps,
    )
    
    # Training loop
    logger.info(f"Starting training for {num_epochs} epochs...")
    braided_model.train()
    
    for epoch in range(num_epochs):
        logger.info(f"\nEpoch {epoch + 1}/{num_epochs}")
        
        total_loss = 0
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch + 1}")
        
        for batch_idx, batch in enumerate(progress_bar):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            
            # Forward pass
            outputs = braided_model.forward(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            
            # Language modeling loss (predict next token)
            shift_logits = outputs.logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()
            
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
            )
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(
                braided_model.fusion_modules.parameters(),
                max_norm=config.get("max_grad_norm", 1.0),
            )
            
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            
            total_loss += loss.item()
            
            # Update progress bar
            progress_bar.set_postfix({
                "loss": f"{loss.item():.4f}",
                "avg_loss": f"{total_loss / (batch_idx + 1):.4f}",
            })
            
            # Save checkpoint periodically
            if (batch_idx + 1) % config.get("save_steps", 500) == 0:
                checkpoint_path = f"checkpoints/fusion_epoch{epoch}_step{batch_idx}.pt"
                braided_model.save_fusion_layers(checkpoint_path)
                logger.info(f"Saved checkpoint: {checkpoint_path}")
        
        avg_loss = total_loss / len(dataloader)
        logger.info(f"Epoch {epoch + 1} average loss: {avg_loss:.4f}")
        
        # Save epoch checkpoint
        epoch_path = f"checkpoints/fusion_epoch{epoch + 1}.pt"
        braided_model.save_fusion_layers(epoch_path)
        logger.info(f"Saved epoch checkpoint: {epoch_path}")
    
    # Save final model
    final_path = "checkpoints/fusion_final.pt"
    braided_model.save_fusion_layers(final_path)
    logger.success(f"Training complete! Final model saved to {final_path}")


def main():
    """Main training function."""
    
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "fusion_config.yaml"
    
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        # Default config
        config = {
            "batch_size": 4,
            "learning_rate": 5e-5,
            "num_epochs": 3,
            "max_length": 512,
            "weight_decay": 0.01,
            "max_grad_norm": 1.0,
            "save_steps": 500,
        }
    
    logger.info(f"Training config: {config}")
    
    # Initialize braided model
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
    
    logger.info("Initializing braided model...")
    braided_model = BraidedLLM(
        model_configs=model_configs,
        fusion_strategy="learned_weighted",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    
    # Sample training data (replace with your actual data)
    train_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language for data science.",
        # Add more training examples...
    ]
    
    logger.warning("Using sample training data. Replace with actual dataset!")
    
    # Train
    train_fusion_layers(braided_model, train_texts, config)


if __name__ == "__main__":
    main()
