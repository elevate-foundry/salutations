"""
Basic usage example of the braided LLM system.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import BraidedLLM
from memory import Neo4jClient, MemoryManager, init_schema
from tools import ToolExecutor
from orchestration import Coordinator
from loguru import logger


def main():
    """Run a basic example."""
    
    logger.info("Starting Salutations - Multi-LLM Braiding System")
    
    # Configuration
    model_configs = [
        {
            "model_name": "meta-llama/Llama-3.1-8B",
            "role": "reasoning",
            "quantization": "8bit",
        },
        {
            "model_name": "mistralai/Mistral-7B-v0.1",
            "role": "search",
            "quantization": "8bit",
        },
        {
            "model_name": "microsoft/Phi-3-mini-4k-instruct",
            "role": "code",
            "quantization": "8bit",
        },
    ]
    
    # Initialize components
    logger.info("Initializing braided model...")
    braided_model = BraidedLLM(
        model_configs=model_configs,
        fusion_strategy="learned_weighted",
        device="cuda",
    )
    
    logger.info("Connecting to Neo4j...")
    neo4j_client = Neo4jClient()
    
    # Initialize schema
    logger.info("Initializing database schema...")
    init_schema(neo4j_client)
    
    logger.info("Initializing memory manager...")
    memory_manager = MemoryManager(neo4j_client)
    
    logger.info("Initializing tool executor...")
    tool_executor = ToolExecutor()
    
    logger.info("Creating coordinator...")
    coordinator = Coordinator(
        braided_model=braided_model,
        memory_manager=memory_manager,
        tool_executor=tool_executor,
    )
    
    # Example queries
    queries = [
        "What are the latest developments in transformer architectures?",
        "Search for information about multi-modal language models and summarize the key findings.",
        "Write a Python function to implement attention mechanism.",
    ]
    
    for i, query in enumerate(queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Query {i}: {query}")
        logger.info(f"{'='*60}\n")
        
        result = coordinator.run(
            query=query,
            use_memory=True,
            use_tools=True,
        )
        
        print(f"\nAnswer: {result['answer']}\n")
        print(f"Tool calls made: {len(result['tool_calls'])}")
        print(f"Iterations: {result['iterations']}")
        print(f"Context used: {result['context_used']}")
        
        if result['tool_calls']:
            print("\nTool calls:")
            for tc in result['tool_calls']:
                print(f"  - {tc['tool']}: {tc['arguments']}")
    
    # Cleanup
    neo4j_client.close()
    logger.info("Example complete!")


if __name__ == "__main__":
    main()
