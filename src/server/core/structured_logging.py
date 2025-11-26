"""Structured logging configuration with optional structlog support.

If structlog is not available in the environment, this module transparently
falls back to standard logging without blocking application startup.
"""

import logging
import logging.config
import sys
from typing import Any, Dict

try:
    import structlog
    from structlog.stdlib import LoggerFactory
    from structlog.processors import (
        TimeStamper,
        add_log_level,
        StackInfoRenderer,
        JSONRenderer,
        ConsoleRenderer,
    )

    STRUCTLOG_AVAILABLE = True
except ImportError:  # structlog не установлен
    structlog = None  # type: ignore[assignment]
    LoggerFactory = None  # type: ignore[assignment]
    TimeStamper = add_log_level = StackInfoRenderer = JSONRenderer = ConsoleRenderer = None
    STRUCTLOG_AVAILABLE = False

from ..config.settings import settings


class _StdLoggerAdapter:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        if kwargs:
            # Log extra fields as a dictionary next to the message
            self._logger.log(level, "%s | %s", msg, kwargs)
        else:
            self._logger.log(level, msg)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)


def configure_logging() -> None:
    """Configure structured logging for the application.

    If structlog is not available, only standard logging is configured.
    """

    if not STRUCTLOG_AVAILABLE or structlog is None:  # type: ignore[truthy-function]
        logging.basicConfig(
            level=settings.LOG_LEVEL,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stdout,
        )
        return

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_log_level,
        structlog.stdlib.add_log_level,
        TimeStamper(fmt="iso"),
        StackInfoRenderer(),
    ]

    # Use JSON renderer in production, console in development
    if settings.ENVIRONMENT == "production":
        processors.append(JSONRenderer())
    else:
        processors.append(ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to integrate with structlog
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": (
                    "console"
                    if settings.ENVIRONMENT != "production"
                    else "json"
                ),
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": True,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> Any:
    """Get a logger instance.

    If structlog is available, return a structured logger,
    otherwise a standard ``logging.Logger``.
    """

    if STRUCTLOG_AVAILABLE and structlog is not None:
        return structlog.get_logger(name)  # type: ignore[no-any-return]

    base_logger = logging.getLogger(name)
    return _StdLoggerAdapter(base_logger)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> Any:
        """Get logger for the class."""
        return get_logger(self.__class__.__name__)


class RequestLogger:
    """Logger for HTTP requests and responses."""

    def __init__(self):
        self.logger = get_logger("http")

    def log_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, Any],
        user_id: str = None,
    ) -> None:
        """Log incoming HTTP request."""
        self.logger.info(
            "http_request",
            method=method,
            path=path,
            user_id=user_id,
            headers_count=len(headers),
        )

    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
    ) -> None:
        """Log HTTP response."""
        self.logger.info(
            "http_response",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
        )

    def log_error(
        self,
        method: str,
        path: str,
        error: Exception,
        user_id: str = None,
    ) -> None:
        """Log HTTP error."""
        self.logger.error(
            "http_error",
            method=method,
            path=path,
            error_type=type(error).__name__,
            error_message=str(error),
            user_id=user_id,
        )


class DatabaseLogger:
    """Logger for database operations."""

    def __init__(self):
        self.logger = get_logger("database")

    def log_query(
        self,
        query: str,
        duration_ms: float,
        params: Dict[str, Any] = None,
    ) -> None:
        """Log database query."""
        self.logger.info(
            "database_query",
            query=(
                query[:100] + "..."
                if len(query) > 100
                else query
            ),
            duration_ms=duration_ms,
            params_count=len(params) if params else 0,
        )

    def log_connection_error(self, error: Exception) -> None:
        """Log database connection error."""
        self.logger.error(
            "database_connection_error",
            error_type=type(error).__name__,
            error_message=str(error),
        )

    def log_transaction(
        self,
        operation: str,
        status: str,
        duration_ms: float,
    ) -> None:
        """Log database transaction."""
        self.logger.info(
            "database_transaction",
            operation=operation,
            status=status,
            duration_ms=duration_ms,
        )


class SecurityLogger:
    """Logger for security events."""

    def __init__(self):
        self.logger = get_logger("security")

    def log_authentication_attempt(
        self,
        email: str,
        ip: str,
        success: bool,
    ) -> None:
        """Log authentication attempt."""
        self.logger.info(
            "authentication_attempt",
            email=email,
            ip=ip,
            success=success,
        )

    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        ip: str,
    ) -> None:
        """Log authorization failure."""
        self.logger.warning(
            "authorization_failure",
            user_id=user_id,
            resource=resource,
            ip=ip,
        )

    def log_suspicious_activity(
        self,
        activity: str,
        details: Dict[str, Any],
        ip: str,
    ) -> None:
        """Log suspicious activity."""
        self.logger.warning(
            "suspicious_activity",
            activity=activity,
            ip=ip,
            **details,
        )


class BusinessLogger:
    """Logger for business events."""

    def __init__(self):
        self.logger = get_logger("business")

    def log_user_registration(
        self,
        user_id: str,
        email: str,
        source: str = "web",
    ) -> None:
        """Log user registration."""
        self.logger.info(
            "user_registered",
            user_id=user_id,
            email=email,
            source=source,
        )

    def log_analysis_request(
        self,
        user_id: str,
        player_id: str,
        analysis_type: str,
    ) -> None:
        """Log analysis request."""
        self.logger.info(
            "analysis_requested",
            user_id=user_id,
            player_id=player_id,
            analysis_type=analysis_type,
        )

    def log_payment_event(
        self,
        user_id: str,
        amount: float,
        currency: str,
        status: str,
        payment_id: str = None,
        provider: str = None,
    ) -> None:
        """Log payment event."""
        self.logger.info(
            "payment_event",
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=status,
            payment_id=payment_id,
            provider=provider,
        )


# Global logger instances
request_logger = RequestLogger()
database_logger = DatabaseLogger()
security_logger = SecurityLogger()
business_logger = BusinessLogger()


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(
            "function_call",
            function=func.__name__,
            args_count=len(args),
            kwargs_count=len(kwargs),
        )

        try:
            result = func(*args, **kwargs)
            logger.info(
                "function_success",
                function=func.__name__,
            )
            return result
        except Exception as e:
            logger.error(
                "function_error",
                function=func.__name__,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise

    return wrapper


def log_api_endpoint(endpoint: str, method: str):
    """Decorator to log API endpoint calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger("api")
            logger.info(
                "api_call",
                endpoint=endpoint,
                method=method,
            )

            try:
                result = func(*args, **kwargs)
                logger.info(
                    "api_success",
                    endpoint=endpoint,
                    method=method,
                )
                return result
            except Exception as e:
                logger.error(
                    "api_error",
                    endpoint=endpoint,
                    method=method,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        return wrapper

    return decorator
