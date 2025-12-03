"""
BIFM-64 Neo4j Graph Integration

Stores fitness topologies as nodes in Neo4j knowledge graph.
Enables pattern recognition, swarm learning, and cross-repo intelligence.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from neo4j import GraphDatabase
import json


class BIFMGraph:
    """Neo4j graph for BIFM-64 fitness topologies"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._create_constraints()
    
    def close(self):
        self.driver.close()
    
    def _create_constraints(self):
        """Create indexes and constraints"""
        with self.driver.session() as session:
            # Unique constraint on fitness braille
            session.run("""
                CREATE CONSTRAINT fitness_braille IF NOT EXISTS
                FOR (f:FitnessTopology) REQUIRE f.braille IS UNIQUE
            """)
            
            # Index on commit SCL
            session.run("""
                CREATE INDEX commit_scl IF NOT EXISTS
                FOR (c:Commit) ON (c.scl)
            """)
            
            # Index on repo name
            session.run("""
                CREATE INDEX repo_name IF NOT EXISTS
                FOR (r:Repo) ON (r.name)
            """)
    
    def store_commit(
        self,
        scl: str,
        braille: str,
        kappa: int,
        sigma: int,
        delta: int,
        repo: str,
        message: str,
        author: str = "autonomous-agent",
    ) -> Dict:
        """Store commit with fitness topology in graph"""
        
        interpretation = self._interpret_fitness(kappa, sigma, delta)
        timestamp = datetime.utcnow().isoformat()
        
        with self.driver.session() as session:
            result = session.run("""
                // Create or merge fitness topology
                MERGE (f:FitnessTopology {braille: $braille})
                ON CREATE SET
                    f.kappa = $kappa,
                    f.sigma = $sigma,
                    f.delta = $delta,
                    f.interpretation = $interpretation,
                    f.created = $timestamp
                
                // Create commit
                CREATE (c:Commit {
                    scl: $scl,
                    message: $message,
                    timestamp: $timestamp,
                    repo: $repo,
                    author: $author
                })
                
                // Link commit to fitness
                CREATE (c)-[:HAS_FITNESS]->(f)
                
                // Link to repo
                MERGE (r:Repo {name: $repo})
                ON CREATE SET r.created = $timestamp
                CREATE (r)-[:CONTAINS]->(c)
                
                // Link to previous commit
                OPTIONAL MATCH (prev:Commit {repo: $repo})
                WHERE prev.timestamp < $timestamp
                WITH c, f, r, prev
                ORDER BY prev.timestamp DESC
                LIMIT 1
                FOREACH (p IN CASE WHEN prev IS NOT NULL THEN [prev] ELSE [] END |
                    CREATE (c)-[:FOLLOWS]->(p)
                )
                
                RETURN c, f, r
            """, {
                "braille": braille,
                "kappa": kappa,
                "sigma": sigma,
                "delta": delta,
                "interpretation": interpretation,
                "scl": scl,
                "message": message,
                "timestamp": timestamp,
                "repo": repo,
                "author": author,
            })
            
            record = result.single()
            return {
                "commit": dict(record["c"]),
                "fitness": dict(record["f"]),
                "repo": dict(record["r"]),
            }
    
    def find_similar_fitness(
        self,
        kappa: int,
        sigma: int,
        delta: int,
        threshold: int = 1,
        limit: int = 20,
    ) -> List[Dict]:
        """Find commits with similar fitness topology"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Commit)-[:HAS_FITNESS]->(f:FitnessTopology)
                WHERE abs(f.kappa - $kappa) <= $threshold
                  AND abs(f.sigma - $sigma) <= $threshold
                  AND f.delta = $delta
                RETURN c.scl as scl,
                       c.message as message,
                       c.timestamp as timestamp,
                       c.repo as repo,
                       f.braille as braille,
                       f.kappa as kappa,
                       f.sigma as sigma,
                       f.delta as delta
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, {
                "kappa": kappa,
                "sigma": sigma,
                "delta": delta,
                "threshold": threshold,
                "limit": limit,
            })
            
            return [dict(record) for record in result]
    
    def learn_optimal_patterns(self, repo: str) -> Optional[Tuple[float, float, float]]:
        """Learn optimal fitness patterns from successful commits"""
        
        with self.driver.session() as session:
            result = session.run("""
                // Find commits followed by successful commits
                MATCH (c1:Commit)-[:FOLLOWS]->(c2:Commit)
                MATCH (c1)-[:HAS_FITNESS]->(f1:FitnessTopology)
                MATCH (c2)-[:HAS_FITNESS]->(f2:FitnessTopology)
                WHERE c1.repo = $repo
                  AND f2.delta <= 1  // Successful commits
                RETURN 
                    avg(f1.kappa) as optimal_kappa,
                    avg(f1.sigma) as optimal_sigma,
                    avg(toFloat(f1.delta)) as optimal_delta
            """, {"repo": repo})
            
            record = result.single()
            if record:
                return (
                    record["optimal_kappa"],
                    record["optimal_sigma"],
                    record["optimal_delta"],
                )
            return None
    
    def get_fitness_evolution(self, repo: str, limit: int = 50) -> List[Dict]:
        """Get fitness evolution timeline for a repo"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:Repo {name: $repo})-[:CONTAINS]->(c:Commit)
                MATCH (c)-[:HAS_FITNESS]->(f:FitnessTopology)
                RETURN c.timestamp as timestamp,
                       c.scl as scl,
                       f.kappa as kappa,
                       f.sigma as sigma,
                       f.delta as delta,
                       f.braille as braille
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, {"repo": repo, "limit": limit})
            
            return [dict(record) for record in result]
    
    def find_similar_repos(self, repo: str, min_shared: int = 10) -> List[Dict]:
        """Find repos with similar fitness patterns"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r1:Repo {name: $repo})-[:CONTAINS]->(c1:Commit)
                MATCH (c1)-[:HAS_FITNESS]->(f:FitnessTopology)
                MATCH (r2:Repo)-[:CONTAINS]->(c2:Commit)-[:HAS_FITNESS]->(f)
                WHERE r1 <> r2
                WITH r2.name as repo_name, count(DISTINCT f) as shared_fitness
                WHERE shared_fitness >= $min_shared
                RETURN repo_name, shared_fitness
                ORDER BY shared_fitness DESC
            """, {"repo": repo, "min_shared": min_shared})
            
            return [dict(record) for record in result]
    
    def get_repo_health(self, repo: str) -> Dict:
        """Get overall health metrics for a repo"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:Repo {name: $repo})-[:CONTAINS]->(c:Commit)
                MATCH (c)-[:HAS_FITNESS]->(f:FitnessTopology)
                WITH c, f
                ORDER BY c.timestamp DESC
                LIMIT 20
                RETURN 
                    avg(f.kappa) as avg_kappa,
                    avg(f.sigma) as avg_sigma,
                    avg(toFloat(f.delta)) as avg_delta,
                    count(CASE WHEN f.delta = 3 THEN 1 END) as critical_count,
                    count(CASE WHEN f.delta <= 1 THEN 1 END) as stable_count
            """, {"repo": repo})
            
            record = result.single()
            if record:
                return dict(record)
            return {}
    
    def create_fitness_similarity_links(self, threshold: int = 1):
        """Create SIMILAR_TO relationships between fitness topologies"""
        
        with self.driver.session() as session:
            session.run("""
                MATCH (f1:FitnessTopology), (f2:FitnessTopology)
                WHERE f1 <> f2
                  AND abs(f1.kappa - f2.kappa) <= $threshold
                  AND abs(f1.sigma - f2.sigma) <= $threshold
                  AND f1.delta = f2.delta
                MERGE (f1)-[s:SIMILAR_TO]-(f2)
                SET s.distance = abs(f1.kappa - f2.kappa) + abs(f1.sigma - f2.sigma)
            """, {"threshold": threshold})
    
    def get_swarm_intelligence(self, limit: int = 100) -> Dict:
        """Get collective intelligence from all agents"""
        
        with self.driver.session() as session:
            result = session.run("""
                // Most common successful patterns
                MATCH (c:Commit)-[:HAS_FITNESS]->(f:FitnessTopology)
                WHERE f.delta <= 1
                WITH f.braille as pattern, count(*) as frequency
                ORDER BY frequency DESC
                LIMIT $limit
                RETURN collect({pattern: pattern, frequency: frequency}) as patterns
            """, {"limit": limit})
            
            record = result.single()
            return dict(record) if record else {}
    
    @staticmethod
    def _interpret_fitness(kappa: int, sigma: int, delta: int) -> str:
        """Generate human-readable interpretation"""
        
        curvature = {
            0: "minimal deformation",
            1: "slight change",
            2: "slight change",
            3: "moderate change",
            4: "moderate change",
            5: "significant change",
            6: "significant change",
            7: "maximum deformation",
        }.get(kappa, "unknown")
        
        stability = {
            0: "rock solid",
            1: "stable",
            2: "stable",
            3: "moderate volatility",
            4: "moderate volatility",
            5: "high volatility",
            6: "high volatility",
            7: "extremely volatile",
        }.get(sigma, "unknown")
        
        direction = {
            0: "neutral/stable",
            1: "positive drift",
            2: "negative drift",
            3: "divergent/critical",
        }.get(delta, "unknown")
        
        return f"{curvature}, {stability}, {direction}"


# Example usage
if __name__ == "__main__":
    # Initialize graph
    graph = BIFMGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Store a commit
    result = graph.store_commit(
        scl="⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯",
        braille="⣯",
        kappa=7,
        sigma=5,
        delta=3,
        repo="salutations",
        message="fix: authentication edge case"
    )
    
    print(f"Stored commit: {result['commit']['scl']}")
    print(f"Fitness: {result['fitness']['braille']}")
    
    # Find similar commits
    similar = graph.find_similar_fitness(kappa=7, sigma=5, delta=3)
    print(f"\nFound {len(similar)} similar commits")
    
    # Get repo health
    health = graph.get_repo_health("salutations")
    print(f"\nRepo health: {health}")
    
    # Close connection
    graph.close()
