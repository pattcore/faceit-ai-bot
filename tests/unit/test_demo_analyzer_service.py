"""
Unit тесты для сервиса анализа демо
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import UploadFile
from io import BytesIO

from src.server.features.demo_analyzer.service import DemoAnalyzer
from src.server.exceptions import DemoAnalysisException


@pytest.mark.unit
class TestDemoAnalyzer:
    """Тесты для DemoAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Создание анализатора"""
        return DemoAnalyzer()
    
    @pytest.fixture
    def demo_file(self):
        """Фикстура для демо-файла"""
        file = Mock(spec=UploadFile)
        file.filename = "test_demo.dem"
        file.read = AsyncMock(return_value=b"fake demo content")
        file.file = BytesIO(b"fake demo content")
        return file
    
    @pytest.fixture
    def invalid_file(self):
        """Фикстура для невалидного файла"""
        file = Mock(spec=UploadFile)
        file.filename = "test.txt"
        return file
    
    @pytest.mark.asyncio
    async def test_analyze_demo_success(self, analyzer, demo_file):
        """Test successful demo analysis"""
        result = await analyzer.analyze_demo(demo_file)
        
        assert result is not None
        assert result.demo_id is not None
        assert result.metadata is not None
        assert result.recommendations is not None
    
    @pytest.mark.asyncio
    async def test_analyze_demo_invalid_file_format(self, analyzer, invalid_file):
        """Тест обработки невалидного формата файла"""
        with pytest.raises(DemoAnalysisException) as exc_info:
            await analyzer.analyze_demo(invalid_file)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "Only .dem files are supported" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_analyze_demo_no_filename(self, analyzer):
        """Тест обработки файла без имени"""
        file = Mock(spec=UploadFile)
        file.filename = None
        
        with pytest.raises(DemoAnalysisException) as exc_info:
            await analyzer.analyze_demo(file)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
    
    @pytest.mark.asyncio
    async def test_parse_demo_file(self, analyzer, demo_file):
        """Тест парсинга демо-файла"""
        result = await analyzer._parse_demo_file(demo_file)
        
        assert result is not None
        assert "match_id" in result
        assert "map" in result
        assert "mode" in result
    
    @pytest.mark.asyncio
    async def test_analyze_player_performance(self, analyzer):
        """Тест анализа производительности игроков"""
        demo_data = {
            "match_id": "12345",
            "map": "de_dust2",
            "mode": "competitive"
        }
        
        result = await analyzer._analyze_player_performance(demo_data)
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_analyze_rounds(self, analyzer):
        """Тест анализа раундов"""
        demo_data = {
            "match_id": "12345",
            "map": "de_dust2",
            "mode": "competitive"
        }
        
        result = await analyzer._analyze_rounds(demo_data)
        
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_identify_key_moments(self, analyzer):
        """Тест определения ключевых моментов"""
        demo_data = {
            "match_id": "12345",
            "map": "de_dust2",
            "mode": "competitive"
        }
        
        result = await analyzer._identify_key_moments(demo_data)
        
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, analyzer):
        """Тест генерации рекомендаций"""
        player_performances = {}
        round_analysis = []
        key_moments = []
        
        result = await analyzer._generate_recommendations(
            player_performances,
            round_analysis,
            key_moments
        )
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_identify_improvement_areas(self, analyzer):
        """Тест определения областей для улучшения"""
        player_performances = {}
        
        result = await analyzer._identify_improvement_areas(player_performances)
        
        assert result is not None
        assert isinstance(result, list)

