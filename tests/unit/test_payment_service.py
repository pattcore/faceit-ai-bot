"""
Unit тесты для сервиса платежей
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.server.features.payments.service import PaymentService
from src.server.features.payments.models import PaymentRequest, PaymentProvider, Currency
from src.server.exceptions import PaymentException


@pytest.mark.unit
class TestPaymentService:
    """Тесты для PaymentService"""
    
    @pytest.fixture
    def settings(self):
        """Фикстура настроек"""
        settings = Mock()
        settings.SBP_TOKEN = "test_sbp_token"
        settings.SBP_API_URL = "https://api.sbp.test"
        settings.YOOKASSA_SHOP_ID = "test_shop_id"
        settings.YOOKASSA_SECRET_KEY = "test_secret_key"
        settings.YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"
        settings.WEBSITE_URL = "http://localhost:3000"
        settings.API_URL = "http://localhost:8000"
        return settings
    
    @pytest.fixture
    def payment_service(self, settings):
        """Создание сервиса платежей"""
        return PaymentService(settings)
    
    @pytest.fixture
    def payment_request(self):
        """Фикстура платежного запроса"""
        return PaymentRequest(
            amount=500.0,
            currency=Currency.RUB,
            provider=PaymentProvider.YOOKASSA,
            user_id="test_user_id",
            subscription_tier="BASIC",
            description="Test payment"
        )
    
    @pytest.mark.asyncio
    async def test_create_payment_invalid_provider(self, payment_service):
        """Тест создания платежа с невалидным провайдером"""
        request = PaymentRequest(
            amount=500.0,
            currency=Currency.RUB,
            provider="INVALID",
            user_id="test_user_id"
        )
        
        with pytest.raises(Exception):
            await payment_service.create_payment(request)
    
    @pytest.mark.asyncio
    @patch('src.server.features.payments.service.httpx.AsyncClient')
    async def test_process_yookassa_payment_success(self, mock_client, payment_service, payment_request):
        """Тест успешной обработки платежа через YooKassa"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "test_payment_id",
            "status": "pending",
            "confirmation": {
                "confirmation_url": "https://payment.test.url"
            },
            "amount": {
                "value": "500.00",
                "currency": "RUB"
            },
            "created_at": datetime.now().isoformat()
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client.return_value = mock_client_instance
        
        result = await payment_service._process_yookassa_payment(payment_request)
        
        assert result is not None
        assert result.payment_id == "test_payment_id"
        assert result.status == "pending"
        assert result.payment_url is not None
    
    @pytest.mark.asyncio
    @patch('src.server.features.payments.service.httpx.AsyncClient')
    async def test_process_yookassa_payment_failure(self, mock_client, payment_service, payment_request):
        """Тест обработки ошибки при платеже через YooKassa"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client.return_value = mock_client_instance
        
        with pytest.raises(Exception):
            await payment_service._process_yookassa_payment(payment_request)
    
    def test_validate_payment_method(self, payment_service):
        """Тест валидации метода платежа"""
        request = PaymentRequest(
            amount=500.0,
            currency=Currency.RUB,
            provider=PaymentProvider.YOOKASSA,
            user_id="test_user_id"
        )
        
        # Test should pass without exceptions for valid request
        try:
            payment_service._validate_payment_method(request)
        except Exception as e:
            pytest.fail(f"Валидация не должна вызывать исключение для валидного запроса: {e}")
    
    def test_detect_region(self, payment_service):
        """Тест определения региона"""
        request_rub = PaymentRequest(
            amount=500.0,
            currency=Currency.RUB,
            provider=PaymentProvider.YOOKASSA,
            user_id="test_user_id"
        )
        
        region = payment_service._detect_region(request_rub)
        assert region == "RU"
        
        request_usd = PaymentRequest(
            amount=500.0,
            currency=Currency.USD,
            provider=PaymentProvider.STRIPE,
            user_id="test_user_id"
        )
        
        region = payment_service._detect_region(request_usd)
        assert region == "US"

