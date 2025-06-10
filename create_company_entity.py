from graph.neo4j_service import Neo4jService
import logging
import hashlib
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_company_entity():
    """Create InnoTech Labs company entity with proper connections"""
    try:
        # Initialize Neo4j service
        service = Neo4jService()
        
        # Company data
        company_data = {
            'name': 'InnoTech Labs',
            'type': 'company',
            'address': '100 IT Park, Whitefield, Bengaluru, Karnataka, India',
            'phone': '+91-80-12345678'
        }
        
        # Generate company ID
        company_id = f"company_{hashlib.md5(company_data['name'].lower().encode()).hexdigest()[:8]}"
        
        # Create the company entity in Neo4j
        with service.driver.session() as session:
            # Create company node
            session.run("""
                MERGE (c:Company {id: $company_id})
                SET c.name = $name,
                    c.type = $type,
                    c.address = $address,
                    c.phone = $phone,
                    c.risk_level = $risk_level,
                    c.updated_at = $timestamp
            """, 
            company_id=company_id,
            name=company_data['name'],
            type=company_data['type'],
            address=company_data['address'],
            phone=company_data['phone'],
            risk_level='MEDIUM',  # Based on the risk assessment
            timestamp=int(time.time())
            )
            
            # Create web source relationships
            web_sources = [
                {
                    'title': 'Khairun Niza - Administrative - innotech labs sdn bhd',
                    'url': 'https://my.linkedin.com/in/khairun-niza-0107a128b',
                    'source': 'my.linkedin.com',
                    'relevance_score': 0.8
                },
                {
                    'title': 'Work with Us | Urban Journalism Network',
                    'url': 'https://www.linkedin.com/posts/urban-journalism-network_work-with-us-activity-7267529431051558912-sT6N',
                    'source': 'linkedin.com',
                    'relevance_score': 0.8
                },
                {
                    'title': 'Terms Of Service',
                    'url': 'https://www.myb2b.com.my/terms-of-service',
                    'source': 'myb2b.com.my',
                    'relevance_score': 0.8
                }
            ]
            
            for source in web_sources:
                url = source.get('url', source.get('link', ''))
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
                    title=source['title'],
                    url=url,
                    source=source['source'],
                    relevance_score=source['relevance_score']
                )
                
                # Create relationship
                session.run("""
                    MATCH (c:Company {id: $company_id})
                    MATCH (w:WebSource {id: $source_id})
                    MERGE (c)-[r:MENTIONED_IN]->(w)
                    SET r.relevance_score = $relevance_score,
                        r.created_at = $timestamp
                """,
                    company_id=company_id,
                    source_id=source_id,
                    relevance_score=source['relevance_score'],
                    timestamp=int(time.time())
                )
            
            # Create risk indicators
            risk_indicators = [
                "Criminal related: criminal",
                "Sanctions related: sdn",
                "Sanctions related: sanction",
                "Regulatory related: violation",
                "Regulatory related: regulatory"
            ]
            
            for indicator in risk_indicators:
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
                    MATCH (c:Company {id: $company_id})
                    MATCH (r:RiskIndicator {id: $indicator_id})
                    MERGE (c)-[rel:HAS_RISK]->(r)
                    SET rel.created_at = $timestamp
                """,
                    company_id=company_id,
                    indicator_id=indicator_id,
                    timestamp=int(time.time())
                )
        
        logger.info(f"Created company entity with ID: {company_id}")
        
        # Get graph data for the company
        graph_data = service.get_entity_graph_data(company_id)
        logger.info(f"Graph data: {graph_data}")
        
        # Clean up
        service.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create company entity: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_company_entity()
    print(f"Test {'passed' if success else 'failed'}") 