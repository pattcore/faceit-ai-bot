from fastapi import APIRouter, Depends, File, UploadFile
from typing import List, Dict
from ..demo_analyzer.service import DemoAnalyzer
from ..demo_analyzer.models import DemoAnalysis
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))
from exceptions import DemoAnalysisException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/demo", tags=["demo"])

demo_analyzer = DemoAnalyzer()

@router.post(
    "/analyze",
    response_model=DemoAnalysis,
    summary="Анализ демо-файла",
    description="Анализирует загруженный демо-файл CS2 и возвращает детальный анализ",
    responses={
        200: {
            "description": "Анализ успешно выполнен"
        },
        400: {
            "description": "Невалидный файл",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Invalid file format. Only .dem files are supported",
                        "error_code": "INVALID_FILE_FORMAT"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера"
        }
    }
)
async def analyze_demo(demo: UploadFile = File(...)):
    """
    Анализ демо файла CS2
    
    Принимает демо-файл в формате .dem и возвращает детальный анализ игры,
    включая производительность игроков, анализ раундов и рекомендации.
    """
    return await demo_analyzer.analyze_demo(demo)