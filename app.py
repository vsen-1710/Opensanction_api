import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.cache import CacheManager
from services.risk_service import RiskService, RisknetError
from utils.validation import InputValidator
from utils.errors import RisknetError
import config  # Import config module
import time
from utils.performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize services
cache_manager = CacheManager()
risk_service = RiskService()
validator = InputValidator()
performance_monitor = PerformanceMonitor()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with performance mode info"""
    return jsonify({
        'status': 'healthy',
        'service': 'Risknet API',
        'version': '1.0.0',
        'fast_mode_enabled': risk_service.fast_mode,
        'optimizations': {
            'parallel_processing': risk_service.fast_mode,
            'web_search_fast_mode': risk_service.web_search_service.fast_mode,
            'ai_fast_mode': risk_service.ai_service.fast_mode
        },
        'timestamp': cache_manager._get_timestamp()
    })

@app.route('/api/performance/fast-mode', methods=['POST'])
def set_fast_mode():
    """Enable or disable fast mode optimizations"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'JSON body required'}), 400
        
        enabled = data.get('enabled', True)
        
        # Apply to all services
        risk_service.set_fast_mode(enabled)
        risk_service.web_search_service.set_fast_mode(enabled)
        risk_service.ai_service.set_fast_mode(enabled)
        
        return jsonify({
            'message': f'Fast mode {"enabled" if enabled else "disabled"}',
            'fast_mode_enabled': enabled,
            'applied_to': ['risk_service', 'web_search_service', 'ai_service']
        })
        
    except Exception as e:
        logger.error(f"Failed to set fast mode: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance/status', methods=['GET'])
def get_performance_status():
    """Get current performance optimization status"""
    return jsonify({
        'performance_mode': 'fast' if risk_service.fast_mode else 'full',
        'optimizations': {
            'risk_service_fast_mode': risk_service.fast_mode,
            'web_search_fast_mode': risk_service.web_search_service.fast_mode,
            'ai_fast_mode': risk_service.ai_service.fast_mode,
            'parallel_processing': risk_service.fast_mode,
            'caching_enabled': True
        },
        'api_availability': {
            'serper_api': bool(risk_service.web_search_service.serper_api_key),
            'openai_api': bool(risk_service.ai_service.openai_api_key),
            'deepseek_api': bool(risk_service.ai_service.deepseek_api_key),
            'perplexity_api': bool(risk_service.web_search_service.perplexity_api_key)
        },
        'speed_estimates': {
            'person_only': '2-5 seconds' if risk_service.fast_mode else '4-8 seconds',
            'company_only': '3-6 seconds' if risk_service.fast_mode else '5-10 seconds',
            'person_and_company': '4-8 seconds (parallel)' if risk_service.fast_mode else '8-15 seconds (sequential)',
            'cached_requests': '< 0.1 seconds'
        }
    })

@app.route('/api/check_risk', methods=['POST'])
def check_risk():
    """Enhanced risk assessment endpoint with flexible input handling and integrated relationship analysis"""
    start_time = time.time()
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            performance_monitor.track_request('/api/check_risk', start_time, False)
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide either person details, company details, or both'
            }), 400
        
        # Validate and normalize input
        try:
            validated_data = validator.validate_risk_assessment_input(request_data)
        except ValueError as e:
            performance_monitor.track_request('/api/check_risk', start_time, False)
            return jsonify({
                'error': 'Input validation failed',
                'message': str(e)
            }), 400
        
        # Log the assessment type
        input_type = validated_data.get('input_type')
        logger.info(f"Processing {input_type} risk assessment with integrated relationship analysis")
        
        # Perform comprehensive risk assessment (includes relationship analysis)
        risk_result = risk_service.assess_risk(validated_data)
        
        # Add input metadata to response
        risk_result['input_metadata'] = {
            'input_type': input_type,
            'entities_provided': {
                'person': bool(validated_data.get('person')),
                'company': bool(validated_data.get('company'))
            },
            'validation_passed': True,
            'includes_relationship_analysis': True
        }
        
        performance_monitor.track_request('/api/check_risk', start_time, True)
        return jsonify(risk_result)
        
    except RisknetError as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        performance_monitor.track_request('/api/check_risk', start_time, False)
        return jsonify({
            'error': 'Risk assessment failed',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in risk assessment: {str(e)}")
        performance_monitor.track_request('/api/check_risk', start_time, False)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during risk assessment'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get API statistics and status"""
    start_time = time.time()
    try:
        stats = risk_service.get_statistics()
        performance_stats = performance_monitor.get_metrics()
        stats['performance_metrics'] = performance_stats
        performance_monitor.track_request('/api/stats', start_time, True)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        performance_monitor.track_request('/api/stats', start_time, False)
        return jsonify({
            'error': 'Statistics unavailable',
            'message': str(e)
        }), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the cache"""
    start_time = time.time()
    try:
        cache_manager.clear()
        performance_monitor.track_request('/api/cache/clear', start_time, True)
        return jsonify({
            'message': 'Cache cleared successfully',
            'timestamp': cache_manager._get_timestamp()
        })
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        performance_monitor.track_request('/api/cache/clear', start_time, False)
        return jsonify({
            'error': 'Failed to clear cache',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': [
            'GET /health',
            'POST /api/check_risk (includes relationship analysis)',
            'GET /api/stats',
            'POST /api/performance/fast-mode',
            'GET /api/performance/status',
            'POST /api/cache/clear'
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    logger.info("Starting Risknet API on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 