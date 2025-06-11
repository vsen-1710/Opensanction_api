import logging
import time
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and track API performance metrics"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'start_time': time.time(),
            'request_times': [],
            'endpoint_stats': {}
        }
        logger.info("Performance monitor initialized")
    
    def track_request(self, endpoint: str, start_time: float, success: bool = True):
        """Track a request's performance"""
        try:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Update basic metrics
            self.metrics['total_requests'] += 1
            if success:
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
            
            # Update request times
            self.metrics['request_times'].append(duration)
            if len(self.metrics['request_times']) > 1000:  # Keep last 1000 requests
                self.metrics['request_times'] = self.metrics['request_times'][-1000:]
            
            # Update average response time
            self.metrics['average_response_time'] = sum(self.metrics['request_times']) / len(self.metrics['request_times'])
            
            # Update endpoint statistics
            if endpoint not in self.metrics['endpoint_stats']:
                self.metrics['endpoint_stats'][endpoint] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'average_response_time': 0,
                    'request_times': []
                }
            
            endpoint_stats = self.metrics['endpoint_stats'][endpoint]
            endpoint_stats['total_requests'] += 1
            if success:
                endpoint_stats['successful_requests'] += 1
            else:
                endpoint_stats['failed_requests'] += 1
            
            endpoint_stats['request_times'].append(duration)
            if len(endpoint_stats['request_times']) > 100:  # Keep last 100 requests per endpoint
                endpoint_stats['request_times'] = endpoint_stats['request_times'][-100:]
            
            endpoint_stats['average_response_time'] = sum(endpoint_stats['request_times']) / len(endpoint_stats['request_times'])
            
        except Exception as e:
            logger.error(f"Error tracking request performance: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            uptime = time.time() - self.metrics['start_time']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            
            return {
                'total_requests': self.metrics['total_requests'],
                'successful_requests': self.metrics['successful_requests'],
                'failed_requests': self.metrics['failed_requests'],
                'average_response_time': round(self.metrics['average_response_time'] * 1000, 2),  # Convert to milliseconds
                'uptime': f"{hours}h {minutes}m {seconds}s",
                'endpoint_stats': {
                    endpoint: {
                        'total_requests': stats['total_requests'],
                        'successful_requests': stats['successful_requests'],
                        'failed_requests': stats['failed_requests'],
                        'average_response_time': round(stats['average_response_time'] * 1000, 2)  # Convert to milliseconds
                    }
                    for endpoint, stats in self.metrics['endpoint_stats'].items()
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {
                'error': 'Failed to get performance metrics',
                'message': str(e)
            }
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        try:
            self.metrics = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'start_time': time.time(),
                'request_times': [],
                'endpoint_stats': {}
            }
            logger.info("Performance metrics reset")
        except Exception as e:
            logger.error(f"Error resetting performance metrics: {str(e)}") 