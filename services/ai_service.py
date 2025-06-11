import logging
import json
import requests
import os
from typing import Dict, Any, List
import time
import re
from config import (
    OPENAI_API_KEY, DEEPSEEK_API_KEY, 
    AI_MAX_TOKENS, AI_TEMPERATURE, API_TIMEOUT,
    MAX_KEY_FINDINGS, MAX_RISK_INDICATORS,
    ENABLE_FAST_MODE
)

logger = logging.getLogger(__name__)

class AIService:
    """AI service for intelligent risk analysis"""
    
    def __init__(self):
        self.fast_mode = False
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        logger.info("AI service initialized for intelligent analysis")
    
    def set_fast_mode(self, enabled: bool):
        """Set fast mode for optimized performance"""
        self.fast_mode = enabled
        logger.info(f"AI service fast mode {'enabled' if enabled else 'disabled'}")
    
    def summarize_search_results(self, search_results: List[Dict[str, Any]], entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize search results using AI analysis"""
        try:
            if not search_results:
                return self._create_fallback_summary([], entity_data)
            
            entity_name = entity_data.get('name', 'Unknown')
            entity_type = entity_data.get('type', 'unknown')
            
            # Try AI-powered analysis first
            ai_summary = None
            
            # Try OpenAI
            if self.openai_api_key:
                ai_summary = self._analyze_with_openai(search_results, entity_name, entity_type)
            
            # Try DeepSeek if OpenAI failed
            if not ai_summary and self.deepseek_api_key:
                ai_summary = self._analyze_with_deepseek(search_results, entity_name, entity_type)
            
            # Fallback to rule-based analysis if no AI available
            if not ai_summary:
                logger.info(f"No AI APIs available, using rule-based analysis for {entity_name}")
                return self._create_fallback_summary(search_results, entity_data)
            
            return ai_summary
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._create_fallback_summary(search_results, entity_data)
    
    def _analyze_with_openai(self, search_results: List[Dict[str, Any]], entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Analyze using OpenAI API"""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare search results text
            results_text = self._format_results_for_ai(search_results)
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a risk analyst specializing in sanctions, compliance, and entity due diligence. Analyze the provided search results and provide a comprehensive risk assessment."
                },
                {
                    "role": "user",
                    "content": f"Analyze these search results for {entity_name} ({entity_type}) and provide a risk assessment:\n\n{results_text}\n\nProvide: 1) Summary 2) Risk indicators 3) Key findings 4) Confidence level (0-1) 5) Sentiment (-1 to 1)"
                }
            ]
            
            payload = {
                "model": "gpt-3.5-turbo" if ENABLE_FAST_MODE else "gpt-4",
                "messages": messages,
                "max_tokens": AI_MAX_TOKENS,
                "temperature": AI_TEMPERATURE
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return self._parse_ai_response(content, entity_name, 'OpenAI')
            else:
                logger.warning(f"OpenAI API failed with status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            return None
    
    def _analyze_with_deepseek(self, search_results: List[Dict[str, Any]], entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Analyze using DeepSeek API"""
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.deepseek_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare search results text
            results_text = self._format_results_for_ai(search_results)
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a risk analyst specializing in sanctions, compliance, and entity due diligence. Analyze the provided search results and provide a comprehensive risk assessment."
                },
                {
                    "role": "user",
                    "content": f"Analyze these search results for {entity_name} ({entity_type}) and provide a risk assessment:\n\n{results_text}\n\nProvide: 1) Summary 2) Risk indicators 3) Key findings 4) Confidence level (0-1) 5) Sentiment (-1 to 1)"
                }
            ]
            
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": AI_MAX_TOKENS,
                "temperature": AI_TEMPERATURE
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return self._parse_ai_response(content, entity_name, 'DeepSeek')
            else:
                logger.warning(f"DeepSeek API failed with status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"DeepSeek analysis failed: {str(e)}")
            return None
    
    def _format_results_for_ai(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results for AI analysis"""
        formatted_results = []
        
        for i, result in enumerate(search_results[:10], 1):  # Limit to top 10 results
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')
            source = result.get('source', 'Unknown source')
            date = result.get('date', 'Unknown date')
            
            formatted_results.append(f"{i}. Title: {title}\n   Source: {source}\n   Date: {date}\n   Content: {snippet}\n")
        
        return "\n".join(formatted_results)
    
    def _parse_ai_response(self, content: str, entity_name: str, ai_provider: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        if not content:
            return {
                'summary': f"AI analysis completed for {entity_name}",
                'risk_indicators': [],
                'sentiment': 0.0,
                'confidence': 0.5,
                'key_findings': [],
                'sources_cited': [],
                'ai_provider': ai_provider
            }

        try:
            # Extract risk indicators, key findings, etc. from the AI response
            risk_indicators = self._extract_risk_indicators_from_text(content)
            key_findings = self._extract_key_findings_from_text(content)
            confidence = self._extract_confidence_from_text(content)
            sentiment = self._extract_sentiment_from_text(content)
            
            # Clean up the summary - avoid truncation mid-sentence
            summary = content
            if len(content) > 500:
                # Find the last complete sentence within 500 characters
                truncated = content[:500]
                last_period = truncated.rfind('.')
                last_exclamation = truncated.rfind('!')
                last_question = truncated.rfind('?')
                
                # Find the last sentence ending
                last_sentence_end = max(last_period, last_exclamation, last_question)
                
                if last_sentence_end > 200:  # Ensure we have a reasonable amount of content
                    summary = content[:last_sentence_end + 1]
                else:
                    # If no good sentence break, truncate at last word boundary
                    truncated = content[:500]
                    last_space = truncated.rfind(' ')
                    if last_space > 200:
                        summary = content[:last_space] + "..."
                    else:
                        summary = truncated + "..."
            
            return {
                'summary': summary,
                'risk_indicators': risk_indicators,
                'sentiment': sentiment,
                'confidence': confidence,
                'key_findings': key_findings,
                'sources_cited': [],  # Would be extracted from the AI response
                'ai_provider': ai_provider
            }
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            return {
                'summary': content[:500] if content else f"AI analysis completed for {entity_name}",
                'risk_indicators': [],
                'sentiment': 0.0,
                'confidence': 0.5,
                'key_findings': [],
                'sources_cited': [],
                'ai_provider': ai_provider
            }
    
    def _extract_risk_indicators_from_text(self, text: str) -> List[str]:
        """Extract risk indicators from AI response text"""
        risk_indicators = []
        text_lower = text.lower()
        
        # Look for common risk patterns in the AI response
        risk_patterns = {
            'sanctions': 'sanctions indicators',
            'investigation': 'under investigation',
            'criminal': 'criminal activity',
            'terrorism': 'terrorism related',
            'corruption': 'corruption allegations',
            'money laundering': 'money laundering',
            'financial crime': 'financial crimes'
        }
        
        for pattern, indicator in risk_patterns.items():
            if pattern in text_lower:
                risk_indicators.append(indicator)
        
        return risk_indicators
    
    def _extract_key_findings_from_text(self, text: str) -> List[str]:
        """Extract key findings from AI response"""
        key_findings = []
        
        # Look for bullet points, numbered items, or key phrases
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '*', '1.', '2.', '3.')) or 'finding' in line.lower():
                if len(line) > 10:  # Avoid very short lines
                    # Don't truncate - use full line, but limit total findings
                    key_findings.append(line)
        
        # Filter out incomplete findings (those that end with common incomplete patterns)
        complete_findings = []
        for finding in key_findings:
            # Skip if it's just a header or incomplete sentence
            if (not finding.endswith((':', 'which are', 'that', 'and', 'or', 'but', 'with')) and 
                len(finding.split()) > 3 and
                not finding.lower().strip() in ['key findings:', '3) key findings:']):
                complete_findings.append(finding)
        
        return complete_findings[:MAX_KEY_FINDINGS]  # Use configured limit
    
    def _extract_confidence_from_text(self, text: str) -> float:
        """Extract confidence level from AI response"""
        text_lower = text.lower()
        
        # Look for confidence indicators
        if 'high confidence' in text_lower or 'very confident' in text_lower:
            return 0.9
        elif 'medium confidence' in text_lower or 'moderately confident' in text_lower:
            return 0.7
        elif 'low confidence' in text_lower or 'uncertain' in text_lower:
            return 0.3
        else:
            return 0.5  # Default confidence
    
    def _extract_sentiment_from_text(self, text: str) -> float:
        """Extract sentiment from AI response"""
        text_lower = text.lower()
        
        # Look for sentiment indicators
        negative_words = ['negative', 'concern', 'risk', 'problem', 'issue', 'violation']
        positive_words = ['positive', 'clean', 'compliant', 'good', 'clear']
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count:
            return -0.5
        elif positive_count > negative_count:
            return 0.5
        else:
            return 0.0
    
    def _create_fallback_summary(self, search_results: List[Dict], entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback summary using rule-based analysis"""
        entity_name = entity_data.get('name', 'Unknown')
        risk_indicators = []
        key_findings = []
        sources_cited = []
        
        # Enhanced risk keywords mapping
        risk_keywords_map = {
            'sanctions': ['sanctions', 'ofac', 'sdn list', 'embargo', 'asset freeze'],
            'criminal': ['criminal', 'fraud', 'embezzlement', 'money laundering', 'arrest', 'charge'],
            'investigation': ['investigation', 'probe', 'inquiry', 'under investigation'],
            'regulatory': ['regulatory violation', 'compliance violation', 'penalty', 'fine', 'settlement'],
            'pep': ['politically exposed', 'pep', 'government official', 'political figure'],
            'corruption': ['corruption', 'bribery', 'kickback', 'corrupt practices'],
            'terrorism': ['terrorism', 'terrorist', 'terror financing']
        }
        
        # Analyze results for risk indicators
        for result in search_results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            source = result.get('source', '')
            
            if source:
                sources_cited.append(source)
            
            for category, keywords in risk_keywords_map.items():
                if any(keyword in text for keyword in keywords):
                    indicator = f"{category.title()} related activity"
                    if indicator not in risk_indicators:
                        risk_indicators.append(indicator)
                    key_findings.append(f"Found {category} related information in {source}")
        
        # Generate summary
        if risk_indicators:
            summary = f"Analysis of {entity_name} indicates the following risk factors: " + ", ".join(risk_indicators[:3])
        else:
            summary = f"No significant risk indicators found for {entity_name} based on available information."
        
        # Calculate confidence based on number of sources
        confidence = min(0.8, len(search_results) * 0.1) if search_results else 0.1
        
        # Calculate sentiment
        sentiment = self._calculate_sentiment_from_results(search_results)
        
        return {
            'summary': summary,
            'risk_indicators': risk_indicators[:MAX_RISK_INDICATORS],
            'sentiment': sentiment,
            'confidence': confidence,
            'key_findings': key_findings[:MAX_KEY_FINDINGS],
            'sources_cited': list(set(sources_cited))[:MAX_RISK_INDICATORS],
            'ai_provider': 'Rule-based Analysis'
        }
    
    def _calculate_sentiment_from_results(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate sentiment from search results"""
        if not search_results:
            return 0.0
        
        negative_keywords = ['sanctions', 'investigation', 'criminal', 'fraud', 'violation', 'penalty']
        positive_keywords = ['compliant', 'cleared', 'exonerated', 'approved', 'legitimate']
        
        negative_count = 0
        positive_count = 0
        
        for result in search_results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            
            for keyword in negative_keywords:
                if keyword in text:
                    negative_count += 1
            
            for keyword in positive_keywords:
                if keyword in text:
                    positive_count += 1
        
        total = negative_count + positive_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total 