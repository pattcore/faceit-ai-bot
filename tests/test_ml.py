import pytest
from fastapi import UploadFile
from unittest.mock import Mock, patch
import io
import json
from tests.mocks.ml_model import analyze_demo, MockMLModel

@pytest.fixture
def mock_demo_data():
    # Create mock demo data
    demo_data = io.BytesIO(b"mock demo data")
    demo_data.seek(0)
    return demo_data

@pytest.fixture
def mock_demo_file(mock_image):
    return UploadFile(
        filename="test.dem",
        file=mock_image
    )

def test_analyze_demo():
    # Create a mock demo file
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.dem"
    mock_file.file = io.BytesIO(b"mock demo data")
    
    result = analyze_demo(mock_file)
    assert "filename" in result
    assert "prediction" in result
    assert "confidence" in result
    assert result["filename"] == "test.dem"
    assert isinstance(result["confidence"], float)
    assert 0 <= result["confidence"] <= 1

def test_analyze_demo_invalid_format():
    with pytest.raises(ValueError) as exc_info:
        analyze_demo(Mock(filename="test.jpg"))
    assert "Invalid file format" in str(exc_info.value)

def test_ml_model_loading():
    """Test ML model initialization"""
    model = MockMLModel()
    result = model.predict({"test": "data"})
    assert isinstance(result, dict)
    assert "prediction" in result
    assert "confidence" in result
    assert isinstance(result["confidence"], float)
    assert 0 <= result["confidence"] <= 1

def test_ml_model_cache():
    """Test that model results are consistent"""
    model = MockMLModel()
    data = {"test": "data"}
    
    # First prediction
    result1 = model.predict(data)
    # Second prediction with same data
    result2 = model.predict(data)
    
    # Results should be identical
    assert result1 == result2

def test_ml_service_cache():
    """Test that results are properly cached"""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.dem"
    mock_file.file = io.BytesIO(b"mock demo data")
    
    # First request
    result1 = analyze_demo(mock_file)
    mock_file.file.seek(0)  # Reset file pointer
    
    # Second request with same file
    result2 = analyze_demo(mock_file)
    
    # Results should be identical
    assert result1 == result2

@pytest.mark.parametrize("confidence_threshold", [0.5, 0.7, 0.9])
def test_analyze_demo_confidence_threshold(confidence_threshold):
    """Test different confidence thresholds for analysis"""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.dem"
    mock_file.file = io.BytesIO(b"mock demo data")
    
    model = MockMLModel()
    result = model.predict({"confidence_threshold": confidence_threshold})
    
    assert isinstance(result, dict)
    assert "confidence" in result
    assert result["confidence"] >= confidence_threshold

def test_analyze_demo_empty_file():
    """Test handling of empty demo file"""
    empty_file = Mock(spec=UploadFile)
    empty_file.filename = "empty.dem"
    empty_file.file = io.BytesIO(b"")
    
    with pytest.raises(ValueError) as exc_info:
        analyze_demo(empty_file)
    assert "Empty file" in str(exc_info.value)