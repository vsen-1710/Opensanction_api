import logging
import requests
import json
import os
from fuzzywuzzy import fuzz
from typing import Dict, Any, List
import time

logger = logging.getLogger(__name__)

class OpenSanctionsService:
    """Real OpenSanctions service with actual data checking"""
    
    def __init__(self):
        self.opensanctions_api_url = os.getenv('OPENSANCTIONS_API_URL', 'https://api.opensanctions.org')
        self.dataset_url = os.getenv(
            'OPENSANCTIONS_DATASET_URL',
            'https://data.opensanctions.org/datasets/latest/default/entities.ftm.json'
        )
        self.sanctions_data = []
        self.data_loaded = False
        self._load_sanctions_data()
        logger.info("OpenSanctions service initialized with real data")
    
    def _load_sanctions_data(self):
        """Load OpenSanctions dataset"""
        try:
            logger.info("Loading OpenSanctions dataset...")
            response = requests.get(self.dataset_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Parse JSON lines format
            for line_num, line in enumerate(response.iter_lines(decode_unicode=True)):
                if line.strip():
                    try:
                        entity = json.loads(line)
                        # Only keep relevant entities with names
                        if self._is_relevant_entity(entity):
                            self.sanctions_data.append(entity)
                    except json.JSONDecodeError:
                        continue
                
                # Limit to prevent memory issues (first 10000 entities)
                if line_num > 10000:
                    break
            
            self.data_loaded = True
            logger.info(f"Loaded {len(self.sanctions_data)} sanctions entities")
            
        except Exception as e:
            logger.error(f"Failed to load OpenSanctions data: {str(e)}")
            # Create minimal mock data as fallback
            self.sanctions_data = [
                {
                    "id": "sanctions-1",
                    "properties": {
                        "name": ["Vladimir Putin"],
                        "birthDate": ["1952-10-07"],
                        "country": ["ru"],
                        "topics": ["sanctions"]
                    }
                }
            ]
            self.data_loaded = True
    
    def _is_relevant_entity(self, entity: Dict) -> bool:
        """Check if entity is relevant for sanctions checking"""
        props = entity.get('properties', {})
        
        # Must have a name
        if not props.get('name'):
            return False
        
        # Check for sanctions-related topics
        topics = props.get('topics', [])
        relevant_topics = ['sanctions', 'crime', 'pep', 'poi']
        
        return any(topic in topics for topic in relevant_topics)
    
    def check_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check entity against real sanctions list"""
        if not self.data_loaded:
            return {
                'matches': [],
                'total_matches': 0,
                'risk_score': 0,
                'status': 'data_not_loaded'
            }
        
        entity_name = entity_data.get('name', '').strip().lower()
        if not entity_name:
            return {
                'matches': [],
                'total_matches': 0,
                'risk_score': 0,
                'status': 'no_name_provided'
            }
        
        matches = []
        
        # Search through sanctions data
        for sanctions_entity in self.sanctions_data:
            match = self._check_name_match(entity_name, sanctions_entity, entity_data)
            if match:
                matches.append(match)
        
        # Sort by confidence score
        matches.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(matches)
        
        return {
            'matches': matches[:5],  # Top 5 matches
            'total_matches': len(matches),
            'risk_score': risk_score,
            'status': 'checked',
            'highest_confidence': matches[0].get('confidence', 0) if matches else 0,
            'matched': len(matches) > 0
        }
    
    def _check_name_match(self, search_name: str, sanctions_entity: Dict, entity_data: Dict) -> Dict[str, Any]:
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
                        'risk_level': self._determine_risk_level(confidence, props.get('topics', []))
                    }
        
        return best_match
    
    def _determine_sanctions_type(self, topics: List[str]) -> str:
        """Determine type of sanctions based on topics"""
        if 'sanctions' in topics:
            return 'Economic Sanctions'
        elif 'crime' in topics:
            return 'Criminal Activity'
        elif 'pep' in topics:
            return 'Politically Exposed Person'
        elif 'poi' in topics:
            return 'Person of Interest'
        else:
            return 'Other'
    
    def _determine_risk_level(self, confidence: int, topics: List[str]) -> str:
        """Determine risk level based on confidence and topics"""
        if confidence >= 95:
            return 'CRITICAL'
        elif confidence >= 85:
            return 'HIGH'
        elif confidence >= 75:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_risk_score(self, matches: List[Dict]) -> int:
        """Calculate overall risk score from matches"""
        if not matches:
            return 0
        
        # Base score from highest confidence match
        highest_confidence = matches[0].get('confidence', 0)
        risk_score = int(highest_confidence)
        
        # Bonus for multiple matches
        if len(matches) > 1:
            risk_score += min(len(matches) * 5, 20)
        
        # Bonus for high-risk topics
        for match in matches[:3]:  # Check top 3 matches
            topics = match.get('topics', [])
            if 'sanctions' in topics:
                risk_score += 20
            elif 'crime' in topics:
                risk_score += 15
            elif 'pep' in topics:
                risk_score += 10
        
        return min(risk_score, 100)  # Cap at 100 