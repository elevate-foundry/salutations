"""
Memory manager for storing and retrieving conversation and knowledge graph data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from loguru import logger
from sentence_transformers import SentenceTransformer

from .neo4j_client import Neo4jClient


class MemoryManager:
    """
    Manages memory storage and retrieval using Neo4j graph database.
    
    Handles:
    - Conversation history
    - Entity extraction and relationships
    - Document storage
    - Vector similarity search
    """
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Initialize memory manager.
        
        Args:
            neo4j_client: Neo4j client instance
            embedding_model: Model for generating embeddings
        """
        self.client = neo4j_client
        
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Optional conversation ID
            metadata: Optional metadata
        
        Returns:
            Conversation ID
        """
        conv_id = conversation_id or str(uuid.uuid4())
        
        query = """
        CREATE (c:Conversation {
            id: $id,
            timestamp: datetime($timestamp),
            metadata: $metadata
        })
        RETURN c.id as id
        """
        
        result = self.client.execute_write(query, {
            "id": conv_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })
        
        logger.info(f"Created conversation: {conv_id}")
        return result[0]["id"]
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        
        # Generate embedding
        embedding = self.embedder.encode(content).tolist()
        
        query = """
        MATCH (c:Conversation {id: $conversation_id})
        CREATE (m:Message {
            id: $message_id,
            role: $role,
            content: $content,
            timestamp: datetime($timestamp),
            embedding: $embedding,
            metadata: $metadata
        })
        CREATE (m)-[:PART_OF]->(c)
        RETURN m.id as id
        """
        
        result = self.client.execute_write(query, {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "embedding": embedding,
            "metadata": metadata or {},
        })
        
        logger.debug(f"Added message {message_id} to conversation {conversation_id}")
        return result[0]["id"]
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum messages to retrieve
        
        Returns:
            List of messages
        """
        query = """
        MATCH (m:Message)-[:PART_OF]->(c:Conversation {id: $conversation_id})
        RETURN m
        ORDER BY m.timestamp ASC
        LIMIT $limit
        """
        
        result = self.client.execute_query(query, {
            "conversation_id": conversation_id,
            "limit": limit,
        })
        
        return [dict(record["m"]) for record in result]
    
    def create_entity(
        self,
        name: str,
        entity_type: str,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create or update an entity.
        
        Args:
            name: Entity name
            entity_type: Entity type (person, organization, concept, etc.)
            description: Entity description
            properties: Additional properties
        
        Returns:
            Entity name
        """
        query = """
        MERGE (e:Entity {name: $name})
        ON CREATE SET
            e.type = $type,
            e.description = $description,
            e.created_at = datetime($timestamp),
            e.properties = $properties
        ON MATCH SET
            e.description = CASE WHEN $description IS NOT NULL THEN $description ELSE e.description END,
            e.updated_at = datetime($timestamp)
        RETURN e.name as name
        """
        
        result = self.client.execute_write(query, {
            "name": name,
            "type": entity_type,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "properties": properties or {},
        })
        
        logger.debug(f"Created/updated entity: {name}")
        return result[0]["name"]
    
    def create_entity_relationship(
        self,
        from_entity: str,
        to_entity: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a relationship between entities.
        
        Args:
            from_entity: Source entity name
            to_entity: Target entity name
            relationship_type: Relationship type
            properties: Relationship properties
        """
        # Sanitize relationship type for Cypher
        rel_type = relationship_type.upper().replace(" ", "_")
        
        query = f"""
        MATCH (a:Entity {{name: $from_entity}})
        MATCH (b:Entity {{name: $to_entity}})
        MERGE (a)-[r:{rel_type}]->(b)
        ON CREATE SET r.created_at = datetime($timestamp), r.properties = $properties
        RETURN r
        """
        
        self.client.execute_write(query, {
            "from_entity": from_entity,
            "to_entity": to_entity,
            "timestamp": datetime.now().isoformat(),
            "properties": properties or {},
        })
        
        logger.debug(f"Created relationship: {from_entity} -{relationship_type}-> {to_entity}")
    
    def link_message_to_entity(self, message_id: str, entity_name: str):
        """Link a message to an entity it mentions."""
        query = """
        MATCH (m:Message {id: $message_id})
        MATCH (e:Entity {name: $entity_name})
        MERGE (m)-[:MENTIONS]->(e)
        """
        
        self.client.execute_write(query, {
            "message_id": message_id,
            "entity_name": entity_name,
        })
    
    def store_document(
        self,
        url: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a document with embedding.
        
        Args:
            url: Document URL
            title: Document title
            content: Document content
            metadata: Optional metadata
        
        Returns:
            Document URL
        """
        # Generate embedding
        embedding = self.embedder.encode(content).tolist()
        
        query = """
        MERGE (d:Document {url: $url})
        ON CREATE SET
            d.title = $title,
            d.content = $content,
            d.embedding = $embedding,
            d.created_at = datetime($timestamp),
            d.metadata = $metadata
        ON MATCH SET
            d.title = $title,
            d.content = $content,
            d.embedding = $embedding,
            d.updated_at = datetime($timestamp)
        RETURN d.url as url
        """
        
        result = self.client.execute_write(query, {
            "url": url,
            "title": title,
            "content": content[:10000],  # Limit content size
            "embedding": embedding,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })
        
        logger.info(f"Stored document: {url}")
        return result[0]["url"]
    
    def semantic_search_messages(
        self,
        query: str,
        top_k: int = 10,
        conversation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search messages by semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results
            conversation_id: Optional conversation filter
        
        Returns:
            List of similar messages with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Use vector index
        result = self.client.vector_search(
            index_name="message_embeddings",
            embedding=query_embedding,
            top_k=top_k,
        )
        
        # Filter by conversation if specified
        if conversation_id:
            result = [
                r for r in result
                if r["node"].get("conversation_id") == conversation_id
            ]
        
        return result
    
    def semantic_search_documents(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search documents by semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of similar documents with scores
        """
        query_embedding = self.embedder.encode(query).tolist()
        
        result = self.client.vector_search(
            index_name="document_embeddings",
            embedding=query_embedding,
            top_k=top_k,
        )
        
        return result
    
    def get_entity_context(
        self,
        entity_name: str,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Get entity with its relationships.
        
        Args:
            entity_name: Entity name
            max_depth: Maximum relationship depth
        
        Returns:
            Entity context with relationships
        """
        query = f"""
        MATCH path = (e:Entity {{name: $entity_name}})-[*1..{max_depth}]-(related)
        RETURN e, collect(distinct related) as related_entities, collect(distinct relationships(path)) as relationships
        """
        
        result = self.client.execute_query(query, {"entity_name": entity_name})
        
        if result:
            return {
                "entity": dict(result[0]["e"]),
                "related_entities": [dict(e) for e in result[0]["related_entities"]],
                "relationships": result[0]["relationships"],
            }
        return {}
