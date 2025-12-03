"""
Neo4j schema initialization and management.
"""

from .neo4j_client import Neo4jClient
from loguru import logger


def init_schema(client: Neo4jClient):
    """
    Initialize Neo4j schema with constraints and indexes.
    
    Args:
        client: Neo4j client instance
    """
    logger.info("Initializing Neo4j schema")
    
    # Constraints
    constraints = [
        "CREATE CONSTRAINT conversation_id IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT message_id IF NOT EXISTS FOR (m:Message) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT document_url IF NOT EXISTS FOR (d:Document) REQUIRE d.url IS UNIQUE",
    ]
    
    for constraint in constraints:
        try:
            client.execute_write(constraint)
            logger.debug(f"Created constraint: {constraint}")
        except Exception as e:
            logger.warning(f"Constraint already exists or error: {e}")
    
    # Indexes
    indexes = [
        "CREATE INDEX message_timestamp IF NOT EXISTS FOR (m:Message) ON (m.timestamp)",
        "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
        "CREATE INDEX conversation_timestamp IF NOT EXISTS FOR (c:Conversation) ON (c.timestamp)",
    ]
    
    for index in indexes:
        try:
            client.execute_write(index)
            logger.debug(f"Created index: {index}")
        except Exception as e:
            logger.warning(f"Index already exists or error: {e}")
    
    # Vector indexes for embeddings
    vector_indexes = [
        {
            "name": "message_embeddings",
            "label": "Message",
            "property": "embedding",
            "dimensions": 384,  # sentence-transformers/all-MiniLM-L6-v2
            "similarity": "cosine",
        },
        {
            "name": "document_embeddings",
            "label": "Document",
            "property": "embedding",
            "dimensions": 384,
            "similarity": "cosine",
        },
    ]
    
    for vec_idx in vector_indexes:
        try:
            query = f"""
            CALL db.index.vector.createNodeIndex(
                '{vec_idx['name']}',
                '{vec_idx['label']}',
                '{vec_idx['property']}',
                {vec_idx['dimensions']},
                '{vec_idx['similarity']}'
            )
            """
            client.execute_write(query)
            logger.info(f"Created vector index: {vec_idx['name']}")
        except Exception as e:
            logger.warning(f"Vector index {vec_idx['name']} already exists or error: {e}")
    
    logger.info("Schema initialization complete")


def get_schema_info(client: Neo4jClient) -> dict:
    """
    Get information about the current schema.
    
    Args:
        client: Neo4j client instance
    
    Returns:
        Dictionary with schema information
    """
    # Get constraints
    constraints_query = "SHOW CONSTRAINTS"
    constraints = client.execute_query(constraints_query)
    
    # Get indexes
    indexes_query = "SHOW INDEXES"
    indexes = client.execute_query(indexes_query)
    
    # Get node labels
    labels_query = "CALL db.labels()"
    labels = client.execute_query(labels_query)
    
    # Get relationship types
    rel_types_query = "CALL db.relationshipTypes()"
    rel_types = client.execute_query(rel_types_query)
    
    return {
        "constraints": constraints,
        "indexes": indexes,
        "node_labels": [r["label"] for r in labels],
        "relationship_types": [r["relationshipType"] for r in rel_types],
    }
