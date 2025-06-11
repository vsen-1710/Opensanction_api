import logging
import requests
import json
import os
from typing import Dict, Any, List
import time
from config import (
    SERPER_API_KEY, PERPLEXITY_API_KEY, 
    MAX_WEB_RESULTS, API_TIMEOUT,
    ENABLE_FAST_MODE
)

logger = logging.getLogger(__name__)

class WebSearchService:
    """Web search service for real-time entity intelligence"""
    
    def __init__(self):
        self.fast_mode = False
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        self.trusted_sources = {
            'bbc.com': 'News',
            'theguardian.com': 'News',
            'apnews.com': 'News',
            'opensanctions.org': 'Sanctions',
            'treasury.gov': 'Government',
            'fincen.gov': 'Government',
            'aljazeera.com': 'News',
            'forbes.com': 'News',
            'npr.org': 'News',
            'dw.com': 'News',
            'abcnews.go.com': 'News',
            'voanews.com': 'News',      
            'indiatoday.in': 'News',
            'hindustantimes.com': 'News',
            'livemint.com': 'News',
            'france24.com': 'News'
        }

        logger.info("Web search service initialized for real-time search")
    
    def set_fast_mode(self, enabled: bool):
        """Set fast mode for optimized performance"""
        self.fast_mode = enabled
        logger.info(f"Web search fast mode {'enabled' if enabled else 'disabled'}")
    
    def search_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for entity information using available APIs"""
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
            
            # Try real API searches first
            results = []
            sources_searched = []
            
            # Try Serper API
            if self.serper_api_key:
                serper_results = self._search_with_serper(entity_name, entity_type)
                results.extend(serper_results)
                sources_searched.append('Serper API')
            
            # Try Perplexity API
            if self.perplexity_api_key:
                perplexity_results = self._search_with_perplexity(entity_name, entity_type)
                results.extend(perplexity_results)
                sources_searched.append('Perplexity API')
            
            # If no APIs available, return empty but valid response
            if not results:
                logger.info(f"No web search APIs available for {entity_name}")
                return {
                    'results': [],
                    'total_results': 0,
                    'risk_indicators': [],
                    'sentiment_score': 0.0,
                    'risk_score': 0,
                    'trusted_sources_used': [],
                    'sources_searched': sources_searched or ['No APIs configured']
                }
            
            # Analyze results
            risk_indicators = self._analyze_risk_indicators(results)
            sentiment_score = self._calculate_sentiment(results)
            risk_score = self._calculate_risk_score(results, risk_indicators)
            
            return {
                'results': results[:MAX_WEB_RESULTS],  # Use configured limit
                'total_results': len(results),
                'risk_indicators': risk_indicators,
                'sentiment_score': sentiment_score,
                'risk_score': risk_score,
                'trusted_sources_used': self._get_trusted_sources_used(results),
                'sources_searched': sources_searched,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return {
                'results': [],
                'total_results': 0,
                'risk_indicators': [],
                'sentiment_score': 0.0,
                'risk_score': 0,
                'trusted_sources_used': [],
                'sources_searched': ['Error']
            }
    
    def _search_with_serper(self, entity_name: str, entity_type: str) -> List[Dict[str, Any]]:
        """Search using Serper API"""
        try:
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            # Create search query
            query = f'"{entity_name}" sanctions risk compliance investigation'
            
            payload = {
                'q': query,
                'num': 10 if not self.fast_mode else 5
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('organic', []):
                    results.append({
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'url': item.get('link', ''),
                        'source': self._extract_domain(item.get('link', '')),
                        'date': item.get('date', 'Unknown')
                    })
                
                logger.info(f"Serper API returned {len(results)} results for {entity_name}")
                return results
            else:
                logger.warning(f"Serper API failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Serper API search failed: {str(e)}")
            return []
    
    def _search_with_perplexity(self, entity_name: str, entity_type: str) -> List[Dict[str, Any]]:
        """Search using Perplexity API"""
        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            messages = [
                {
                    "role": "user",
                    "content": f"Search for recent news, sanctions, investigations, or compliance issues related to {entity_name}. Include sources and dates."
                }
            ]
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": messages,
                "max_tokens": 500 if self.fast_mode else 1000,
                "temperature": 0.1,
                "return_citations": True
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                citations = data.get('citations', [])
                
                # Parse the response to extract structured results
                results = self._parse_perplexity_response(content, citations, entity_name)
                logger.info(f"Perplexity API returned {len(results)} results for {entity_name}")
                return results
            else:
                logger.warning(f"Perplexity API failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Perplexity API search failed: {str(e)}")
            return []
    
    def _parse_perplexity_response(self, content: str, citations: List[Dict], entity_name: str) -> List[Dict[str, Any]]:
        """Parse Perplexity API response into structured results"""
        results = []
        
        # Extract information from citations
        for citation in citations:
            url = citation.get('url', '')
            title = citation.get('title', '')
            
            if url and title:
                results.append({
                    'title': title,
                    'snippet': content[:200] + '...' if len(content) > 200 else content,
                    'url': url,
                    'source': self._extract_domain(url),
                    'date': 'Recent'
                })
        
        # If no citations, create a single result from the content
        if not results and content:
            results.append({
                'title': f'Intelligence Report on {entity_name}',
                'snippet': content,
                'url': 'https://perplexity.ai',
                'source': 'perplexity.ai',
                'date': 'Recent'
            })
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return url
    
    def _analyze_risk_indicators(self, results: List[Dict[str, Any]]) -> List[str]:
        """Analyze results for risk indicators"""
        risk_indicators = []
        risk_keywords = {
            'sanctions': ['sanctions', 'sanctioned', 'ofac', 'sdn list', 'embargo', 'asset freeze'],
            'criminal': ['criminal', 'arrest', 'charged', 'convicted', 'fraud', 'embezzlement'],
            'investigation': ['investigation', 'probe', 'inquiry', 'under investigation', 'being investigated'],
            'money_laundering': ['money laundering', 'aml violation', 'financial crime', 'suspicious transactions'],
            'terrorism': ['terrorism', 'terrorist', 'terror financing', 'terrorist organization'],
            'corruption': ['corruption', 'bribery', 'corrupt', 'kickback', 'corrupt practices'],
            'regulatory': ['regulatory violation', 'compliance violation', 'penalty', 'fine', 'settlement']
        }
        
        for result in results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            
            for category, keywords in risk_keywords.items():
                if any(keyword in text for keyword in keywords):
                    indicator = f"{category.replace('_', ' ').title()} indicators found"
                    if indicator not in risk_indicators:
                        risk_indicators.append(indicator)
        
        return risk_indicators
    
    def _calculate_sentiment(self, results: List[Dict[str, Any]]) -> float:
        """Calculate sentiment score from results"""
        if not results:
            return 0.0
        
        negative_keywords = ['scandal', 'investigation', 'sanctions', 'criminal', 'fraud', 'violation', 'penalty']
        positive_keywords = ['successful', 'award', 'achievement', 'growth', 'expansion', 'innovation']
        
        negative_count = 0
        positive_count = 0
        total_words = 0
        
        for result in results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            words = text.split()
            total_words += len(words)
            
            for word in words:
                if any(neg_word in word for neg_word in negative_keywords):
                    negative_count += 1
                elif any(pos_word in word for pos_word in positive_keywords):
                    positive_count += 1
        
        if total_words == 0:
            return 0.0
        
        # Calculate sentiment score between -1 and 1
        sentiment = (positive_count - negative_count) / max(total_words / 10, 1)
        return max(-1.0, min(1.0, sentiment))
    
    def _calculate_risk_score(self, results: List[Dict[str, Any]], risk_indicators: List[str]) -> int:
        """Calculate risk score based on results"""
        if not results:
            return 0
        
        score = 0
        
        # Base score from number of risk indicators
        score += len(risk_indicators) * 15
        
        # Additional score from trusted sources
        trusted_results = [r for r in results if self._is_trusted_source(r.get('source', ''))]
        score += len(trusted_results) * 10
        
        # High-risk keywords get extra points
        high_risk_keywords = ['sanctions', 'terrorism', 'criminal', 'money laundering']
        for result in results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            if any(keyword in text for keyword in high_risk_keywords):
                score += 20
        
        return min(100, score)
    
    def _is_trusted_source(self, source: str) -> bool:
        """Check if source is trusted"""
        return source.lower() in [domain.lower() for domain in self.trusted_sources.keys()]
    
    def _get_trusted_sources_used(self, results: List[Dict[str, Any]]) -> List[str]:
        """Get list of trusted sources used"""
        trusted_sources = []
        for result in results:
            source = result.get('source', '')
            if self._is_trusted_source(source) and source not in trusted_sources:
                trusted_sources.append(source)
        return trusted_sources 