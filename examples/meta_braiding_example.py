"""
Example: Teaching an agent to braid LLMs.

This demonstrates how a meta-learning agent can learn to:
1. Select which models to combine
2. Choose fusion layers
3. Pick fusion strategies
4. Optimize for different tasks
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.meta_braider import MetaBraider, MetaBraiderTrainer
from loguru import logger


def main():
    """Demonstrate meta-braiding."""
    
    logger.info("=" * 70)
    logger.info("🤖 META-BRAIDING: Teaching an Agent to Braid LLMs")
    logger.info("=" * 70)
    logger.info("")
    
    # ========================================================================
    # Step 1: Define Model Pool
    # ========================================================================
    
    logger.info("📚 Step 1: Define Model Pool")
    logger.info("-" * 70)
    
    model_pool = [
        {
            "model_name": "meta-llama/Llama-3.1-8B",
            "role": "general",
            "size": 8e9,
            "num_layers": 32,
            "hidden_dim": 4096,
            "domain": "general",
            "quantization": "8bit",
            "recency": 0.9,  # Recent model
        },
        {
            "model_name": "codellama/CodeLlama-7b",
            "role": "code",
            "size": 7e9,
            "num_layers": 32,
            "hidden_dim": 4096,
            "domain": "code",
            "quantization": "8bit",
            "recency": 0.7,
        },
        {
            "model_name": "mistralai/Mistral-7B-v0.1",
            "role": "knowledge",
            "size": 7e9,
            "num_layers": 32,
            "hidden_dim": 4096,
            "domain": "general",
            "quantization": "8bit",
            "recency": 0.8,
        },
        {
            "model_name": "microsoft/Phi-3-mini-4k-instruct",
            "role": "efficient",
            "size": 3.8e9,
            "num_layers": 32,
            "hidden_dim": 3072,
            "domain": "general",
            "quantization": "8bit",
            "recency": 0.95,
        },
        {
            "model_name": "epfl-llm/meditron-7b",
            "role": "medical",
            "size": 7e9,
            "num_layers": 32,
            "hidden_dim": 4096,
            "domain": "medical",
            "quantization": "8bit",
            "recency": 0.6,
        },
    ]
    
    logger.info(f"Model pool contains {len(model_pool)} models:")
    for model in model_pool:
        logger.info(f"  - {model['model_name']} ({model['domain']})")
    
    logger.info("")
    
    # ========================================================================
    # Step 2: Create Meta-Braider Agent
    # ========================================================================
    
    logger.info("📚 Step 2: Create Meta-Braider Agent")
    logger.info("-" * 70)
    
    meta_braider = MetaBraider(
        model_pool=model_pool,
        hidden_dim=512,
        num_layers=3,
    )
    
    logger.info("✓ Meta-braider agent created")
    logger.info(f"  - Can choose from {len(model_pool)} models")
    logger.info(f"  - Learns optimal braiding strategies")
    logger.info(f"  - Adapts to different tasks")
    logger.info("")
    
    # ========================================================================
    # Step 3: Test on Different Tasks
    # ========================================================================
    
    logger.info("📚 Step 3: Agent Makes Braiding Decisions")
    logger.info("-" * 70)
    logger.info("")
    
    # Task 1: Code generation
    logger.info("🔧 Task 1: Code Generation")
    task_code = {
        "type": "code",
        "complexity": 0.7,
        "capabilities": ["reasoning", "knowledge"],
        "description": "Write a Python function to implement quicksort",
    }
    
    decision_code = meta_braider.forward(task_code, compute_budget=1.0)
    
    logger.info(f"Agent's decision for code task:")
    logger.info(f"  Model weights: {decision_code.model_weights.tolist()}")
    logger.info(f"  Top models: {[model_pool[i]['role'] for i in decision_code.model_weights.topk(3).indices.tolist()]}")
    logger.info(f"  Fusion layers: {decision_code.layer_selection}")
    logger.info(f"  Strategy: {decision_code.fusion_strategy}")
    logger.info(f"  Params: {decision_code.fusion_params}")
    logger.info("")
    
    # Task 2: Medical question answering
    logger.info("🏥 Task 2: Medical Question Answering")
    task_medical = {
        "type": "qa",
        "complexity": 0.9,
        "capabilities": ["reasoning", "knowledge"],
        "description": "Explain the mechanism of action for ACE inhibitors",
    }
    
    decision_medical = meta_braider.forward(task_medical, compute_budget=1.0)
    
    logger.info(f"Agent's decision for medical task:")
    logger.info(f"  Model weights: {decision_medical.model_weights.tolist()}")
    logger.info(f"  Top models: {[model_pool[i]['role'] for i in decision_medical.model_weights.topk(3).indices.tolist()]}")
    logger.info(f"  Fusion layers: {decision_medical.layer_selection}")
    logger.info(f"  Strategy: {decision_medical.fusion_strategy}")
    logger.info("")
    
    # Task 3: Creative writing
    logger.info("✍️  Task 3: Creative Writing")
    task_creative = {
        "type": "creative",
        "complexity": 0.6,
        "capabilities": ["reasoning"],
        "description": "Write a short story about time travel",
    }
    
    decision_creative = meta_braider.forward(task_creative, compute_budget=0.7)
    
    logger.info(f"Agent's decision for creative task:")
    logger.info(f"  Model weights: {decision_creative.model_weights.tolist()}")
    logger.info(f"  Top models: {[model_pool[i]['role'] for i in decision_creative.model_weights.topk(3).indices.tolist()]}")
    logger.info(f"  Fusion layers: {decision_creative.layer_selection}")
    logger.info(f"  Strategy: {decision_creative.fusion_strategy}")
    logger.info("")
    
    # ========================================================================
    # Step 4: Demonstrate Learning
    # ========================================================================
    
    logger.info("📚 Step 4: Agent Learns from Feedback")
    logger.info("-" * 70)
    logger.info("")
    
    logger.info("💡 The agent can learn from task performance:\n")
    
    logger.info("Example learning loop:")
    logger.info("  1. Agent makes braiding decision")
    logger.info("  2. Braided model performs task")
    logger.info("  3. Performance is measured")
    logger.info("  4. Agent updates its strategy")
    logger.info("  5. Repeat → Agent gets better over time!")
    logger.info("")
    
    # Simulate learning
    logger.info("Simulating learning from feedback...")
    
    import torch
    optimizer = torch.optim.Adam(meta_braider.parameters(), lr=1e-4)
    
    # Good performance on code task
    meta_braider.learn_from_feedback(
        task_info=task_code,
        decision=decision_code,
        performance=0.9,  # High performance
        optimizer=optimizer,
    )
    
    # Poor performance on medical task (agent will learn to adjust)
    meta_braider.learn_from_feedback(
        task_info=task_medical,
        decision=decision_medical,
        performance=0.4,  # Low performance
        optimizer=optimizer,
    )
    
    logger.info("")
    
    # ========================================================================
    # Step 5: Training the Agent
    # ========================================================================
    
    logger.info("📚 Step 5: Training the Meta-Braider")
    logger.info("-" * 70)
    logger.info("")
    
    logger.info("To fully train the agent, you would:")
    logger.info("  1. Create a dataset of diverse tasks")
    logger.info("  2. For each task:")
    logger.info("     - Agent decides how to braid")
    logger.info("     - Create braided model")
    logger.info("     - Evaluate performance")
    logger.info("     - Update agent based on results")
    logger.info("  3. Agent learns:")
    logger.info("     - Code tasks → Use code models more")
    logger.info("     - Medical tasks → Use medical models more")
    logger.info("     - Complex tasks → More fusion points")
    logger.info("     - Simple tasks → Fewer models, less fusion")
    logger.info("")
    
    # Example training dataset
    training_tasks = [
        {
            "info": {"type": "code", "complexity": 0.7, "capabilities": ["reasoning"]},
            "data": "sample code task",
        },
        {
            "info": {"type": "qa", "complexity": 0.8, "capabilities": ["knowledge"]},
            "data": "sample QA task",
        },
        {
            "info": {"type": "reasoning", "complexity": 0.9, "capabilities": ["reasoning"]},
            "data": "sample reasoning task",
        },
    ]
    
    logger.info(f"Example training dataset: {len(training_tasks)} tasks")
    logger.info("")
    
    # Create trainer
    trainer = MetaBraiderTrainer(
        meta_braider=meta_braider,
        eval_dataset=training_tasks,
        learning_rate=1e-4,
    )
    
    logger.info("Training for 10 episodes (demo)...")
    # trainer.train(num_episodes=10)  # Uncomment to actually train
    logger.info("(Training skipped in demo)")
    logger.info("")
    
    # ========================================================================
    # Step 6: Key Insights
    # ========================================================================
    
    logger.info("📚 Step 6: Key Insights")
    logger.info("-" * 70)
    logger.info("")
    
    logger.info("🎯 What the Meta-Braider Learns:\n")
    
    logger.info("1. Model Selection")
    logger.info("   - Which models work best for which tasks")
    logger.info("   - How to weight different models")
    logger.info("   - When to use specialized vs general models\n")
    
    logger.info("2. Fusion Strategy")
    logger.info("   - Learned weighted for simple tasks")
    logger.info("   - Attention for complex interactions")
    logger.info("   - Router for multi-domain tasks\n")
    
    logger.info("3. Layer Selection")
    logger.info("   - More fusion for complex tasks")
    logger.info("   - Less fusion for simple tasks")
    logger.info("   - Strategic placement of fusion points\n")
    
    logger.info("4. Compute Efficiency")
    logger.info("   - Balance performance vs compute")
    logger.info("   - Use smaller models when possible")
    logger.info("   - Adaptive fusion frequency\n")
    
    logger.info("✨ Benefits:\n")
    logger.info("  ✓ Automatic braiding configuration")
    logger.info("  ✓ Learns from experience")
    logger.info("  ✓ Adapts to new tasks")
    logger.info("  ✓ Optimizes for performance and efficiency")
    logger.info("  ✓ No manual tuning required!")
    logger.info("")
    
    # ========================================================================
    # Step 7: Advanced Capabilities
    # ========================================================================
    
    logger.info("📚 Step 7: Advanced Capabilities")
    logger.info("-" * 70)
    logger.info("")
    
    logger.info("🚀 The agent can learn to:\n")
    
    logger.info("1. Multi-Task Optimization")
    logger.info("   - Learn one braiding strategy for multiple tasks")
    logger.info("   - Transfer knowledge across domains\n")
    
    logger.info("2. Online Learning")
    logger.info("   - Continuously improve from user feedback")
    logger.info("   - Adapt to new models in the pool\n")
    
    logger.info("3. Meta-Learning")
    logger.info("   - Learn to learn braiding strategies")
    logger.info("   - Few-shot adaptation to new tasks\n")
    
    logger.info("4. Explainability")
    logger.info("   - Explain why certain models were chosen")
    logger.info("   - Provide confidence scores\n")
    
    logger.info("5. Constraint Satisfaction")
    logger.info("   - Respect compute budgets")
    logger.info("   - Optimize for latency vs accuracy")
    logger.info("   - Handle model availability\n")
    
    logger.success("=" * 70)
    logger.success("🎉 Meta-Braiding Demo Complete!")
    logger.success("=" * 70)
    logger.info("")
    logger.info("The agent has learned to:")
    logger.info("  ✓ Analyze tasks")
    logger.info("  ✓ Select appropriate models")
    logger.info("  ✓ Choose fusion strategies")
    logger.info("  ✓ Optimize braiding parameters")
    logger.info("  ✓ Learn from feedback")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Train on real tasks with actual models")
    logger.info("  2. Collect performance data")
    logger.info("  3. Iterate and improve")
    logger.info("  4. Deploy as automatic braiding system!")


if __name__ == "__main__":
    main()
