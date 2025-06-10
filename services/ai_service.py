import logging
import os
import requests
from typing import Dict, Any, List
import json
import config  # Import config module

logger = logging.getLogger(__name__)

class AIService:
    """Real AI service for risk analysis and summarization"""
    
    def __init__(self):
        self.openai_api_key = config.OPENAI_API_KEY
        self.deepseek_api_key = config.DEEPSEEK_API_KEY
        self.fast_mode = True  # Enable fast mode by default
        
        # Debug logging for API keys
        logger.info(f"AIService initialized with OpenAI API key: {'Present' if self.openai_api_key else 'None'}")
        logger.info(f"AIService initialized with DeepSeek API key: {'Present' if self.deepseek_api_key else 'None'}")
        
        logger.info("AI service initialized with real API keys")
    
    def summarize_search_results(self, search_results: List[Dict], entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize search results using real AI APIs"""
        if not search_results:
            # Try to use AI even with no results
            if self.deepseek_api_key:
                return {
                    'summary': 'No search results available for analysis.',
                    'risk_score': 0,
                    'sentiment': 'neutral',
                    'confidence': 0.1,
                    'risk_indicators': [],
                    'ai_provider': 'DeepSeek'
                }
            elif self.openai_api_key:
                return {
                    'summary': 'No search results available for analysis.',
                    'risk_score': 0,
                    'sentiment': 'neutral',
                    'confidence': 0.1,
                    'risk_indicators': [],
                    'ai_provider': 'OpenAI'
                }
            else:
                return {
                    'summary': 'No search results available for analysis.',
                    'risk_score': 0,
                    'sentiment': 'neutral',
                    'confidence': 0.1,
                    'risk_indicators': [],
                    'ai_provider': 'Fallback Analysis'
                }
        
        # OPTIMIZATION: Limit results in fast mode for quicker processing
        if self.fast_mode:
            limited_results = search_results[:10]  # Top 10 results only
            logger.info(f"Fast mode: Processing {len(limited_results)} of {len(search_results)} search results")
        else:
            limited_results = search_results[:15]  # Top 15 results
        
        content = self._prepare_content_for_analysis(limited_results, entity_data)
        
        # Try OpenAI first, then DeepSeek as fallback
        result = None
        
        if self.openai_api_key:
            result = self._summarize_with_openai(content, entity_data)
            if result:
                result['ai_provider'] = 'OpenAI'
        
        if not result and self.deepseek_api_key:
            result = self._summarize_with_deepseek(content, entity_data)
            if result:
                result['ai_provider'] = 'DeepSeek'
        
        # Fallback to rule-based analysis
        if not result:
            result = self._create_fallback_summary(limited_results, entity_data)
            result['ai_provider'] = 'Fallback Analysis'
        
        # Ensure all required fields are present
        result = self._ensure_complete_response(result)
        
        return result

    def _prepare_content_for_analysis(self, search_results: List[Dict], entity_data: Dict[str, Any]) -> str:
        """Prepare search results content for AI analysis with optimizations"""
        entity_name = entity_data.get('name', 'Unknown')
        entity_company = entity_data.get('company', '')
        
        # OPTIMIZATION: Shorter content preparation in fast mode
        if self.fast_mode:
            content_parts = [
                f"RISK ANALYSIS: {entity_name}",
                f"Company: {entity_company}" if entity_company else "",
                "",
                "KEY SEARCH RESULTS:",
                ""
            ]
            
            # Limit to top 8 results and shorter snippets in fast mode
            for i, result in enumerate(search_results[:8], 1):
                source = result.get('source', 'Unknown')
                title = result.get('title', 'No title')
                snippet = result.get('snippet', 'No content')[:150]  # Shorter snippets
                
                content_parts.extend([
                    f"[{i}] {source}: {title}",
                    f"Content: {snippet}...",
                    ""
                ])
        else:
            # Full mode: comprehensive content
            content_parts = [
                f"RISK INTELLIGENCE ANALYSIS REQUEST",
                f"Entity: {entity_name}",
                f"Company: {entity_company}" if entity_company else "",
                f"Country: {entity_data.get('country', 'Unknown')}",
                "",
                "SEARCH RESULTS FROM MAJOR NEWS SOURCES:",
                ""
            ]
            
            for i, result in enumerate(search_results[:15], 1):
                source = result.get('source', 'Unknown')
                title = result.get('title', 'No title')
                snippet = result.get('snippet', 'No content')
                
                content_parts.extend([
                    f"[{i}] Source: {source}",
                    f"Title: {title}",
                    f"Content: {snippet}",
                    f"URL: {result.get('link', result.get('url', 'N/A'))}",
                    ""
                ])
        
        return "\n".join(content_parts)
    
    def _summarize_with_openai(self, content: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize using OpenAI GPT with optimizations"""
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            entity_name = entity_data.get('name', 'the entity')
            
            # OPTIMIZATION: Use different prompts and token limits based on mode
            if self.fast_mode:
                system_prompt = "You are a risk analyst. Analyze search results for sanctions, criminal activity, and regulatory violations. Provide concise structured analysis."
                
                user_prompt = f"""Quick risk analysis for {entity_name}:

{content}

JSON response:
{{
    "summary": "Brief risk assessment (max 150 words)",
    "risk_indicators": ["risk 1", "risk 2"],
    "sentiment": "positive|negative|neutral",
    "confidence": 0.85,
    "risk_score": 65,
    "key_findings": ["finding 1", "finding 2"]
}}"""
                max_tokens = 500  # Reduced tokens for faster response
            else:
                # Full mode: comprehensive analysis
                system_prompt = """You are an expert risk intelligence analyst specializing in financial crime, sanctions, and regulatory compliance. 

Analyze the provided search results and create a comprehensive risk assessment. Focus on:

1. SANCTIONS: Any mention of economic sanctions, asset freezes, or designated persons lists
2. CRIMINAL ACTIVITY: Arrests, charges, convictions, investigations, fraud, money laundering
3. REGULATORY ACTIONS: SEC investigations, banking violations, compliance issues, fines
4. POLITICAL EXPOSURE: Government positions, politically exposed persons (PEP), political connections
5. REPUTATIONAL RISKS: Scandals, controversies, negative media coverage
6. BUSINESS RISKS: Corporate malfeasance, bankruptcy, regulatory violations

Provide a structured analysis with specific evidence from the search results."""

                user_prompt = f"""Analyze the following information about {entity_name} and provide a comprehensive risk assessment:

{content}

Respond in JSON format with:
{{
    "summary": "Detailed risk assessment summary (max 300 words)",
    "risk_indicators": ["specific risk factor 1", "specific risk factor 2", ...],
    "sentiment": "positive|negative|neutral",
    "confidence": 0.85,
    "risk_score": 75,
    "key_findings": ["finding 1", "finding 2", ...],
    "sources_cited": ["source 1", "source 2", ...]
}}"""
                max_tokens = 800  # Full tokens for comprehensive analysis

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            content_response = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(content_response)
                return self._validate_ai_response(result)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response from text
                return self._parse_text_response(content_response, entity_data)
                
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {str(e)}")
            return None
    
    def _summarize_with_deepseek(self, content: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize using DeepSeek API with optimizations"""
        try:
            entity_name = entity_data.get('name', 'the entity')
            
            url = "https://api.deepseek.com/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            # OPTIMIZATION: Adjust tokens and prompt based on mode
            if self.fast_mode:
                max_tokens = 500
                prompt = f"""Quick risk analysis for {entity_name}:

{content}

JSON format:
{{
    "summary": "Brief risk assessment",
    "risk_indicators": ["risk factors"],
    "sentiment": "positive|negative|neutral",
    "confidence": 0.8,
    "risk_score": 65,
    "key_findings": ["findings"]
}}"""
            else:
                max_tokens = 800
                prompt = f"""Analyze this information about {entity_name} for comprehensive risk assessment:

{content}

Provide analysis in JSON format:
{{
    "summary": "Detailed risk assessment summary",
    "risk_indicators": ["specific risk factors found"],
    "sentiment": "positive|negative|neutral",
    "confidence": 0.8,
    "risk_score": 65,
    "key_findings": ["important findings"],
    "sources_cited": ["sources mentioned"]
}}"""
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert risk intelligence analyst. Analyze search results for sanctions, criminal activity, regulatory violations, and other risk factors. Provide detailed, structured assessments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
            
            # OPTIMIZATION: Shorter timeout in fast mode
            timeout = 20 if self.fast_mode else 30
            
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            content_response = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Try to parse JSON response
            try:
                result = json.loads(content_response)
                return self._validate_ai_response(result)
            except json.JSONDecodeError:
                return self._parse_text_response(content_response, entity_data)
                
        except Exception as e:
            logger.error(f"DeepSeek summarization failed: {str(e)}")
            return None

    def set_fast_mode(self, enabled: bool):
        """Enable or disable fast mode for AI processing"""
        self.fast_mode = enabled
        logger.info(f"AI service fast mode {'enabled' if enabled else 'disabled'}")

    def _validate_ai_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize AI response"""
        # Ensure required fields exist
        validated = {
            'summary': result.get('summary', 'Analysis completed'),
            'risk_indicators': result.get('risk_indicators', []),
            'sentiment': result.get('sentiment', 'neutral'),
            'confidence': min(max(result.get('confidence', 0.5), 0.0), 1.0),
            'risk_score': min(max(result.get('risk_score', 0), 0), 100),
            'key_findings': result.get('key_findings', []),
            'sources_cited': result.get('sources_cited', [])
        }
        
        # Validate sentiment
        if validated['sentiment'] not in ['positive', 'negative', 'neutral']:
            validated['sentiment'] = 'neutral'
        
        return validated
    
    def _parse_text_response(self, text_response: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        risk_indicators = []
        sentiment = 'neutral'
        
        text_lower = text_response.lower()
        
        # Extract risk indicators using keyword matching
        risk_keywords = {
            'sanctions': ['sanction', 'ofac', 'sdn', 'embargo'],
            'criminal': ['criminal', 'fraud', 'embezzlement', 'money laundering'],
            'investigation': ['investigation', 'probe', 'inquiry'],
            'regulatory': ['regulatory', 'violation', 'penalty', 'fine'],
            'pep': ['politically exposed', 'pep', 'government official'],
            'corruption': ['corruption', 'bribery', 'kickback']
        }
        
        for category, keywords in risk_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    risk_indicators.append(f"{category.title()} related: {keyword}")
        
        # Determine sentiment
        negative_indicators = ['sanction', 'criminal', 'fraud', 'investigation', 'violation']
        positive_indicators = ['cleared', 'compliant', 'ethical', 'legitimate']
        
        negative_count = sum(1 for indicator in negative_indicators if indicator in text_lower)
        positive_count = sum(1 for indicator in positive_indicators if indicator in text_lower)
        
        if negative_count > positive_count:
            sentiment = 'negative'
        elif positive_count > negative_count:
            sentiment = 'positive'
        
        return {
            'summary': text_response[:200] + '...' if len(text_response) > 200 else text_response,
            'risk_indicators': list(set(risk_indicators)),  # Remove duplicates
            'sentiment': sentiment,
            'confidence': min(0.7, len(risk_indicators) * 0.1 + 0.3)
        }
    
    def _create_fallback_summary(self, search_results: List[Dict], entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback summary using rule-based analysis"""
        entity_name = entity_data.get('name', 'Unknown')
        risk_indicators = []
        negative_results = 0
        total_results = len(search_results)
        
        # Analyze search results for risk keywords
        risk_keywords = [
            'sanctions', 'criminal', 'fraud', 'investigation', 'corruption',
            'money laundering', 'violation', 'penalty', 'regulatory action',
            'pep', 'politically exposed'
        ]
        
        for result in search_results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            content = f"{title} {snippet}"
            
            for keyword in risk_keywords:
                if keyword in content:
                    risk_indicators.append(f"Found '{keyword}' in search results")
                    negative_results += 1
                    break
        
        # Generate summary
        if risk_indicators:
            summary = f"Analysis of {entity_name} found {len(risk_indicators)} potential risk indicators in search results. "
            summary += f"Key concerns include: {', '.join(risk_indicators[:3])}."
            sentiment = 'negative'
        else:
            summary = f"Analysis of {entity_name} did not identify significant risk indicators in available search results."
            sentiment = 'neutral'
        
        confidence = min(0.6, (total_results * 0.1))
        
        return {
            'summary': summary,
            'risk_indicators': list(set(risk_indicators)),
            'sentiment': sentiment,
            'confidence': confidence
        }
    
    def analyze_entity_connections(self, entity_data: Dict[str, Any], connections: List[Dict]) -> Dict[str, Any]:
        """Analyze entity connections for risk assessment"""
        if not connections:
            return {
                'analysis': 'No connections available for analysis.',
                'risk_score': 0,
                'high_risk_connections': []
            }
        
        high_risk_connections = []
        risk_score = 0
        
        for connection in connections:
            connection_risk = connection.get('risk_level', 'LOW')
            if connection_risk == 'HIGH':
                high_risk_connections.append(connection)
                risk_score += 30
            elif connection_risk == 'MEDIUM':
                risk_score += 10
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        if high_risk_connections:
            analysis = f"Entity has {len(high_risk_connections)} high-risk connections. "
            analysis += "This significantly increases the overall risk profile."
        else:
            analysis = "No high-risk connections identified in the network analysis."
        
        return {
            'analysis': analysis,
            'risk_score': risk_score,
            'high_risk_connections': high_risk_connections[:5],  # Limit to top 5
            'total_connections': len(connections)
        }
    
    def _ensure_complete_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure the response has all required fields"""
        complete_result = {
            'summary': result.get('summary', 'Risk analysis completed'),
            'risk_indicators': result.get('risk_indicators', []),
            'sentiment': result.get('sentiment', 'neutral'),
            'confidence': result.get('confidence', 0.5),
            'risk_score': result.get('risk_score', 0),
            'key_findings': result.get('key_findings', []),
            'sources_cited': result.get('sources_cited', []),
            'ai_provider': result.get('ai_provider', 'Unknown'),
            'detailed_analysis': {
                'risk_categories': self._categorize_risks(result.get('risk_indicators', [])),
                'confidence_factors': self._calculate_confidence_factors(result),
                'recommendations': self._generate_recommendations(result)
            }
        }
        
        # Ensure sentiment is valid
        if complete_result['sentiment'] not in ['positive', 'negative', 'neutral']:
            complete_result['sentiment'] = 'neutral'
        
        # Ensure confidence is in valid range
        complete_result['confidence'] = min(max(complete_result['confidence'], 0.0), 1.0)
        
        # Ensure risk score is in valid range
        complete_result['risk_score'] = min(max(complete_result['risk_score'], 0), 100)
        
        return complete_result

    def _categorize_risks(self, risk_indicators: List[str]) -> Dict[str, List[str]]:
        """Categorize risk indicators into different risk types"""
        categories = {
            'financial': [],
            'legal': [],
            'reputational': [],
            'compliance': [],
            'other': []
        }
        
        for indicator in risk_indicators:
            indicator_lower = indicator.lower()
            if any(word in indicator_lower for word in ['fraud', 'money', 'laundering', 'financial']):
                categories['financial'].append(indicator)
            elif any(word in indicator_lower for word in ['criminal', 'legal', 'sanction']):
                categories['legal'].append(indicator)
            elif any(word in indicator_lower for word in ['reputation', 'negative', 'sentiment']):
                categories['reputational'].append(indicator)
            elif any(word in indicator_lower for word in ['compliance', 'regulation', 'pep']):
                categories['compliance'].append(indicator)
            else:
                categories['other'].append(indicator)
        
        return categories

    def _calculate_confidence_factors(self, result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence factors for different aspects of the analysis"""
        return {
            'data_quality': min(1.0, len(result.get('sources_cited', [])) * 0.2),
            'risk_consistency': min(1.0, len(result.get('risk_indicators', [])) * 0.1),
            'source_reliability': min(1.0, sum(1 for s in result.get('sources_cited', []) 
                                             if any(domain in s.lower() for domain in 
                                                  ['.gov', '.org', 'reuters', 'bloomberg'])) * 0.2)
        }

    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on risk assessment"""
        recommendations = []
        risk_level = result.get('risk_level', 'low')
        risk_indicators = result.get('risk_indicators', [])
        
        if risk_level in ['high', 'very_high']:
            recommendations.append("Immediate enhanced due diligence recommended")
            recommendations.append("Consider additional verification of identity and background")
        
        if any('fraud' in indicator.lower() for indicator in risk_indicators):
            recommendations.append("Conduct detailed financial transaction analysis")
        
        if any('pep' in indicator.lower() for indicator in risk_indicators):
            recommendations.append("Implement enhanced monitoring procedures")
        
        if len(risk_indicators) > 3:
            recommendations.append("Regular risk reassessment recommended")
        
        return recommendations 