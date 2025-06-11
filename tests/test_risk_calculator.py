import unittest
from utils.risk_calculator import RiskCalculator
from graph.neo4j_service import Neo4jService
import os

class TestRiskCalculator(unittest.TestCase):
    def setUp(self):
        # Enable mock mode for Neo4j
        os.environ['NEO4J_MOCK_MODE'] = 'True'
        self.calculator = RiskCalculator()
        
        # Example sanctions data
        self.sanctions_data = {
            'matched': True,
            'matches': [
                {
                    'confidence': 85,
                    'topics': ['Money Laundering', 'Stage 2: Investigation and Legal Proceedings', 'SEC Violations']
                },
                {
                    'confidence': 75,
                    'topics': ['Business Crimes', 'Stage 1: Pre-Investigation and Allegation']
                }
            ]
        }
        
        # Example web intelligence data
        self.web_intel_data = {
            'risk_indicators': [
                'Suspicious financial transactions',
                'Money Laundering allegations',
                'Regulatory investigation'
            ],
            'sentiment_score': -0.6
        }
        
        # Example graph analysis data
        self.graph_data = {
            'connection_count': 10,
            'risk_connections': 3
        }
        
        # Example multi-entity data
        self.multi_entity_sanctions = {
            'company1': {
                'matched': True,
                'matches': [
                    {
                        'confidence': 90,
                        'topics': ['Sanctions Connect', 'Stage 4: Administrative and Regulatory Actions']
                    }
                ]
            },
            'person1': {
                'matched': True,
                'matches': [
                    {
                        'confidence': 80,
                        'topics': ['PEP', 'Stage 2: Investigation and Legal Proceedings']
                    }
                ]
            }
        }
        
        self.multi_entity_web = {
            'company1': {
                'risk_indicators': ['Sanctions violations', 'Regulatory action'],
                'sentiment_score': -0.4
            },
            'person1': {
                'risk_indicators': ['Political exposure', 'Regulatory scrutiny'],
                'sentiment_score': -0.3
            }
        }
        
        self.multi_entity_graph = {
            'company1': {
                'connection_count': 15,
                'risk_connections': 5
            },
            'person1': {
                'connection_count': 8,
                'risk_connections': 2
            }
        }

    def test_legacy_risk_calculation(self):
        """Test the legacy risk calculation API"""
        result = self.calculator.calculate_risk(
            self.sanctions_data,
            self.web_intel_data,
            self.graph_data
        )
        
        # Verify the result structure
        self.assertIn('risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('component_scores', result)
        self.assertIn('risk_factors', result)
        
        # Verify risk score is between 0 and 1
        self.assertGreaterEqual(result['risk_score'], 0)
        self.assertLessEqual(result['risk_score'], 1)
        
        # Verify risk level is valid
        self.assertIn(result['risk_level'], ['very_low', 'low', 'medium', 'high', 'very_high'])
        
        # Print detailed results
        print("\nLegacy Risk Calculation Results:")
        print(f"Risk Score: {result['risk_score']}")
        print(f"Risk Level: {result['risk_level']}")
        print("Component Scores:")
        for component, score in result['component_scores'].items():
            print(f"  {component}: {score}")
        print("Risk Factors:")
        for factor in result['risk_factors']:
            print(f"  - {factor}")

    def test_comprehensive_risk_calculation(self):
        """Test the comprehensive risk calculation API"""
        result = self.calculator.calculate_comprehensive_risk(
            self.multi_entity_sanctions,
            self.multi_entity_web,
            self.multi_entity_graph,
            'person_and_company'
        )
        
        # Verify the result structure
        self.assertIn('risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('component_scores', result)
        self.assertIn('risk_factors', result)
        self.assertIn('entities_analyzed', result)
        
        # Verify risk score is between 0 and 1
        self.assertGreaterEqual(result['risk_score'], 0)
        self.assertLessEqual(result['risk_score'], 1)
        
        # Verify risk level is valid
        self.assertIn(result['risk_level'], ['very_low', 'low', 'medium', 'high', 'very_high'])
        
        # Verify entities analyzed
        self.assertEqual(set(result['entities_analyzed']), {'company1', 'person1'})
        
        # Print detailed results
        print("\nComprehensive Risk Calculation Results:")
        print(f"Risk Score: {result['risk_score']}")
        print(f"Risk Level: {result['risk_level']}")
        print("Component Scores:")
        for component, score in result['component_scores'].items():
            print(f"  {component}: {score}")
        print("Risk Factors:")
        for factor in result['risk_factors']:
            print(f"  - {factor}")

if __name__ == '__main__':
    unittest.main() 