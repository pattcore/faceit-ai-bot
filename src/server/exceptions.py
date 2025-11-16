"""
Custom Exceptions for Faceit AI Bot
"""
from fastapi import HTTPException, status


class FaceitAPIError(HTTPException):
    """Base exception for Faceit API errors"""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class PlayerNotFoundError(HTTPException):
    """Player not found on Faceit"""
    def __init__(self, nickname: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player '{nickname}' not found on Faceit"
        )


class FaceitAPIKeyMissingError(HTTPException):
    """Faceit API key is not configured"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Faceit API key is not configured. Please contact administrator."
        )


class RateLimitExceededError(HTTPException):
    """Rate limit exceeded"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


class AnalysisError(HTTPException):
    """Error during player analysis"""
    def __init__(self, detail: str = "Failed to analyze player"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class InvalidPlayerDataError(HTTPException):
    """Invalid or incomplete player data"""
    def __init__(self, detail: str = "Invalid player data"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class GroqAPIError(HTTPException):
    """Error with Groq AI API"""
    def __init__(self, detail: str = "AI analysis service unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class DatabaseError(HTTPException):
    """Database operation error"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class AuthenticationError(HTTPException):
    """Authentication failed"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Authorization failed - insufficient permissions"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationError(HTTPException):
    """Input validation error"""
    def __init__(self, detail: str = "Invalid input data"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
