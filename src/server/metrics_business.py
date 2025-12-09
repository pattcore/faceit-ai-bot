"""Business Prometheus metrics for player analysis and users."""

from prometheus_client import Counter, Histogram


ANALYSIS_REQUESTS = Counter(
    "faceit_analysis_requests_total",
    "Total analysis requests",
)


ANALYSIS_DURATION = Histogram(
    "faceit_analysis_duration_seconds",
    "Analysis duration in seconds",
)


ACTIVE_USERS = Counter(
    "faceit_active_users",
    "Active user sessions",
)


CAPTCHA_SUCCESS = Counter(
    "faceit_captcha_success_total",
    "Successful CAPTCHA verifications",
)


CAPTCHA_FAILED = Counter(
    "faceit_captcha_failed_total",
    "Failed CAPTCHA verifications",
)


CAPTCHA_ERRORS = Counter(
    "faceit_captcha_errors_total",
    "Errors during CAPTCHA provider communication or configuration",
)


RATE_LIMIT_EXCEEDED = Counter(
    "faceit_rate_limit_exceeded_total",
    "Number of times per-user operation rate limit was exceeded",
    ["operation", "tier", "window"],
)


AUTH_FAILED = Counter(
    "faceit_auth_failed_total",
    "Total failed authentication attempts",
    ["ip", "reason"],
)


AUTH_SUCCESS = Counter(
    "faceit_auth_success_total",
    "Total successful authentication events",
    ["ip", "method"],
)
