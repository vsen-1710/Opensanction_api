import logging
import requests
from typing import Dict, List, Any, Optional
from fuzzywuzzy import fuzz
import json
import time
import os

logger = logging.getLogger(__name__)

class OpenSanctionsService:
    """OpenSanctions service with real API integration"""

    def __init__(self):
        # Try to use real OpenSanctions data first
        self.api_base_url = "https://api.opensanctions.org"
        self.sanctions_data = []
        self.data_loaded = False
        self._load_sanctions_data()

    def _load_sanctions_data(self):
        """Load sanctions data from OpenSanctions API or fallback to empty dataset"""
        logger.info("Initializing OpenSanctions service...")
        
        try:
            logger.info("Attempting to load real OpenSanctions dataset...")
            
            # Try to load a subset of real OpenSanctions data for testing
            # Use a smaller endpoint for faster loading
            test_url = f"{self.api_base_url}/search/default"
            
            headers = {
                'User-Agent': 'RiskAssessmentAPI/1.0',
                'Accept': 'application/json'
            }
            
            # Test connection first
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("Successfully connected to OpenSanctions API")
                # Initialize with empty dataset - real data will be fetched per request
                self.sanctions_data = []
                self.data_loaded = True
                logger.info("OpenSanctions service initialized with real API access")
                return
            else:
                logger.warning(f"OpenSanctions API returned status {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Failed to connect to real OpenSanctions API: {str(e)}")
        
        # Fallback to empty dataset
        logger.info("Using empty dataset - will perform live API searches")
        self.sanctions_data = []
        self.data_loaded = True
        logger.info("OpenSanctions service initialized with empty local dataset")

    def _search_opensanctions_api(self, entity_name: str, entity_type: str = "Person") -> List[Dict]:
        """Search OpenSanctions API for real-time results"""
        try:
            search_url = f"{self.api_base_url}/search/default"
            params = {
                'q': entity_name,
                'limit': 10,
                'fuzzy': 'true'
            }
            
            headers = {
                'User-Agent': 'RiskAssessmentAPI/1.0',
                'Accept': 'application/json'
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                logger.info(f"Found {len(results)} results from OpenSanctions API for '{entity_name}'")
                return results
            else:
                logger.warning(f"OpenSanctions API search failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching OpenSanctions API: {str(e)}")
            return []

    def _is_relevant_entity(self, entity: Dict) -> bool:
        """Check if entity is relevant for sanctions checking"""
        props = entity.get('properties', {})
        return bool(props.get('name'))
    
    def check_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check entity against sanctions list"""
        if not self.data_loaded:
            return {
                'matches': [],
                'total_matches': 0,
                'risk_score': 0,
                'status': 'data_not_loaded'
            }
        
        entity_name = entity_data.get('name', '').strip()
        if not entity_name:
            return {
                'matches': [],
                'total_matches': 0,
                'risk_score': 0,
                'status': 'no_name_provided'
            }
        
        # Try real-time API search first
        api_results = self._search_opensanctions_api(entity_name)
        
        matches = []
        
        # Process API results
        for result in api_results:
            match = self._process_api_result(entity_name, result, entity_data)
            if match:
                matches.append(match)
        
        # If no API results, search local data (if any)
        if not matches and self.sanctions_data:
            for sanctions_entity in self.sanctions_data:
                match = self._check_name_match(entity_name.lower(), sanctions_entity, entity_data)
                if match:
                    matches.append(match)
        
        # Sort by confidence score
        matches.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(matches)
        
        # Determine risk level
        risk_level = self._determine_overall_risk_level(matches, risk_score)
        
        return {
            'matches': matches[:5],  # Top 5 matches
            'total_matches': len(matches),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'status': 'checked',
            'highest_confidence': matches[0].get('confidence', 0) if matches else 0,
            'matched': len(matches) > 0,
            'sanctions_types': list(set(match.get('sanctions_type') for match in matches if match.get('sanctions_type'))),
            'risk_factors': self._extract_risk_factors(matches),
            'search_method': 'api' if api_results else 'local'
        }

    def _process_api_result(self, search_name: str, api_result: Dict, entity_data: Dict) -> Optional[Dict[str, Any]]:
        """Process API result and convert to match format"""
        try:
            properties = api_result.get('properties', {})
            result_names = properties.get('name', [])
            
            if not result_names:
                return None
            
            # Find best name match
            best_confidence = 0
            best_name = ""
            
            for name in result_names:
                if isinstance(name, str):
                    confidence = fuzz.ratio(search_name.lower(), name.lower())
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_name = name
            
            # Only consider matches above threshold
            if best_confidence < 70:
                return None
            
            # Extract topics/datasets for risk assessment
            topics = properties.get('topics', [])
            datasets = api_result.get('datasets', [])
            
            return {
                'id': api_result.get('id', 'unknown'),
                'name': best_name,
                'matched_name': search_name,
                'confidence': best_confidence,
                'country': properties.get('country', ['Unknown'])[0] if properties.get('country') else 'Unknown',
                'birth_date': properties.get('birthDate', ['Unknown'])[0] if properties.get('birthDate') else 'Unknown',
                'topics': topics,
                'datasets': datasets,
                'sanctions_type': self._determine_sanctions_type(topics + datasets),
                'risk_level': self._determine_risk_level(best_confidence, topics + datasets),
                'aliases': properties.get('alias', []),
                'identifiers': properties.get('idNumber', []),
                'addresses': properties.get('address', []),
                'nationalities': properties.get('nationality', []),
                'programs': properties.get('program', []),
                'source': 'opensanctions_api'
            }
            
        except Exception as e:
            logger.error(f"Error processing API result: {str(e)}")
            return None
    
    def _check_name_match(self, search_name: str, sanctions_entity: Dict, entity_data: Dict) -> Optional[Dict[str, Any]]:
        """Check if names match with fuzzy matching"""
        props = sanctions_entity.get('properties', {})
        sanctions_names = props.get('name', [])
        
        best_match = None
        highest_confidence = 0
        
        for sanctions_name in sanctions_names:
            if isinstance(sanctions_name, str):
                sanctions_name_lower = sanctions_name.lower().strip()
                
                # Exact match
                if search_name == sanctions_name_lower:
                    confidence = 100
                # Fuzzy match
                else:
                    confidence = fuzz.ratio(search_name, sanctions_name_lower)
                
                # Consider a match if confidence > 70
                if confidence > 70 and confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = {
                        'id': sanctions_entity.get('id', 'unknown'),
                        'name': sanctions_name,
                        'matched_name': search_name,
                        'confidence': confidence,
                        'country': props.get('country', ['Unknown'])[0] if props.get('country') else 'Unknown',
                        'birth_date': props.get('birthDate', ['Unknown'])[0] if props.get('birthDate') else 'Unknown',
                        'topics': props.get('topics', []),
                        'sanctions_type': self._determine_sanctions_type(props.get('topics', [])),
                        'risk_level': self._determine_risk_level(confidence, props.get('topics', [])),
                        'aliases': props.get('alias', []),
                        'identifiers': props.get('idNumber', []),
                        'addresses': props.get('address', []),
                        'nationalities': props.get('nationality', []),
                        'programs': props.get('program', []),
                        'source': 'local_data'
                    }
        
        return best_match
    
    def _determine_sanctions_type(self, topics: List[str]) -> str:
        """Determine type of sanctions based on topics"""
        topics_lower = [topic.lower() for topic in topics]
        
        if any('sanction' in topic for topic in topics_lower):
            return 'Economic Sanctions'
        elif any('crime' in topic for topic in topics_lower):
            return 'Criminal Activity'
        elif any('pep' in topic for topic in topics_lower):
            return 'Politically Exposed Person'
        elif any('poi' in topic for topic in topics_lower):
            return 'Person of Interest'
        elif any('terror' in topic for topic in topics_lower):
            return 'Terrorism Related'
        elif any('corrupt' in topic for topic in topics_lower):
            return 'Corruption Related'
        elif any('war' in topic for topic in topics_lower):
            return 'War Crimes'
        else:
            return 'Other'
    
    def _determine_risk_level(self, confidence: int, topics: List[str]) -> str:
        """Determine risk level based on confidence and topics"""
        # Higher risk for certain topics
        high_risk_topics = ['sanction', 'terror', 'war', 'crime']
        has_high_risk_topic = any(any(risk_topic in topic.lower() for risk_topic in high_risk_topics) for topic in topics)
        
        if confidence >= 95 or (confidence >= 85 and has_high_risk_topic):
            return 'CRITICAL'
        elif confidence >= 85:
            return 'HIGH'
        elif confidence >= 75:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _determine_overall_risk_level(self, matches: List[Dict], risk_score: int) -> str:
        """Determine overall risk level based on matches and risk score"""
        if not matches:
            return 'very_low'
        
        # Check for critical matches
        if any(match.get('risk_level') == 'CRITICAL' for match in matches):
            return 'very_high'
        elif any(match.get('risk_level') == 'HIGH' for match in matches):
            return 'high'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        elif risk_score >= 20:
            return 'low'
        else:
            return 'very_low'
    
    def _calculate_risk_score(self, matches: List[Dict]) -> int:
        """Calculate overall risk score from matches"""
        if not matches:
            return 0
        
        # Base score from highest confidence match
        highest_confidence = matches[0].get('confidence', 0)
        risk_score = int(highest_confidence * 0.9)  # Higher base multiplier for critical matches
        
        # Major bonus for multiple critical matches (very high risk scenario)
        if len(matches) > 1:
            # Each additional match adds significant risk
            risk_score += min(len(matches) * 15, 40)  # Increased bonus for multiple matches
        
        # Enhanced bonus for high-risk topics
        for match in matches[:5]:  # Check top 5 matches
            topics = match.get('topics', [])
            risk_level = match.get('risk_level', '')
            
            # Critical entities get maximum bonus
            if risk_level == 'CRITICAL':
                risk_score += 25  # Major bonus for critical risk level
            
            # Topic-based bonuses
            if 'sanctions' in topics:
                risk_score += 25  # Increased sanctions bonus
            if 'terrorism' in topics:
                risk_score += 30  # Very high terrorism bonus
            if 'government' in topics:
                risk_score += 15  # Government/PEP bonus
            if 'pep' in topics:
                risk_score += 20  # Increased PEP bonus
            if 'state-owned' in topics:
                risk_score += 20  # State-owned entity bonus
            if 'energy' in topics:
                risk_score += 10  # Strategic sector bonus
            if 'crime' in topics:
                risk_score += 20
            if 'corruption' in topics:
                risk_score += 15
            if 'money laundering' in topics:
                risk_score += 25
            if 'weapons' in topics:
                risk_score += 35  # Maximum weapons bonus
        
        # Special bonus for very high-risk combinations
        critical_matches = sum(1 for match in matches if match.get('risk_level') == 'CRITICAL')
        if critical_matches >= 2:
            risk_score += 30  # Major bonus for multiple critical entities
        
        # Bonus for high-risk country combinations (Russia, Iran, North Korea, etc.)
        high_risk_countries = ['RU', 'IR', 'KP', 'SY']
        country_matches = sum(1 for match in matches if match.get('country') in high_risk_countries)
        if country_matches >= 2:
            risk_score += 20  # Multiple high-risk countries
        
        # Additional bonus for multiple high-risk topics across entities
        all_topics = []
        for match in matches:
            all_topics.extend(match.get('topics', []))
        
        high_risk_topic_count = sum(1 for topic in ['sanctions', 'terrorism', 'crime', 'money laundering', 'weapons', 'government', 'pep'] if topic in all_topics)
        if high_risk_topic_count >= 4:
            risk_score += 25  # Multiple high-risk topics bonus
        
        return min(risk_score, 100)  # Cap at 100
    
    def _extract_risk_factors(self, matches: List[Dict]) -> List[str]:
        """Extract risk factors from matches"""
        risk_factors = []
        
        for match in matches:
            topics = match.get('topics', [])
            sanctions_type = match.get('sanctions_type', '')
            risk_level = match.get('risk_level', '')
            
            if sanctions_type:
                risk_factors.append(f"{sanctions_type} (Risk Level: {risk_level})")
            
            if 'sanctions' in topics:
                risk_factors.append("Subject to economic sanctions")
            if 'crime' in topics:
                risk_factors.append("Criminal activity reported")
            if 'pep' in topics:
                risk_factors.append("Politically exposed person")
            if 'terrorism' in topics:
                risk_factors.append("Terrorism related")
            if 'corruption' in topics:
                risk_factors.append("Corruption related")
        
        return list(set(risk_factors))  # Remove duplicates 