"""
Cache Service
Сервис кэширования с Redis
"""
import json
import logging
from typing import Optional, Any
import os

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, caching disabled")


class CacheService:
    """Caching service"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        
        if REDIS_AVAILABLE:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                self.enabled = True
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.enabled = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600  # 1 час по умолчанию
    ) -> bool:
        """Save value to cache"""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.enabled:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def get_player_cache_key(self, nickname: str) -> str:
        """Get cache key for player"""
        return f"player:analysis:{nickname.lower()}"
    
    def get_stats_cache_key(self, nickname: str) -> str:
        """Get cache key for stats"""
        return f"player:stats:{nickname.lower()}"


# Singleton instance
cache_service = CacheService()
