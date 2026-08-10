import json
import logging
import time
from typing import Any, Optional
import redis

from app.core.config import settings

logger = logging.getLogger("careerpilot.cache")


class InMemoryTTLCache:
    """Thread-safe, lightweight in-memory TTL cache fallback when Redis is unconfigured."""
    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            val, expires_at = self._cache[key]
            if time.time() < expires_at:
                return val
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        expires_at = time.time() + ttl_seconds
        self._cache[key] = (value, expires_at)

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]

    def delete_pattern(self, pattern: str) -> int:
        # Simple prefix matching e.g. "jobs:*"
        prefix = pattern.replace("*", "")
        keys_to_del = [k for k in self._cache.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            del self._cache[k]
        return len(keys_to_del)

    def clear(self):
        self._cache.clear()


class CacheService:
    def __init__(self):
        self.redis_client = None
        self.in_memory = InMemoryTTLCache()

        if settings.REDIS_URL:
            try:
                client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2.0)
                client.ping()
                self.redis_client = client
                logger.info("Redis cache connected successfully.")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis at {settings.REDIS_URL}, using in-memory TTL fallback: {e}")
                self.redis_client = None
        else:
            logger.info("REDIS_URL not configured. Operating in high-performance in-memory TTL cache mode.")
        self.in_memory.clear()


    def get(self, key: str) -> Optional[Any]:
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
                return None
            return self.in_memory.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return self.in_memory.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        try:
            serialized = json.dumps(value, default=str)
            if self.redis_client:
                self.redis_client.setex(key, ttl_seconds, serialized)
            self.in_memory.set(key, value, ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            self.in_memory.set(key, value, ttl_seconds)
            return False

    def delete(self, key: str) -> bool:
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            self.in_memory.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            self.in_memory.delete(key)
            return False

    def delete_pattern(self, pattern: str) -> int:
        count = 0
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
            mem_count = self.in_memory.delete_pattern(pattern)
            return max(count, mem_count)
        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern '{pattern}': {e}")
            return self.in_memory.delete_pattern(pattern)


cache_service = CacheService()
