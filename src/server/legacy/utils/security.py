"""
Security utility functions for OWASP compliance
"""
import re
import bleach
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Security utilities for input validation and sanitization"""

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML input to prevent XSS"""
        # Allow only basic tags
        allowed_tags = ['p', 'br', 'strong', 'em', 'u']
        allowed_attrs = {}
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs)

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format (alphanumeric + underscore)"""
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[^\w\.-]', '', filename)
        # Prevent directory traversal
        sanitized = sanitized.replace('..', '')
        return sanitized[:100]  # Limit length

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        # Faceit API keys are typically 32 characters hex
        pattern = r'^[a-f0-9]{32}$'
        return bool(re.match(pattern, api_key))

    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any], ip: str = None):
        """Log security-related events"""
        logger.warning(
            "SECURITY_EVENT",
            extra={
                "event_type": event_type,
                "details": details,
                "ip_address": ip,
                "timestamp": str(datetime.utcnow())
            }
        )

    @staticmethod
    def validate_request_size(content_length: int, max_size: int = 1024*1024) -> bool:
        """Validate request size to prevent DoS"""
        return content_length <= max_size

# Security validator for Pydantic models
def security_validator(cls, v):
    """Pydantic validator for security checks"""
    if isinstance(v, str):
        # Basic SQL injection check
        dangerous_patterns = [
            r';\s*(?:DROP|DELETE|UPDATE|INSERT|ALTER)',
            r'--',
            r'/\*.*\*/',
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                SecurityUtils.log_security_event(
                    "suspicious_input_detected",
                    {"pattern": pattern, "input": v[:100]}
                )
                raise ValueError("Potentially dangerous input detected")

    return v
