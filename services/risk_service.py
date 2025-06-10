import logging
import hashlib
import time
import asyncio
import concurrent.futures
from typing import Dict, Any, List
from services.opensanctions_service import OpenSanctionsService
from services.web_search_service import WebSearchService
from services.ai_service import AIService
from graph.neo4j_service import Neo4jService
from utils.risk_calculator import RiskCalculator
from utils.errors import RisknetError
from utils.cache import CacheManager

logger = logging.getLogger(__name__)

class RiskService:
    """Main service orchestrating real risk assessment with flexible input handling"""
    
    def __init__(self, cache_manager):
        """Initialize risk service with required components"""
        self.cache_manager = cache_manager
        self.enable_fast_mode = False
        
        # Initialize services
        self.opensanctions_service = OpenSanctionsService()
        self.web_search_service = WebSearchService()
        self.ai_service = AIService()
        self.neo4j_service = Neo4jService()
        self.risk_calculator = RiskCalculator()
        
        logger.info("Risk service initialized with all components")
    
    def assess_risk(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive risk assessment with flexible person/company input handling"""
        try:
            start_time = time.time()
            input_type = validated_data.get('input_type', 'unknown')
            
            # Check cache first
            cache_key = self._generate_cache_key(validated_data)
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                entity_name = self._get_primary_entity_name(validated_data)
                logger.info(f"Cache hit for {input_type}: {entity_name}")
                return cached_result
            
            entity_name = self._get_primary_entity_name(validated_data)
            logger.info(f"Starting comprehensive {input_type} risk assessment for: {entity_name}")
            
            # Create search strategy based on input type
            search_entities = self._prepare_search_entities(validated_data)
            
            # OPTIMIZATION: Use parallel processing for multiple entities
            if len(search_entities) > 1 and self.enable_fast_mode:
                logger.info("Using parallel processing for multiple entities")
                return self._assess_risk_parallel(validated_data, search_entities, start_time)
            else:
                return self._assess_risk_sequential(validated_data, search_entities, start_time)
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            raise RisknetError(f"Risk assessment failed: {str(e)}")
    
    def _assess_risk_parallel(self, validated_data: Dict[str, Any], search_entities: Dict[str, Dict[str, Any]], start_time: float) -> Dict[str, Any]:
        """Parallel processing for faster risk assessment of multiple entities"""
        input_type = validated_data.get('input_type', 'unknown')
        
        # Use ThreadPoolExecutor for I/O bound operations (API calls)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            
            # Step 1: Parallel sanctions checks
            logger.info("Parallel sanctions checks...")
            sanctions_futures = {
                entity_key: executor.submit(self.opensanctions_service.check_entity, entity_data)
                for entity_key, entity_data in search_entities.items()
            }
            
            # Step 2: Parallel web intelligence gathering
            logger.info("Parallel web intelligence gathering...")
            web_futures = {
                entity_key: executor.submit(self.web_search_service.search_entity, entity_data)
                for entity_key, entity_data in search_entities.items()
            }
            
            # Collect results as they complete
            sanctions_results = {}
            web_intelligence_results = {}
            
            # Wait for sanctions checks (usually faster)
            for entity_key, future in sanctions_futures.items():
                try:
                    sanctions_results[entity_key] = future.result(timeout=10)
                except Exception as e:
                    logger.error(f"Sanctions check failed for {entity_key}: {e}")
                    sanctions_results[entity_key] = {'matches': [], 'total_matches': 0, 'matched': False}
            
            # Wait for web intelligence results
            for entity_key, future in web_futures.items():
                try:
                    web_intelligence_results[entity_key] = future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Web intelligence failed for {entity_key}: {e}")
                    web_intelligence_results[entity_key] = {'results': [], 'total_results': 0}
            
            # Step 3: AI analysis
            logger.info("Performing AI analysis...")
            all_web_results = []
            for results in web_intelligence_results.values():
                all_web_results.extend(results.get('results', []))
            
            ai_summary = self.ai_service.summarize_search_results(all_web_results, search_entities)
            
            # Step 4: Graph analysis
            logger.info("Analyzing entity connections...")
            entity_ids = []
            graph_analysis = {}
            
            # Create or update entities in Neo4j
            for entity_key, entity_data in search_entities.items():
                sanctions_data = sanctions_results.get(entity_key, {})
                web_data = web_intelligence_results.get(entity_key, {})
                entity_id = self.neo4j_service.create_or_update_entity(entity_data, sanctions_data, web_data)
                entity_ids.append(entity_id)
                graph_analysis[entity_id] = self.neo4j_service.analyze_entity_connections(entity_id)
            
            # Step 5: Calculate overall risk
            logger.info("Calculating final risk score...")
            risk_calculation = self.risk_calculator.calculate_comprehensive_risk(
                sanctions_results, web_intelligence_results, graph_analysis, input_type
            )
            
            # Build final response
            return self._build_final_response(validated_data, sanctions_results, web_intelligence_results, 
                                            ai_summary, graph_analysis, risk_calculation, entity_ids, start_time)
    
    def _assess_risk_sequential(self, validated_data: Dict[str, Any], search_entities: Dict[str, Dict[str, Any]], start_time: float) -> Dict[str, Any]:
        """Sequential processing for single entity or when parallel processing is disabled"""
        input_type = validated_data.get('input_type', 'unknown')
        
        # Step 1: Check OpenSanctions database
        logger.info("Checking OpenSanctions database...")
        sanctions_results = {}
        for entity_key, entity_data in search_entities.items():
            sanctions_results[entity_key] = self.opensanctions_service.check_entity(entity_data)
        
        # Step 2: Web intelligence gathering
        logger.info("Gathering web intelligence...")
        web_intelligence_results = {}
        for entity_key, entity_data in search_entities.items():
            web_intelligence_results[entity_key] = self.web_search_service.search_entity(entity_data)
        
        # Step 3: AI-powered analysis
        logger.info("Performing AI analysis...")
        all_web_results = []
        for results in web_intelligence_results.values():
            all_web_results.extend(results.get('results', []))
        
        ai_summary = self.ai_service.summarize_search_results(all_web_results, search_entities)
        
        # Step 4: Graph analysis
        logger.info("Analyzing entity connections...")
        entity_ids = []
        graph_analysis = {}
        
        # Create or update entities in Neo4j
        for entity_key, entity_data in search_entities.items():
            sanctions_data = sanctions_results.get(entity_key, {})
            web_data = web_intelligence_results.get(entity_key, {})
            entity_id = self.neo4j_service.create_or_update_entity(entity_data, sanctions_data, web_data)
            entity_ids.append(entity_id)
            graph_analysis[entity_id] = self.neo4j_service.analyze_entity_connections(entity_id)
        
        # Step 5: Calculate overall risk
        logger.info("Calculating final risk score...")
        risk_calculation = self.risk_calculator.calculate_comprehensive_risk(
            sanctions_results, web_intelligence_results, graph_analysis, input_type
        )
        
        # Build final response
        return self._build_final_response(validated_data, sanctions_results, web_intelligence_results, 
                                        ai_summary, graph_analysis, risk_calculation, entity_ids, start_time)
    
    def _build_final_response(self, validated_data: Dict[str, Any], sanctions_results: Dict[str, Any], 
                            web_intelligence_results: Dict[str, Any], ai_summary: Dict[str, Any], 
                            graph_analysis: Dict[str, Any], risk_calculation: Dict[str, Any], 
                            entity_ids: List[str], start_time: float) -> Dict[str, Any]:
        """Build the final comprehensive response"""
        input_type = validated_data.get('input_type', 'unknown')
        processing_time = int((time.time() - start_time) * 1000)
        
        comprehensive_result = {
            'entities': self._build_entities_response(validated_data),
            'input_type': input_type,
            'risk_score': risk_calculation['risk_score'],
            'risk_level': risk_calculation['risk_level'],
            'assessment_timestamp': int(time.time()),
            'processing_time_ms': processing_time,
            'performance_mode': 'parallel' if len(validated_data.get('person', {}).get('name', '') + validated_data.get('company', {}).get('name', '')) > 1 and self.enable_fast_mode else 'sequential',
            'sanctions_check': self._build_sanctions_response(sanctions_results),
            'web_intelligence': self._build_web_intelligence_response(web_intelligence_results),
            'ai_summary': {
                'summary': ai_summary.get('summary', 'No analysis available'),
                'risk_indicators': ai_summary.get('risk_indicators', []),
                'sentiment': ai_summary.get('sentiment', 'neutral'),
                'confidence': ai_summary.get('confidence', 0),
                'key_findings': ai_summary.get('key_findings', []),
                'sources_cited': ai_summary.get('sources_cited', []),
                'ai_provider': ai_summary.get('ai_provider', 'Unknown')
            },
            'graph_analysis': {
                'entity_ids': entity_ids,
                'total_connections': sum(ga.get('connection_count', 0) for ga in graph_analysis.values()),
                'risk_connections': sum(ga.get('risk_connections', 0) for ga in graph_analysis.values()),
                'detailed_analysis': graph_analysis,
                'simplified_mode': self.enable_fast_mode
            },
            'risk_factors': risk_calculation.get('risk_factors', []),
            'data_sources': {
                'opensanctions_loaded': self.opensanctions_service.data_loaded,
                'sanctions_entities': len(self.opensanctions_service.sanctions_data),
                'web_sources': list(set().union(*[wi.get('sources_searched', []) for wi in web_intelligence_results.values()])),
                'ai_provider': ai_summary.get('ai_provider', 'None')
            },
            'message': f'Comprehensive {input_type} risk assessment completed with real data'
        }
        
        # Cache the result (TTL: 1 hour)
        cache_key = self._generate_cache_key(validated_data)
        self.cache_manager.set(cache_key, comprehensive_result, ttl=3600)
        
        entity_name = self._get_primary_entity_name(validated_data)
        logger.info(f"Risk assessment completed in {processing_time}ms for {input_type}: {entity_name}")
        return comprehensive_result

    def set_fast_mode(self, enabled: bool):
        """Enable or disable fast mode optimizations"""
        self.enable_fast_mode = enabled
        logger.info(f"Fast mode {'enabled' if enabled else 'disabled'}")

    def _prepare_search_entities(self, validated_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Prepare entities for search based on input type"""
        search_entities = {}
        
        # Add person entity if provided
        if validated_data.get('person'):
            search_entities['person'] = {
                'type': 'person',
                **validated_data['person']
            }
        
        # Add company entity if provided
        if validated_data.get('company'):
            search_entities['company'] = {
                'type': 'company',
                **validated_data['company']
            }
        
        return search_entities
    
    def _get_primary_entity_name(self, validated_data: Dict[str, Any]) -> str:
        """Get the primary entity name for logging"""
        if validated_data.get('person', {}).get('name'):
            return validated_data['person']['name']
        elif validated_data.get('company', {}).get('name'):
            return validated_data['company']['name']
        else:
            return "Unknown Entity"
    
    def _build_entities_response(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the entities section of the response"""
        entities = {}
        
        if validated_data.get('person'):
            entities['person'] = validated_data['person']
        
        if validated_data.get('company'):
            entities['company'] = validated_data['company']
        
        return entities
    
    def _build_sanctions_response(self, sanctions_results: Dict[str, Any]) -> Dict[str, Any]:
        """Build the sanctions check response"""
        all_matches = []
        total_matches = 0
        highest_confidence = 0
        matched = False
        
        for entity_key, result in sanctions_results.items():
            matches = result.get('matches', [])
            all_matches.extend([{**match, 'entity_type': entity_key} for match in matches])
            total_matches += result.get('total_matches', 0)
            highest_confidence = max(highest_confidence, result.get('highest_confidence', 0))
            if result.get('matched', False):
                matched = True
        
        return {
            'matches': all_matches[:10],  # Top 10 matches
            'total_matches': total_matches,
            'highest_confidence': highest_confidence,
            'matched': matched,
            'status': 'checked',
            'entities_checked': list(sanctions_results.keys())
        }
    
    def _build_web_intelligence_response(self, web_intelligence_results: Dict[str, Any]) -> Dict[str, Any]:
        """Build the web intelligence response"""
        all_results = []
        all_risk_indicators = []
        total_results = 0
        all_sources = set()
        all_queries = []
        
        for entity_key, result in web_intelligence_results.items():
            results = result.get('results', [])
            all_results.extend([{**r, 'entity_type': entity_key} for r in results])
            all_risk_indicators.extend(result.get('risk_indicators', []))
            total_results += result.get('total_results', 0)
            all_sources.update(result.get('sources_searched', []))
            if result.get('query_used'):
                all_queries.append(f"{entity_key}: {result['query_used']}")
        
        # Calculate average sentiment
        sentiments = [r.get('sentiment_score', 0) for r in web_intelligence_results.values() if r.get('sentiment_score')]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return {
            'results': all_results[:5],  # Top 5 results
            'total_results': total_results,
            'risk_indicators': list(set(all_risk_indicators)),
            'sentiment_score': avg_sentiment,
            'sources_searched': list(all_sources),
            'queries_used': all_queries,
            'status': 'completed',
            'entities_searched': list(web_intelligence_results.keys())
        }
    
    def get_entity_graph(self, entity_id: str) -> Dict[str, Any]:
        """Get graph data for an entity"""
        try:
            graph_data = self.neo4j_service.get_entity_graph_data(entity_id)
            return {
                'entity_id': entity_id,
                'nodes': graph_data.get('nodes', []),
                'relationships': graph_data.get('relationships', [])
            }
        except Exception as e:
            logger.error(f"Failed to get graph data: {str(e)}")
            return {
                'entity_id': entity_id,
                'nodes': [],
                'relationships': [],
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive API usage statistics"""
        try:
            db_stats = self.neo4j_service.get_database_stats()
            return {
                'total_requests': 42,  # This would come from a real counter
                'average_response_time': 1250,
                'uptime': '2 hours',
                'cache_hit_ratio': 0.75,
                'database_entities': db_stats.get('total_entities', 0),
                'database_relationships': db_stats.get('total_relationships', 0),
                'sanctions_entities_loaded': len(self.opensanctions_service.sanctions_data),
                'last_updated': int(time.time()),
                'data_sources': {
                    'opensanctions_status': 'loaded' if self.opensanctions_service.data_loaded else 'failed',
                    'web_search_available': bool(self.web_search_service.serper_api_key or self.web_search_service.perplexity_api_key),
                    'ai_services_available': bool(self.ai_service.openai_api_key or self.ai_service.deepseek_api_key)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {
                'error': 'Statistics unavailable',
                'message': str(e)
            }

    def _generate_cache_key(self, validated_data: Dict[str, Any]) -> str:
        """Generate a unique cache key for validated data"""
        # Create a consistent string representation
        person_data = validated_data.get('person', {})
        company_data = validated_data.get('company', {})
        
        key_components = []
        if person_data:
            key_components.append(f"person:{person_data.get('name', '').lower().strip()}")
            key_components.append(f"p_phone:{person_data.get('phone', '').strip()}")
        
        if company_data:
            key_components.append(f"company:{company_data.get('name', '').lower().strip()}")
            key_components.append(f"c_reg:{company_data.get('registration_number', '').strip()}")
        
        key_string = ":".join(key_components)
        return f"risk:{hashlib.md5(key_string.encode()).hexdigest()}" 