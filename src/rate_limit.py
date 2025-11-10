"""
Rate limiting middleware
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import os
from datetime import datetime, timedelta

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))


class RateLimiter:
    """Rate limiter based on Redis"""
    
    def __init__(self, requests: int = 100, window: int = 3600):
        self.requests = requests
        self.window = window
    
    async def check_rate_limit(self, request: Request):
        """Check rate limit for IP"""
        
        # Get client IP
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Check current request count
        current = redis_client.get(key)
        
        if current is None:
            # First request
            redis_client.setex(key, self.window, 1)
            return True
        
        current = int(current)
        
        if current >= self.requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.requests} requests per hour."
            )
        
        # Increment counter
        redis_client.incr(key)
        return True


# Middleware for FastAPI
async def rate_limit_middleware(request: Request, call_next):
    """Middleware for rate limit checking"""
    
    # Skip for certain paths
    if request.url.path in ["/health", "/metrics", "/docs"]:
        return await call_next(request)
    
    limiter = RateLimiter(requests=100, window=3600)
    await limiter.check_rate_limit(request)
    
    response = await call_next(request)
    return response
