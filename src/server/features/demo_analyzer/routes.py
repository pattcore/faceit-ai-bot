import logging

from fastapi import APIRouter, File, UploadFile

from ..demo_analyzer.service import DemoAnalyzer
from ..demo_analyzer.models import DemoAnalysis

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/demo",
    tags=["demo"]
)

demo_analyzer = DemoAnalyzer()


@router.post(
    "/analyze",
    response_model=DemoAnalysis,
    summary="Demo file analysis",
    description=(
        "Analyzes uploaded CS2 demo file and "
        "returns detailed analysis"
    ),
    responses={
        200: {
            "description": "Analysis completed successfully"
        },
        400: {
            "description": "Invalid file",
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
            "description": "Internal server error"
        }
    }
)
async def analyze_demo(demo: UploadFile = File(...)):
    """
    CS2 demo file analysis

    Accepts demo file in .dem format and returns detailed game analysis,
    including player performance, round analysis and recommendations.
    """
    return await demo_analyzer.analyze_demo(demo)
