import logging
import requests
import os
from typing import Dict, Any, List
import time
import config  # Import config module

logger = logging.getLogger(__name__)

class WebSearchService:
    """Service for web intelligence gathering"""
    
    def __init__(self):
        """Initialize web search service"""
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        self.fast_mode = False
        logger.info("Web search service initialized")
    
    def search_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for entity information on the web"""
        try:
            entity_name = entity_data.get('name', '')
            entity_type = entity_data.get('type', 'unknown')
            
            if not entity_name:
                return {
                    'results': [],
                    'total_results': 0,
                    'risk_indicators': [],
                    'sentiment_score': 0.0,
                    'sources_searched': []
                }
            
            # Build search query
            query = self._build_search_query(entity_name, entity_type)
            
            # Perform search
            search_results = self._perform_search(query)
            
            # Analyze results
            risk_indicators = self._analyze_risk_indicators(search_results)
            sentiment_score = self._calculate_sentiment(search_results)
            
            return {
                'results': search_results,
                'total_results': len(search_results),
                'risk_indicators': risk_indicators,
                'sentiment_score': sentiment_score,
                'sources_searched': ['Google via Serper']
            }
            
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return {
                'results': [],
                'total_results': 0,
                'risk_indicators': [],
                'sentiment_score': 0.0,
                'sources_searched': []
            }
    
    def _build_search_query(self, entity_name: str, entity_type: str) -> str:
        """Build search query based on entity type"""
        if entity_type == 'company':
            return f'company: "{entity_name}" (sanctions OR criminal OR investigation)'
        else:
            return f'person: "{entity_name}" (sanctions OR criminal OR investigation)'
    
    def _perform_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform web search using available APIs"""
        if self.serper_api_key:
            return self._search_serper(query)
        elif self.perplexity_api_key:
            return self._search_perplexity(query)
        else:
            # Mock results for testing
            return [
                {
                    'title': 'Test Result 1',
                    'url': 'https://example.com/test1',
                    'source': 'example.com',
                    'snippet': 'This is a test result about sanctions and criminal activity.',
                    'relevance_score': 0.8,
                    'search_engine': 'Google'
                },
                {
                    'title': 'Test Result 2',
                    'url': 'https://example.com/test2',
                    'source': 'example.com',
                    'snippet': 'Another test result about regulatory violations.',
                    'relevance_score': 0.7,
                    'search_engine': 'Google'
                }
            ]
    
    def _search_serper(self, query: str) -> List[Dict[str, Any]]:
        """Search using Serper API"""
        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'q': query,
                'gl': 'us',
                'hl': 'en',
                'num': 10
            }
            
            response = requests.post(
                'https://google.serper.dev/search',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                results = response.json()
                organic_results = results.get('organic', [])
                
                return [{
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'source': result.get('source', ''),
                    'snippet': result.get('snippet', ''),
                    'relevance_score': 0.8,  # Default score
                    'search_engine': 'Google'
                } for result in organic_results]
            
            return []
            
        except Exception as e:
            logger.error(f"Serper search failed: {str(e)}")
            return []
    
    def _search_perplexity(self, query: str) -> List[Dict[str, Any]]:
        """Search using Perplexity API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'query': query,
                'max_results': 10
            }
            
            response = requests.post(
                'https://api.perplexity.ai/search',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                results = response.json()
                
                return [{
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'source': result.get('source', ''),
                    'snippet': result.get('snippet', ''),
                    'relevance_score': result.get('relevance_score', 0.8),
                    'search_engine': 'Perplexity'
                } for result in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Perplexity search failed: {str(e)}")
            return []
    
    def _analyze_risk_indicators(self, results: List[Dict[str, Any]]) -> List[str]:
        """Analyze search results for risk indicators"""
        risk_indicators = []
        risk_keywords = {
            'criminal': 'Criminal related',
            'sanction': 'Sanctions related',
            'violation': 'Regulatory related',
            'investigation': 'Regulatory related',
            'fraud': 'Criminal related',
            'corruption': 'Criminal related',
            'money laundering': 'Criminal related',
            'terrorism': 'Sanctions related',
            'sdn': 'Sanctions related',
            'regulatory': 'Regulatory related'
        }
        
        for result in results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            
            for keyword, category in risk_keywords.items():
                if keyword in text:
                    indicator = f"{category}: {keyword}"
                    if indicator not in risk_indicators:
                        risk_indicators.append(indicator)
        
        return risk_indicators
    
    def _calculate_sentiment(self, results: List[Dict[str, Any]]) -> float:
        """Calculate sentiment score from search results"""
        if not results:
            return 0.0
        
        # Simple sentiment analysis based on keywords
        positive_words = {'success', 'growth', 'innovation', 'positive', 'achievement'}
        negative_words = {'criminal', 'sanction', 'violation', 'investigation', 'fraud', 'corruption'}
        
        total_score = 0.0
        for result in results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            
            # Count positive and negative words
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            # Calculate score for this result (-1 to 1)
            if positive_count + negative_count > 0:
                score = (positive_count - negative_count) / (positive_count + negative_count)
                total_score += score
        
        # Return average sentiment (-1 to 1)
        return total_score / len(results) if results else 0.0
    
    def set_fast_mode(self, enabled: bool):
        """Enable or disable fast mode"""
        self.fast_mode = enabled
        logger.info(f"Web search fast mode {'enabled' if enabled else 'disabled'}") 