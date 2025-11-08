"""
Unit тесты для валидаторов
"""
import pytest
from pydantic import ValidationError

from src.server.features.demo_analyzer.validators import DemoFileValidator


@pytest.mark.unit
class TestValidators:
    """Тесты для валидаторов"""
    
    def test_demo_file_validator_success(self):
        """Тест успешной валидации демо-файла"""
        validator = DemoFileValidator(
            filename="test_demo.dem",
            content_type="application/octet-stream",
            size=1024
        )
        
        assert validator.filename == "test_demo.dem"
        assert validator.size == 1024
    
    def test_demo_file_validator_invalid_extension(self):
        """Тест валидации файла с невалидным расширением"""
        with pytest.raises(ValidationError) as exc_info:
            DemoFileValidator(
                filename="test.txt",
                content_type="text/plain",
                size=1024
            )
        
        assert "Only .dem files are supported" in str(exc_info.value)
    
    def test_demo_file_validator_empty_filename(self):
        """Тест валидации файла с пустым именем"""
        with pytest.raises(ValidationError):
            DemoFileValidator(
                filename="",
                content_type="application/octet-stream",
                size=1024
            )
    
    def test_demo_file_validator_too_large(self):
        """Тест валидации файла слишком большого размера"""
        with pytest.raises(ValidationError) as exc_info:
            DemoFileValidator(
                filename="test_demo.dem",
                content_type="application/octet-stream",
                size=200 * 1024 * 1024  # 200MB
            )
        
        assert "exceeds maximum" in str(exc_info.value)
    
    def test_demo_file_validator_zero_size(self):
        """Тест валидации файла с нулевым размером"""
        with pytest.raises(ValidationError) as exc_info:
            DemoFileValidator(
                filename="test_demo.dem",
                content_type="application/octet-stream",
                size=0
            )
        
        assert "greater than 0" in str(exc_info.value)
    
    def test_demo_file_validator_negative_size(self):
        """Тест валидации файла с отрицательным размером"""
        with pytest.raises(ValidationError):
            DemoFileValidator(
                filename="test_demo.dem",
                content_type="application/octet-stream",
                size=-100
            )

