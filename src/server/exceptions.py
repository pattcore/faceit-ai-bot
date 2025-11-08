"""
Кастомные исключения для обработки ошибок приложения
"""
from fastapi import HTTPException
from typing import Optional


class BaseAPIException(HTTPException):
    """Базовое исключение для API"""
    def __init__(self, status_code: int, detail: str, error_code: Optional[str] = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class PaymentException(BaseAPIException):
    """Исключение при обработке платежей"""
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(status_code=400, detail=detail, error_code=error_code or "PAYMENT_ERROR")


class DemoAnalysisException(BaseAPIException):
    """Исключение при анализе демо-файла"""
    def __init__(self, detail: str, error_code: Optional[str] = None, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail, error_code=error_code or "DEMO_ANALYSIS_ERROR")


class FaceitAPIException(BaseAPIException):
    """Исключение при работе с Faceit API"""
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(status_code=502, detail=detail, error_code=error_code or "FACEIT_API_ERROR")


class DatabaseException(BaseAPIException):
    """Исключение при работе с базой данных"""
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(status_code=500, detail=detail, error_code=error_code or "DATABASE_ERROR")


class ValidationException(BaseAPIException):
    """Исключение при валидации данных"""
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(status_code=422, detail=detail, error_code=error_code or "VALIDATION_ERROR")


class AuthenticationException(BaseAPIException):
    """Исключение при аутентификации"""
    def __init__(self, detail: str = "Authentication failed", error_code: Optional[str] = None):
        super().__init__(status_code=401, detail=detail, error_code=error_code or "AUTHENTICATION_ERROR")


class AuthorizationException(BaseAPIException):
    """Исключение при авторизации"""
    def __init__(self, detail: str = "Access denied", error_code: Optional[str] = None):
        super().__init__(status_code=403, detail=detail, error_code=error_code or "AUTHORIZATION_ERROR")

