"""
Main coordinator for orchestrating braided LLM with tools and memory.
"""

from typing import List, Dict, Any, Optional
from loguru import logger
import json

from models import BraidedLLM
from memory import MemoryManager
from tools import ToolExecutor


class Coordinator:
    """
    Coordinates the braided LLM system with tools and memory.
    
    Handles:
    - Request routing
    - Tool selection and execution
    - Memory retrieval and storage
    - Response generation
    """
    
    def __init__(
        self,
        braided_model: BraidedLLM,
        memory_manager: MemoryManager,
        tool_executor: ToolExecutor,
        max_iterations: int = 5,
    ):
        """
        Initialize coordinator.
        
        Args:
            braided_model: Braided LLM instance
            memory_manager: Memory manager instance
            tool_executor: Tool executor instance
            max_iterations: Maximum tool-calling iterations
        """
        self.model = braided_model
        self.memory = memory_manager
        self.tools = tool_executor
        self.max_iterations = max_iterations
    
    def run(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        use_memory: bool = True,
        use_tools: bool = True,
    ) -> Dict[str, Any]:
        """
        Run a query through the system.
        
        Args:
            query: User query
            conversation_id: Optional conversation ID
            use_memory: Whether to use memory retrieval
            use_tools: Whether to use tools
        
        Returns:
            Response dictionary with answer and metadata
        """
        logger.info(f"Processing query: {query[:100]}...")
        
        # Create conversation if needed
        if conversation_id is None and use_memory:
            conversation_id = self.memory.create_conversation()
        
        # Store user message
        if use_memory and conversation_id:
            self.memory.add_message(
                conversation_id=conversation_id,
                role="user",
                content=query,
            )
        
        # Retrieve relevant context from memory
        context = []
        if use_memory:
            context = self._retrieve_context(query, conversation_id)
        
        # Build prompt with context
        prompt = self._build_prompt(query, context)
        
        # Agentic loop with tool calling
        iteration = 0
        final_response = None
        tool_calls_made = []
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Iteration {iteration}/{self.max_iterations}")
            
            # Generate response
            response = self.model.generate(
                prompt=prompt,
                max_new_tokens=512,
                temperature=0.7,
            )
            
            # Check if model wants to use a tool
            if use_tools:
                tool_call = self._parse_tool_call(response)
                
                if tool_call:
                    logger.info(f"Tool call detected: {tool_call['tool']}")
                    
                    # Execute tool
                    tool_result = self.tools.execute(
                        tool_name=tool_call["tool"],
                        arguments=tool_call["arguments"],
                    )
                    
                    tool_calls_made.append({
                        "tool": tool_call["tool"],
                        "arguments": tool_call["arguments"],
                        "result": tool_result,
                    })
                    
                    # Store tool result in memory if it's a document
                    if use_memory and tool_call["tool"] == "web_search":
                        self._store_search_results(tool_result)
                    
                    # Add tool result to prompt and continue
                    prompt = self._add_tool_result_to_prompt(
                        prompt, tool_call, tool_result
                    )
                    continue
            
            # No tool call, we have final response
            final_response = response
            break
        
        # Extract final answer
        answer = self._extract_answer(final_response)
        
        # Store assistant message
        if use_memory and conversation_id:
            self.memory.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
                metadata={"tool_calls": tool_calls_made},
            )
        
        return {
            "answer": answer,
            "conversation_id": conversation_id,
            "tool_calls": tool_calls_made,
            "iterations": iteration,
            "context_used": len(context) > 0,
        }
    
    def _retrieve_context(
        self,
        query: str,
        conversation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from memory."""
        context = []
        
        # Get conversation history
        if conversation_id:
            history = self.memory.get_conversation_history(
                conversation_id=conversation_id,
                limit=10,
            )
            context.extend(history)
        
        # Semantic search for relevant messages
        similar_messages = self.memory.semantic_search_messages(
            query=query,
            top_k=5,
        )
        context.extend([msg["node"] for msg in similar_messages])
        
        # Search documents
        similar_docs = self.memory.semantic_search_documents(
            query=query,
            top_k=3,
        )
        context.extend([doc["node"] for doc in similar_docs])
        
        logger.debug(f"Retrieved {len(context)} context items")
        return context
    
    def _build_prompt(
        self,
        query: str,
        context: List[Dict[str, Any]],
    ) -> str:
        """Build prompt with context."""
        prompt_parts = []
        
        # System message
        prompt_parts.append(
            "You are a helpful AI assistant with access to web search and memory. "
            "You can call tools by outputting JSON in the format: "
            '{"tool": "tool_name", "arguments": {...}}\n\n'
        )
        
        # Add context if available
        if context:
            prompt_parts.append("Relevant context:\n")
            for item in context[:5]:  # Limit context
                if "content" in item:
                    prompt_parts.append(f"- {item['content'][:200]}\n")
            prompt_parts.append("\n")
        
        # Add query
        prompt_parts.append(f"User query: {query}\n\n")
        prompt_parts.append("Response:")
        
        return "".join(prompt_parts)
    
    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from model response."""
        try:
            # Look for JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                
                if "tool" in data:
                    return data
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _add_tool_result_to_prompt(
        self,
        prompt: str,
        tool_call: Dict[str, Any],
        tool_result: Any,
    ) -> str:
        """Add tool result to prompt for next iteration."""
        result_str = json.dumps(tool_result, indent=2)
        
        addition = (
            f"\n\nTool call: {tool_call['tool']}\n"
            f"Arguments: {json.dumps(tool_call['arguments'])}\n"
            f"Result: {result_str}\n\n"
            f"Based on this information, provide your final answer:"
        )
        
        return prompt + addition
    
    def _extract_answer(self, response: str) -> str:
        """Extract final answer from response."""
        # Remove any JSON tool calls
        start = response.find("{")
        if start >= 0:
            response = response[:start]
        
        return response.strip()
    
    def _store_search_results(self, search_results: Dict[str, Any]):
        """Store search results in memory."""
        if "results" in search_results:
            for result in search_results["results"]:
                if "link" in result and "title" in result:
                    self.memory.store_document(
                        url=result["link"],
                        title=result["title"],
                        content=result.get("snippet", ""),
                        metadata={"source": "web_search"},
                    )
