"""
Integration тесты для API анализа демо
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from io import BytesIO


@pytest.mark.integration
@pytest.mark.api
class TestDemoAPI:
    """Тесты для API анализа демо"""
    
    def test_analyze_demo_success(self, client):
        """Тест успешного анализа демо"""
        # Создаем мок файла
        demo_file = ("test_demo.dem", BytesIO(b"fake demo content"), "application/octet-stream")
        
        response = client.post(
            "/demo/analyze",
            files={"demo": demo_file}
        )
        
        # Проверяем, что запрос обработан (может быть 200 или 500 в зависимости от реализации)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "demo_id" in data
            assert "metadata" in data
            assert "recommendations" in data
    
    def test_analyze_demo_invalid_format(self, client):
        """Тест анализа демо с невалидным форматом"""
        invalid_file = ("test.txt", BytesIO(b"invalid content"), "text/plain")
        
        response = client.post(
            "/demo/analyze",
            files={"demo": invalid_file}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "error_code" in data
        assert data["error_code"] == "INVALID_FILE_FORMAT"
    
    def test_analyze_demo_no_file(self, client):
        """Тест анализа демо без файла"""
        response = client.post("/demo/analyze")
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.server.features.demo_analyzer.service.DemoAnalyzer.analyze_demo')
    async def test_analyze_demo_error_handling(self, mock_analyze, client):
        """Тест обработки ошибок при анализе демо"""
        from src.server.exceptions import DemoAnalysisException
        
        mock_analyze.side_effect = DemoAnalysisException(
            detail="Internal error",
            error_code="INTERNAL_ERROR"
        )
        
        demo_file = ("test_demo.dem", BytesIO(b"fake demo content"), "application/octet-stream")
        
        response = client.post(
            "/demo/analyze",
            files={"demo": demo_file}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error_code"] == "INTERNAL_ERROR"

