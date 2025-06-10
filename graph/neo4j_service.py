import logging
import os
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
import hashlib
import time
import uuid
import config

logger = logging.getLogger(__name__)

class Neo4jService:
    """Service for graph database operations"""
    
    def __init__(self):
        """Initialize Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
            )
            self._create_constraints()
            logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
    
    def _create_constraints(self):
        """Create database constraints and indexes"""
        try:
            with self.driver.session() as session:
                # Create constraints
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (w:WebSource) REQUIRE w.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:RiskIndicator) REQUIRE r.id IS UNIQUE")
                
                # Create indexes
                session.run("CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.name)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (w:WebSource) ON (w.url)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (r:RiskIndicator) ON (r.type)")
                
                logger.info("Database constraints and indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create constraints: {str(e)}")
            raise
    
    def create_or_update_entity(self, entity_data: Dict[str, Any], sanctions_data: Dict[str, Any], web_data: Dict[str, Any]) -> str:
        """Create or update an entity in the graph database"""
        try:
            # Generate entity ID
            entity_id = self._generate_entity_id(entity_data)
            
            with self.driver.session() as session:
                # Create/update entity node
                session.run("""
                    MERGE (e:Entity {id: $entity_id})
                    SET e.name = $name,
                        e.type = $type,
                        e.risk_level = $risk_level,
                        e.updated_at = $timestamp
                """, 
                entity_id=entity_id,
                name=entity_data.get('name', ''),
                type=entity_data.get('type', 'unknown'),
                risk_level=self._determine_risk_level(sanctions_data, web_data),
                timestamp=int(time.time())
                )
                
                # Create web source relationships
                for result in web_data.get('results', []):
                    url = result.get('url', result.get('link', ''))
                    source_id = f"source_{hashlib.md5(url.encode()).hexdigest()[:8]}"
                    
                    # Create web source node
                    session.run("""
                        MERGE (w:WebSource {id: $source_id})
                        SET w.title = $title,
                            w.url = $url,
                            w.source = $source,
                            w.relevance_score = $relevance_score
                    """,
                        source_id=source_id,
                        title=result.get('title', ''),
                        url=url,
                        source=result.get('source', ''),
                        relevance_score=result.get('relevance_score', 0.0)
                    )
                    
                    # Create relationship
                    session.run("""
                        MATCH (e:Entity {id: $entity_id})
                        MATCH (w:WebSource {id: $source_id})
                        MERGE (e)-[r:MENTIONED_IN]->(w)
                        SET r.relevance_score = $relevance_score,
                            r.created_at = $timestamp
                    """,
                        entity_id=entity_id,
                        source_id=source_id,
                        relevance_score=result.get('relevance_score', 0.0),
                        timestamp=int(time.time())
                    )
                
                # Create risk indicators
                for indicator in web_data.get('risk_indicators', []):
                    indicator_id = f"risk_{hashlib.md5(indicator.encode()).hexdigest()[:8]}"
                    
                    # Create risk indicator node
                    session.run("""
                        MERGE (r:RiskIndicator {id: $indicator_id})
                        SET r.description = $description,
                            r.type = $type
                    """,
                        indicator_id=indicator_id,
                        description=indicator,
                        type=indicator.split(':')[0].strip()
                    )
                    
                    # Create relationship
                    session.run("""
                        MATCH (e:Entity {id: $entity_id})
                        MATCH (r:RiskIndicator {id: $indicator_id})
                        MERGE (e)-[rel:HAS_RISK]->(r)
                        SET rel.created_at = $timestamp
                    """,
                        entity_id=entity_id,
                        indicator_id=indicator_id,
                        timestamp=int(time.time())
                    )
                
                # Create sanctions relationships
                for match in sanctions_data.get('matches', []):
                    sanction_id = f"sanction_{hashlib.md5(str(match).encode()).hexdigest()[:8]}"
                    
                    # Create sanction node
                    session.run("""
                        MERGE (s:Sanction {id: $sanction_id})
                        SET s.description = $description,
                            s.confidence = $confidence,
                            s.type = $type
                    """,
                        sanction_id=sanction_id,
                        description=match.get('description', ''),
                        confidence=match.get('confidence', 0),
                        type=match.get('type', 'unknown')
                    )
                    
                    # Create relationship
                    session.run("""
                        MATCH (e:Entity {id: $entity_id})
                        MATCH (s:Sanction {id: $sanction_id})
                        MERGE (e)-[rel:HAS_SANCTION]->(s)
                        SET rel.confidence = $confidence,
                            rel.created_at = $timestamp
                    """,
                        entity_id=entity_id,
                        sanction_id=sanction_id,
                        confidence=match.get('confidence', 0),
                        timestamp=int(time.time())
                    )
            
            return entity_id
            
        except Exception as e:
            logger.error(f"Failed to create/update entity: {str(e)}")
            raise
    
    def analyze_entity_connections(self, entity_id: str) -> Dict[str, Any]:
        """Analyze entity connections and risk factors"""
        try:
            with self.driver.session() as session:
                # Get entity details
                entity_result = session.run("""
                    MATCH (e:Entity {id: $entity_id})
                    RETURN e
                """, entity_id=entity_id).single()
                
                if not entity_result:
                    return {
                        'analysis': 'Entity not found',
                        'connection_count': 0,
                        'risk_connections': 0
                    }
                
                # Count connections
                connection_result = session.run("""
                    MATCH (e:Entity {id: $entity_id})-[r]->(n)
                    RETURN count(r) as connection_count
                """, entity_id=entity_id).single()
                
                # Count risk connections
                risk_result = session.run("""
                    MATCH (e:Entity {id: $entity_id})-[r]->(n)
                    WHERE n:RiskIndicator OR n:Sanction
                    RETURN count(r) as risk_count
                """, entity_id=entity_id).single()
                
                # Get detailed analysis
                analysis_result = session.run("""
                    MATCH (e:Entity {id: $entity_id})-[r]->(n)
                    RETURN type(r) as rel_type, labels(n) as node_type, n.id as node_id
                    ORDER BY rel_type
                """, entity_id=entity_id).data()
                
                return {
                    'analysis': 'Entity connections analyzed',
                    'connection_count': connection_result['connection_count'],
                    'risk_connections': risk_result['risk_count'],
                    'detailed_connections': analysis_result
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze entity connections: {str(e)}")
            return {
                'analysis': f'Error: {str(e)}',
                'connection_count': 0,
                'risk_connections': 0
            }
    
    def get_entity_graph_data(self, entity_id: str) -> Dict[str, Any]:
        """Get complete graph data for an entity"""
        try:
            with self.driver.session() as session:
                # Get all nodes and relationships
                result = session.run("""
                    MATCH (e:Entity {id: $entity_id})
                    CALL {
                        WITH e
                        MATCH (e)-[r]->(n)
                        RETURN collect(DISTINCT n) as nodes,
                               collect(DISTINCT r) as relationships
                    }
                    RETURN e as entity, nodes, relationships
                """, entity_id=entity_id).single()
                
                if not result:
                    return {
                        'entity_id': entity_id,
                        'nodes': [],
                        'relationships': []
                    }
                
                # Format nodes
                nodes = [{
                    'id': node['id'],
                    'labels': list(node.labels),
                    'properties': dict(node)
                } for node in result['nodes']]
                
                # Add entity node
                nodes.append({
                    'id': result['entity']['id'],
                    'labels': list(result['entity'].labels),
                    'properties': dict(result['entity'])
                })
                
                # Format relationships
                relationships = [{
                    'id': rel.id,
                    'type': type(rel).__name__,
                    'startNode': rel.start_node.id,
                    'endNode': rel.end_node.id,
                    'properties': dict(rel)
                } for rel in result['relationships']]
                
                return {
                    'entity_id': entity_id,
                    'nodes': nodes,
                    'relationships': relationships
                }
                
        except Exception as e:
            logger.error(f"Failed to get entity graph data: {str(e)}")
            return {
                'entity_id': entity_id,
                'nodes': [],
                'relationships': []
            }
    
    def _generate_entity_id(self, entity_data: Dict[str, Any]) -> str:
        """Generate a unique entity ID"""
        entity_type = entity_data.get('type', 'unknown')
        name = entity_data.get('name', '')
        
        if entity_type == 'company':
            return f"company_{hashlib.md5(name.lower().encode()).hexdigest()[:8]}"
        else:
            return f"entity_{hashlib.md5(name.lower().encode()).hexdigest()[:8]}"
    
    def _determine_risk_level(self, sanctions_data: Dict[str, Any], web_data: Dict[str, Any]) -> str:
        """Determine risk level based on sanctions and web data"""
        if sanctions_data.get('matched', False):
            return 'HIGH'
        
        risk_indicators = web_data.get('risk_indicators', [])
        if len(risk_indicators) > 2:
            return 'MEDIUM'
        
        return 'LOW'
    
    def close(self):
        """Close Neo4j connection"""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Neo4j connection closed") 