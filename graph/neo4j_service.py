import logging
import os
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
import hashlib
import time
import uuid
import config

logger = logging.getLogger(__name__)

class Neo4jService:
    """Service for graph database operations"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j connection with connection retry logic"""
        self.uri = uri or "bolt://opensancton_neo4j:7687"
        self.user = user or "neo4j"
        self.password = password or "password"
        self.driver = None
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        # Try to establish connection with retries
        self._connect_with_retry()
    
    def _connect_with_retry(self):
        """Attempt to connect to Neo4j with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    max_connection_lifetime=3600
                )
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("Successfully connected to Neo4j")
                return
            except (ServiceUnavailable, AuthError, ClientError) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Neo4j connection attempt {attempt + 1} failed: {str(e)}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to connect to Neo4j after {self.max_retries} attempts: {str(e)}")
                    raise
    
    def _execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Neo4j query with error handling"""
        if not self.driver:
            raise ServiceUnavailable("Neo4j driver not initialized")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def _create_constraints(self):
        """Create database constraints and indexes"""
        try:
            with self.driver.session() as session:
                # Create constraints
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Director) REQUIRE d.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (w:WebSource) REQUIRE w.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:RiskIndicator) REQUIRE r.id IS UNIQUE")
                
                # Create indexes
                session.run("CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.name)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (d:Director) ON (d.name)")
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
            entity_type = entity_data.get('type', 'unknown')
            
            with self.driver.session() as session:
                # Create/update specific entity type node
                if entity_type == 'person':
                    session.run("""
                        MERGE (p:Person:Entity {id: $entity_id})
                        SET p.name = $name,
                            p.type = $type,
                            p.phone = $phone,
                            p.email = $email,
                            p.address = $address,
                            p.country = $country,
                            p.date_of_birth = $date_of_birth,
                            p.risk_level = $risk_level,
                            p.updated_at = $timestamp
                    """, 
                    entity_id=entity_id,
                    name=entity_data.get('name', ''),
                    type=entity_type,
                    phone=entity_data.get('phone', ''),
                    email=entity_data.get('email', ''),
                    address=entity_data.get('address', ''),
                    country=entity_data.get('country', ''),
                    date_of_birth=entity_data.get('date_of_birth', ''),
                    risk_level=self._determine_risk_level(sanctions_data, web_data),
                    timestamp=int(time.time())
                    )
                
                elif entity_type == 'company':
                    session.run("""
                        MERGE (c:Company:Entity {id: $entity_id})
                        SET c.name = $name,
                            c.type = $type,
                            c.phone = $phone,
                            c.address = $address,
                            c.country = $country,
                            c.industry = $industry,
                            c.registration_number = $registration_number,
                            c.website = $website,
                            c.incorporation_date = $incorporation_date,
                            c.risk_level = $risk_level,
                            c.updated_at = $timestamp
                    """, 
                    entity_id=entity_id,
                    name=entity_data.get('name', ''),
                    type=entity_type,
                    phone=entity_data.get('phone', ''),
                    address=entity_data.get('address', ''),
                    country=entity_data.get('country', ''),
                    industry=entity_data.get('industry', ''),
                    registration_number=entity_data.get('registration_number', ''),
                    website=entity_data.get('website', ''),
                    incorporation_date=entity_data.get('incorporation_date', ''),
                    risk_level=self._determine_risk_level(sanctions_data, web_data),
                    timestamp=int(time.time())
                    )
                
                else:
                    # Generic entity
                    session.run("""
                        MERGE (e:Entity {id: $entity_id})
                        SET e.name = $name,
                            e.type = $type,
                            e.risk_level = $risk_level,
                            e.updated_at = $timestamp
                    """, 
                    entity_id=entity_id,
                    name=entity_data.get('name', ''),
                    type=entity_type,
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

    def create_director_relationship(self, director_id: str, company_id: str, 
                                   director_info: Dict[str, Any] = None) -> str:
        """Create director relationship between person and company"""
        try:
            with self.driver.session() as session:
                # Create director node if director_info provided
                if director_info:
                    director_entity_id = f"director_{hashlib.md5(director_id.encode()).hexdigest()[:8]}"
                    
                    session.run("""
                        MERGE (d:Director:Person:Entity {id: $director_id})
                        SET d.name = $name,
                            d.director_id = $external_director_id,
                            d.position = $position,
                            d.appointment_date = $appointment_date,
                            d.status = $status,
                            d.type = 'director',
                            d.updated_at = $timestamp
                    """,
                        director_id=director_entity_id,
                        external_director_id=director_id,
                        name=director_info.get('name', ''),
                        position=director_info.get('position', 'Director'),
                        appointment_date=director_info.get('appointment_date', ''),
                        status=director_info.get('status', 'Active'),
                        timestamp=int(time.time())
                    )
                    
                    # Create relationship between director and company
                    session.run("""
                        MATCH (d:Director {director_id: $director_id})
                        MATCH (c:Company {id: $company_id})
                        MERGE (d)-[r:DIRECTOR_OF]->(c)
                        SET r.position = $position,
                            r.appointment_date = $appointment_date,
                            r.status = $status,
                            r.created_at = $timestamp
                    """,
                        director_id=director_id,
                        company_id=company_id,
                        position=director_info.get('position', 'Director'),
                        appointment_date=director_info.get('appointment_date', ''),
                        status=director_info.get('status', 'Active'),
                        timestamp=int(time.time())
                    )
                    
                    return director_entity_id
                else:
                    # Just create relationship if both entities exist
                    result = session.run("""
                        MATCH (p:Person {id: $director_id})
                        MATCH (c:Company {id: $company_id})
                        MERGE (p)-[r:DIRECTOR_OF]->(c)
                        SET r.created_at = $timestamp
                        RETURN r
                    """,
                        director_id=director_id,
                        company_id=company_id,
                        timestamp=int(time.time())
                    )
                    
                    if result.single():
                        return f"relationship_created_{director_id}_{company_id}"
                    else:
                        logger.warning(f"Could not create director relationship - entities not found")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to create director relationship: {str(e)}")
            raise

    def create_person_company_relationship(self, person_id: str, company_id: str, 
                                         relationship_type: str = "ASSOCIATED_WITH") -> bool:
            """Create relationship between person and company"""
            try:
                query = """
                MATCH (p:Entity {id: $person_id})
                MATCH (c:Entity {id: $company_id})
                MERGE (p)-[r:ASSOCIATED_WITH]->(c)
                SET r.type = $relationship_type,
                    r.created_at = $timestamp
                RETURN r
                """
                
                result = self._execute_query(query, {
                    'person_id': person_id,
                    'company_id': company_id,
                    'relationship_type': relationship_type,
                    'timestamp': int(time.time())
                })
                
                return bool(result)
                
            except Exception as e:
                logger.error(f"Failed to create person-company relationship: {str(e)}")
                return False

    def find_entity_relationships(self, entity_id: str) -> dict:
        """Find all relationships for a given entity."""
        try:
            if not self.driver:
                raise RisknetError("Neo4j driver not initialized")

            with self.driver.session() as session:
                # Query to find all relationships
                query = """
                MATCH (e {id: $entity_id})-[r]-(related)
                RETURN type(r) as relationship_type,
                       e.name as entity_name,
                       related.name as related_name,
                       related.id as related_id,
                       related.type as related_type
                """
                
                result = session.run(query, entity_id=entity_id)
                relationships = []
                
                for record in result:
                    relationship = {
                        'type': record['relationship_type'],
                        'entity_name': record['entity_name'],
                        'related_name': record['related_name'],
                        'related_id': record['related_id'],
                        'related_type': record['related_type']
                    }
                    relationships.append(relationship)
                
                return {
                    'created_relationships': relationships,
                    'director_relationships': [r for r in relationships if r['type'] == 'DIRECTOR_OF'],
                    'entity_relationships': [r for r in relationships if r['type'] != 'DIRECTOR_OF']
                }
                
        except Exception as e:
            logging.error(f"Failed to find entity relationships: {str(e)}")
            return {
                'created_relationships': [],
                'director_relationships': [],
                'entity_relationships': []
            } 