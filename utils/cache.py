import logging
import json
import os
import redis
from typing import Any, Optional, Dict
import time

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis cache manager for storing risk assessment results"""
    
    def __init__(self):
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        self.cache_ttl = int(os.getenv('CACHE_TTL', 3600))  # 1 hour default
        
        self.redis_client = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection"""
        try:
            # Create Redis connection
            connection_kwargs = {
                'host': self.redis_host,
                'port': self.redis_port,
                'db': self.redis_db,
                'decode_responses': True,
                'socket_timeout': 5,
                'socket_connect_timeout': 5
            }
            
            if self.redis_password:
                connection_kwargs['password'] = self.redis_password
            
            self.redis_client = redis.Redis(**connection_kwargs)
            
            # Test connection
            self.redis_client.ping()
            
            logger.info("Successfully connected to Redis cache")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}")
            # Continue without cache
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached value by key
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(f"risknet:{key}")
            if cached_data:
                data = json.loads(cached_data)
                
                # Check if data has expired (additional safety check)
                if 'cached_at' in data:
                    cached_at = data['cached_at']
                    if time.time() - cached_at > self.cache_ttl:
                        # Data is expired, remove it
                        self.delete(key)
                        return None
                
                logger.debug(f"Cache hit for key: {key}")
                return data
            
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error getting cached data for key {key}: {str(e)}")
        
        return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set cached value with optional TTL
        
        Args:
            key: Cache key
            value: Data to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Add metadata to cached data
            cache_data = {
                **value,
                'cached_at': time.time(),
                'cache_key': key
            }
            
            serialized_data = json.dumps(cache_data, default=self._json_serializer)
            
            # Use provided TTL or default
            ttl_to_use = ttl if ttl is not None else self.cache_ttl
            
            # Set with expiration
            result = self.redis_client.setex(
                f"risknet:{key}", 
                ttl_to_use, 
                serialized_data
            )
            
            if result:
                logger.debug(f"Cached data for key: {key} (TTL: {ttl_to_use}s)")
                return True
            
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Error caching data for key {key}: {str(e)}")
        
        return False
    
    def delete(self, key: str) -> bool:
        """
        Delete cached value
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(f"risknet:{key}")
            if result:
                logger.debug(f"Deleted cache key: {key}")
                return True
        
        except redis.RedisError as e:
            logger.warning(f"Error deleting cache key {key}: {str(e)}")
        
        return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(f"risknet:{key}"))
        
        except redis.RedisError as e:
            logger.warning(f"Error checking cache key existence {key}: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.redis_client:
            return {
                'status': 'disconnected',
                'total_keys': 0,
                'memory_usage': 0,
                'hit_ratio': 0.0
            }
        
        try:
            # Get Redis info
            info = self.redis_client.info()
            
            # Count Risknet keys
            risknet_keys = self.redis_client.keys("risknet:*")
            
            stats = {
                'status': 'connected',
                'total_keys': len(risknet_keys),
                'memory_usage': info.get('used_memory_human', 'Unknown'),
                'memory_usage_bytes': info.get('used_memory', 0),
                'connected_clients': info.get('connected_clients', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
            
            # Calculate hit ratio
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            total_requests = hits + misses
            
            if total_requests > 0:
                stats['hit_ratio'] = hits / total_requests
            else:
                stats['hit_ratio'] = 0.0
            
            return stats
            
        except redis.RedisError as e:
            logger.warning(f"Error getting cache stats: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def flush_expired(self) -> int:
        """
        Flush expired cache entries (Redis handles this automatically, but we can clean up manually)
        
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            deleted_count = 0
            current_time = time.time()
            
            # Get all Risknet keys
            keys = self.redis_client.keys("risknet:*")
            
            for key in keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        parsed_data = json.loads(data)
                        cached_at = parsed_data.get('cached_at', 0)
                        
                        # Check if expired
                        if current_time - cached_at > self.cache_ttl:
                            self.redis_client.delete(key)
                            deleted_count += 1
                            
                except (json.JSONDecodeError, KeyError):
                    # Invalid data format, delete it
                    self.redis_client.delete(key)
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")
            
            return deleted_count
            
        except redis.RedisError as e:
            logger.warning(f"Error flushing expired cache: {str(e)}")
            return 0
    
    def clear_all(self) -> bool:
        """
        Clear all Risknet cache entries
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys("risknet:*")
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} cache entries")
                return True
            
            return True
            
        except redis.RedisError as e:
            logger.warning(f"Error clearing cache: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test Redis connection
        
        Returns:
            True if connected, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        
        except redis.RedisError:
            return False
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for handling datetime and other objects"""
        if hasattr(obj, 'isoformat'):
            # Handle datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle custom objects
            return obj.__dict__
        else:
            # Let the default JSON encoder handle it
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def get_cache_key_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific cache key
        
        Args:
            key: Cache key to inspect
            
        Returns:
            Dictionary with key information or None
        """
        if not self.redis_client:
            return None
        
        try:
            full_key = f"risknet:{key}"
            
            # Check if key exists
            if not self.redis_client.exists(full_key):
                return None
            
            # Get TTL
            ttl = self.redis_client.ttl(full_key)
            
            # Get data size
            data = self.redis_client.get(full_key)
            data_size = len(data.encode('utf-8')) if data else 0
            
            # Try to parse data for additional info
            cached_at = None
            if data:
                try:
                    parsed_data = json.loads(data)
                    cached_at = parsed_data.get('cached_at')
                except json.JSONDecodeError:
                    pass
            
            return {
                'key': key,
                'exists': True,
                'ttl_seconds': ttl,
                'size_bytes': data_size,
                'cached_at': cached_at,
                'age_seconds': time.time() - cached_at if cached_at else None
            }
            
        except redis.RedisError as e:
            logger.warning(f"Error getting cache key info for {key}: {str(e)}")
            return None
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except redis.RedisError as e:
                logger.warning(f"Error closing Redis connection: {str(e)}")

    def _get_timestamp(self) -> int:
        """Get current timestamp"""
        return int(time.time())

    def clear(self):
        """Clear all cached results"""
        try:
            self.redis_client.flushall()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}") 