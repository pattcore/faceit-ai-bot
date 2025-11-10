"""
Sentry integration for error tracking
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import os


def init_sentry():
    """Initialize Sentry"""
    
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("ENVIRONMENT", "development")
    
    if not sentry_dsn:
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=1.0 if environment == "development" else 0.1,
        profiles_sample_rate=1.0 if environment == "development" else 0.1,
        integrations=[
            FastApiIntegration(),
            RedisIntegration(),
        ],
        # Filter sensitive data
        before_send=before_send,
    )


def before_send(event, hint):
    """Filter before sending to Sentry"""
    
    # Remove sensitive data
    if 'request' in event:
        headers = event['request'].get('headers', {})
        if 'Authorization' in headers:
            headers['Authorization'] = '[Filtered]'
        if 'X-API-Key' in headers:
            headers['X-API-Key'] = '[Filtered]'
    
    return event
