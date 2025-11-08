"""
This is a mock module for testing purposes
"""
from typing import Dict, Any

class MockMLModel:
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        confidence = 0.95  # High base confidence
        
        # If confidence threshold is specified, use it
        if "confidence_threshold" in data:
            confidence = max(confidence, float(data["confidence_threshold"]))
            
        return {
            "prediction": "positive",
            "confidence": confidence
        }

model = MockMLModel()

def analyze_demo(demo_file) -> Dict[str, Any]:
    if not demo_file.filename.endswith('.dem'):
        raise ValueError("Invalid file format")
        
    file_content = demo_file.file.read()
    if not file_content:
        raise ValueError("Empty file")
        
    demo_file.file.seek(0)  # Reset file pointer
        
    return {
        "filename": demo_file.filename,
        "prediction": "positive",
        "confidence": 0.85
    }