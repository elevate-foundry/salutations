"""
Neo4j client for graph database operations.
"""

from neo4j import GraphDatabase, Driver
from typing import List, Dict, Any, Optional
from loguru import logger
import os


class Neo4jClient:
    """Client for interacting with Neo4j graph database."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI
            user: Username
            password: Password
            database: Database name
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = database
        
        logger.info(f"Connecting to Neo4j at {self.uri}")
        self.driver: Driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )
        
        # Verify connection
        self.driver.verify_connectivity()
        logger.info("Neo4j connection established")
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
        
        Returns:
            List of result records as dictionaries
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a write query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
        
        Returns:
            List of result records
        """
        with self.driver.session(database=self.database) as session:
            result = session.execute_write(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return [dict(record) for record in result]
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a node.
        
        Args:
            label: Node label
            properties: Node properties
        
        Returns:
            Created node
        """
        query = f"""
        CREATE (n:{label} $properties)
        RETURN n
        """
        result = self.execute_write(query, {"properties": properties})
        return result[0]["n"] if result else {}
    
    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a relationship between nodes.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
        
        Returns:
            Created relationship
        """
        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{rel_type} $properties]->(b)
        RETURN r
        """
        result = self.execute_write(query, {
            "from_id": from_id,
            "to_id": to_id,
            "properties": properties or {},
        })
        return result[0]["r"] if result else {}
    
    def find_nodes(
        self,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find nodes by label and properties.
        
        Args:
            label: Node label
            properties: Properties to match
            limit: Maximum results
        
        Returns:
            List of matching nodes
        """
        if properties:
            where_clause = " AND ".join([
                f"n.{key} = ${key}" for key in properties.keys()
            ])
            query = f"""
            MATCH (n:{label})
            WHERE {where_clause}
            RETURN n
            LIMIT $limit
            """
            params = {**properties, "limit": limit}
        else:
            query = f"""
            MATCH (n:{label})
            RETURN n
            LIMIT $limit
            """
            params = {"limit": limit}
        
        result = self.execute_query(query, params)
        return [record["n"] for record in result]
    
    def vector_search(
        self,
        index_name: str,
        embedding: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            index_name: Vector index name
            embedding: Query embedding vector
            top_k: Number of results
        
        Returns:
            List of similar nodes with scores
        """
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
        YIELD node, score
        RETURN node, score
        """
        result = self.execute_query(query, {
            "index_name": index_name,
            "top_k": top_k,
            "embedding": embedding,
        })
        return result
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
