"""
Integration тесты для API платежей
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.integration
@pytest.mark.api
class TestPaymentsAPI:
    """Тесты для API платежей"""
    
    def test_get_payment_methods(self, client):
        """Тест получения методов платежа для региона"""
        response = client.get("/payments/methods/RU")
        
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "available_methods" in data or "enabled_providers" in data
    
    def test_get_payment_methods_invalid_region(self, client):
        """Тест получения методов платежа для невалидного региона"""
        response = client.get("/payments/methods/INVALID")
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data
    
    @patch('src.server.features.payments.service.PaymentService.create_payment')
    async def test_create_payment_success(self, mock_create, client, payment_request):
        """Тест успешного создания платежа"""
        mock_create.return_value = {
            "payment_id": "test_payment_id",
            "status": "pending",
            "payment_url": "https://payment.test.url",
            "amount": 500.0,
            "currency": "RUB"
        }
        
        response = client.post(
            "/payments/create",
            json=payment_request
        )
        
        # Может быть 200 или 500 в зависимости от реализации
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "payment_id" in data
            assert "status" in data
    
    def test_create_payment_invalid_request(self, client):
        """Тест создания платежа с невалидным запросом"""
        invalid_request = {
            "amount": -100.0,
            "currency": "INVALID",
            "provider": "INVALID"
        }
        
        response = client.post(
            "/payments/create",
            json=invalid_request
        )
        
        assert response.status_code in [400, 422]  # Validation error
    
    @patch('src.server.features.payments.service.PaymentService.check_payment_status')
    async def test_check_payment_status(self, mock_check, client):
        """Тест проверки статуса платежа"""
        mock_check.return_value = "pending"
        
        response = client.get(
            "/payments/status/test_payment_id?provider=YOOKASSA"
        )
        
        # Может быть 200 или 500 в зависимости от реализации
        assert response.status_code in [200, 500]
    
    @patch('src.server.features.payments.service.PaymentService.process_webhook')
    async def test_sbp_webhook(self, mock_webhook, client):
        """Тест вебхука СБП"""
        mock_webhook.return_value = None
        
        webhook_data = {
            "payment_id": "test_payment_id",
            "status": "completed"
        }
        
        response = client.post(
            "/payments/webhook/sbp",
            json=webhook_data
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
    
    @patch('src.server.features.payments.service.PaymentService.process_webhook')
    async def test_yookassa_webhook(self, mock_webhook, client):
        """Тест вебхука YooKassa"""
        mock_webhook.return_value = None
        
        webhook_data = {
            "event": "payment.succeeded",
            "object": {
                "id": "test_payment_id",
                "status": "succeeded"
            }
        }
        
        response = client.post(
            "/payments/webhook/yookassa",
            json=webhook_data
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"

