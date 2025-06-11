import logging
import os
from typing import Dict, Any, List
import time
from models.crime_models import CRIME_DOMAINS, CRIME_STAGES, CrimeDomain, CrimeStage

logger = logging.getLogger(__name__)

class RiskCalculator:
    """Enhanced risk calculator for flexible person/company data structures"""
    
    def __init__(self):
        logger.info("Risk calculator initialized (simplified mode)")
        self.risk_weights = {
            'sanctions': 0.35,      # High weight for sanctions matches
            'web_intelligence': 0.35,  # Increased weight for web findings
            'graph_connections': 0.2,  # Medium weight for graph analysis
            'ai_assessment': 0.1     # Lower weight for AI analysis
        }
        
        # Risk level thresholds
        self.risk_thresholds = {
            'very_low': 0.0,
            'low': 0.3,      # Increased from 0.2
            'medium': 0.5,   # Increased from 0.4
            'high': 0.7,
            'very_high': 0.9
        }
        
        # Priority weights for crime domains
        self.priority_weights = {
            'P0': 1.0,  # Highest priority
            'P1': 0.8,  # High priority
            'P2': 0.6,  # Medium priority
            'P3': 0.4   # Low priority
        }
        
        # Stage weights for crime stages
        self.stage_weights = {
            'Stage 1': 0.4,  # Early stage
            'Stage 2': 0.6,  # Investigation stage
            'Stage 3': 0.8,  # Resolution stage
            'Stage 4': 1.0   # Final stage
        }
    
    def calculate_risk(self, sanctions_result: Dict[str, Any], web_intelligence: Dict[str, Any], 
                       graph_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Original risk calculation method for backward compatibility"""
        # Convert single entity results to multi-entity format
        sanctions_results = {'entity': sanctions_result}
        web_intelligence_results = {'entity': web_intelligence}
        graph_analysis_results = {'entity': graph_analysis}
        
        return self.calculate_comprehensive_risk(
            sanctions_results, web_intelligence_results, graph_analysis_results, 'legacy'
        )
    
    def calculate_comprehensive_risk(self, sanctions_results: Dict[str, Any], 
                                   web_intelligence_results: Dict[str, Any],
                                   graph_analysis_results: Dict[str, Any],
                                   input_type: str) -> Dict[str, Any]:
        """Comprehensive risk calculation for flexible person/company inputs"""
        try:
            logger.info(f"Calculating comprehensive risk for {input_type} assessment")
            
            # Calculate individual risk components
            sanctions_score = self._calculate_sanctions_risk(sanctions_results)
            web_intel_score = self._calculate_web_intelligence_risk(web_intelligence_results)
            graph_score = self._calculate_graph_risk(graph_analysis_results)
            ai_score = 0.5  # Placeholder for AI assessment
            
            # Calculate weighted overall risk score
            overall_risk = (
                sanctions_score * self.risk_weights['sanctions'] +
                web_intel_score * self.risk_weights['web_intelligence'] +
                graph_score * self.risk_weights['graph_connections'] +
                ai_score * self.risk_weights['ai_assessment']
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk)
            
            # Compile risk factors
            risk_factors = self._compile_risk_factors(
                sanctions_results, web_intelligence_results, 
                graph_analysis_results, input_type
            )
            
            return {
                'risk_score': round(overall_risk, 3),
                'risk_level': risk_level,
                'component_scores': {
                    'sanctions': round(sanctions_score, 3),
                    'web_intelligence': round(web_intel_score, 3),
                    'graph_connections': round(graph_score, 3),
                    'ai_assessment': round(ai_score, 3)
                },
                'weights_applied': self.risk_weights,
                'risk_factors': risk_factors,
                'assessment_type': input_type,
                'entities_analyzed': list(sanctions_results.keys())
            }
            
        except Exception as e:
            logger.error(f"Risk calculation failed: {str(e)}")
            return {
                'risk_score': 0.5,
                'risk_level': 'medium',
                'component_scores': {
                    'sanctions': 0.0,
                    'web_intelligence': 0.0,
                    'graph_connections': 0.0,
                    'ai_assessment': 0.0
                },
                'risk_factors': ['Risk calculation error'],
                'error': str(e)
            }
    
    def _calculate_sanctions_risk(self, sanctions_results: Dict[str, Any]) -> float:
        """Calculate risk score based on sanctions matches"""
        if not sanctions_results:
            return 0.0
        
        max_risk = 0.0
        total_matches = 0
        
        for entity_key, result in sanctions_results.items():
            if not result.get('matched', False):
                continue
                
            matches = result.get('matches', [])
            total_matches += len(matches)
            
            for match in matches:
                confidence = match.get('confidence', 0) / 100.0
                
                # Risk scoring based on sanctions type and confidence
                base_risk = confidence
                
                # Enhance risk based on sanctions topic and crime domain
                topics = match.get('topics', [])
                for domain in CRIME_DOMAINS:
                    if domain.name.lower() in ' '.join(topics).lower():
                        base_risk *= (1.0 + self.priority_weights.get(domain.priority, 0.5))
                        break
                
                # Enhance risk based on crime stage
                for stage in CRIME_STAGES:
                    if stage.name.lower() in ' '.join(topics).lower():
                        base_risk *= (1.0 + self.stage_weights.get(stage.stage, 0.5))
                        break
                
                max_risk = max(max_risk, min(base_risk, 1.0))
        
        # Boost risk if multiple matches
        if total_matches > 1:
            max_risk = min(max_risk * 1.1, 1.0)
        
        return max_risk
    
    def _calculate_web_intelligence_risk(self, web_intelligence_results: Dict[str, Any]) -> float:
        """Calculate risk score based on web intelligence"""
        if not web_intelligence_results:
            return 0.0
        
        total_risk_indicators = 0
        sentiment_scores = []
        
        for entity_key, result in web_intelligence_results.items():
            risk_indicators = result.get('risk_indicators', [])
            total_risk_indicators += len(risk_indicators)
            
            # Check risk indicators against crime domains
            for indicator in risk_indicators:
                for domain in CRIME_DOMAINS:
                    if domain.name.lower() in indicator.lower():
                        total_risk_indicators += self.priority_weights.get(domain.priority, 0.5)
                        break
            
            sentiment = result.get('sentiment_score', 0)
            if sentiment != 0:
                sentiment_scores.append(sentiment)
        
        # Base risk from number of risk indicators
        indicator_risk = min(total_risk_indicators * 0.1, 0.7)
        
        # Sentiment risk (negative sentiment increases risk)
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            # Convert sentiment to risk (negative sentiment = higher risk)
            sentiment_risk = max(0, (0 - avg_sentiment) * 0.3)
        else:
            sentiment_risk = 0.0
        
        return min(indicator_risk + sentiment_risk, 1.0)
    
    def _calculate_graph_risk(self, graph_analysis_results: Dict[str, Any]) -> float:
        """Calculate risk score based on graph connections"""
        if not graph_analysis_results:
            return 0.0
        
        total_connections = 0
        total_risk_connections = 0
        
        for entity_id, analysis in graph_analysis_results.items():
            total_connections += analysis.get('connection_count', 0)
            total_risk_connections += analysis.get('risk_connections', 0)
        
        if total_connections == 0:
            return 0.0
        
        # Risk based on proportion of risky connections
        risk_ratio = total_risk_connections / total_connections
        
        # Scale based on total connections (more connections = potentially higher risk)
        connection_factor = min(total_connections * 0.02, 0.3)
        
        return min(risk_ratio * 0.7 + connection_factor, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score >= self.risk_thresholds['very_high']:
            return 'very_high'
        elif risk_score >= self.risk_thresholds['high']:
            return 'high'
        elif risk_score >= self.risk_thresholds['medium']:
            return 'medium'
        elif risk_score >= self.risk_thresholds['low']:
            return 'low'
        else:
            return 'very_low'
    
    def _compile_risk_factors(self, sanctions_results: Dict[str, Any],
                            web_intelligence_results: Dict[str, Any],
                            graph_analysis_results: Dict[str, Any],
                            input_type: str) -> List[str]:
        """Compile detailed risk factors"""
        factors = []
        
        # Sanctions factors
        for entity_key, result in sanctions_results.items():
            if result.get('matched', False):
                matches = result.get('matches', [])
                factors.append(f"Found {len(matches)} sanctions matches for {entity_key}")
                
                for match in matches[:3]:  # Top 3 matches
                    confidence = match.get('confidence', 0)
                    topics = match.get('topics', [])
                    
                    # Match topics with crime domains
                    matched_domains = []
                    for domain in CRIME_DOMAINS:
                        if domain.name.lower() in ' '.join(topics).lower():
                            matched_domains.append(f"{domain.name} ({domain.priority})")
                    
                    # Match topics with crime stages
                    matched_stages = []
                    for stage in CRIME_STAGES:
                        if stage.name.lower() in ' '.join(topics).lower():
                            matched_stages.append(f"{stage.name} ({stage.stage})")
                    
                    factors.append(f"Sanctions match: {confidence}% confidence")
                    if matched_domains:
                        factors.append(f"Matched crime domains: {', '.join(matched_domains)}")
                    if matched_stages:
                        factors.append(f"Matched crime stages: {', '.join(matched_stages)}")
        
        # Web intelligence factors
        for entity_key, result in web_intelligence_results.items():
            risk_indicators = result.get('risk_indicators', [])
            if risk_indicators:
                # Match indicators with crime domains
                matched_domains = []
                for indicator in risk_indicators:
                    for domain in CRIME_DOMAINS:
                        if domain.name.lower() in indicator.lower():
                            matched_domains.append(f"{domain.name} ({domain.priority})")
                            break
                
                if matched_domains:
                    factors.append(f"Web risk indicators for {entity_key}: {', '.join(matched_domains)}")
                else:
                    factors.append(f"Web risk indicators for {entity_key}: {', '.join(risk_indicators[:3])}")
            
            sentiment = result.get('sentiment_score', 0)
            if sentiment < -0.3:
                factors.append(f"Negative sentiment detected for {entity_key}: {sentiment}")
        
        # Graph factors
        total_risk_connections = sum(
            analysis.get('risk_connections', 0) 
            for analysis in graph_analysis_results.values()
        )
        if total_risk_connections > 0:
            factors.append(f"Found {total_risk_connections} risky entity connections")
        
        # Input type specific factors
        if input_type == 'person_and_company':
            factors.append("Comprehensive person-company relationship analysis performed")
        elif input_type == 'company_only':
            factors.append("Corporate entity risk assessment")
        elif input_type == 'person_only':
            factors.append("Individual person risk assessment")
        
        if not factors:
            factors.append("No significant risk indicators found")
        
        return factors

    def get_risk_distribution_stats(self, scores: List[float]) -> Dict[str, Any]:
        """Calculate statistics for a list of risk scores"""
        if not scores:
            return {
                'count': 0,
                'average': 0.0,
                'median': 0.0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0
            }
        
        scores_sorted = sorted(scores)
        count = len(scores)
        
        # Calculate percentiles
        def percentile(data, p):
            index = (p / 100) * (len(data) - 1)
            lower = int(index)
            upper = min(lower + 1, len(data) - 1)
            weight = index - lower
            return data[lower] * (1 - weight) + data[upper] * weight
        
        # Count risk levels
        high_risk_count = sum(1 for s in scores if s >= self.high_risk_threshold)
        medium_risk_count = sum(1 for s in scores 
                              if self.medium_risk_threshold <= s < self.high_risk_threshold)
        low_risk_count = count - high_risk_count - medium_risk_count
        
        return {
            'count': count,
            'average': sum(scores) / count,
            'median': percentile(scores_sorted, 50),
            'p25': percentile(scores_sorted, 25),
            'p75': percentile(scores_sorted, 75),
            'p90': percentile(scores_sorted, 90),
            'min': min(scores),
            'max': max(scores),
            'high_risk_count': high_risk_count,
            'medium_risk_count': medium_risk_count,
            'low_risk_count': low_risk_count,
            'high_risk_percentage': (high_risk_count / count) * 100,
            'medium_risk_percentage': (medium_risk_count / count) * 100,
            'low_risk_percentage': (low_risk_count / count) * 100
        } 