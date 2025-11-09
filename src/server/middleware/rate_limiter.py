"""
Rate Limiter Middleware
Ограничение частоты запросов
"""
import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter для защиты API"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Хранилище запросов: {ip: [(timestamp, count)]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
    
    def _clean_old_requests(self, requests_list: list, time_window: int) -> list:
        """Очистить старые запросы"""
        current_time = time.time()
        return [
            (timestamp, count)
            for timestamp, count in requests_list
            if current_time - timestamp < time_window
        ]
    
    def _get_client_ip(self, request: Request) -> str:
        """Получить IP клиента"""
        # Проверяем заголовки прокси
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback на прямой IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, str]:
        """
        Проверить лимит запросов
        
        Returns:
            (allowed, message)
        """
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Очищаем старые запросы
        self.minute_requests[client_ip] = self._clean_old_requests(
            self.minute_requests[client_ip],
            60  # 1 минута
        )
        self.hour_requests[client_ip] = self._clean_old_requests(
            self.hour_requests[client_ip],
            3600  # 1 час
        )
        
        # Подсчитываем запросы
        minute_count = sum(count for _, count in self.minute_requests[client_ip])
        hour_count = sum(count for _, count in self.hour_requests[client_ip])
        
        # Проверяем лимиты
        if minute_count >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        if hour_count >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Добавляем текущий запрос
        self.minute_requests[client_ip].append((current_time, 1))
        self.hour_requests[client_ip].append((current_time, 1))
        
        return True, "OK"
    
    async def __call__(self, request: Request):
        """Middleware для FastAPI"""
        allowed, message = await self.check_rate_limit(request)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {self._get_client_ip(request)}")
            raise HTTPException(
                status_code=429,
                detail=message
            )


# Singleton instance
rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000
)
