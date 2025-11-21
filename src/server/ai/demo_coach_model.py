from __future__ import annotations

from typing import Any

from .groq_service import GroqService
from src.server.features.demo_analyzer.models import (
    CoachReport,
    DemoAnalysisInput,
)


class DemoCoachModel:
    """Interface for the demo coaching model.

    This class is a placeholder for an actual model implementation
    (fine-tuned LLM or external API). It should take DemoAnalysisInput
    and return a structured CoachReport.
    """

    def __init__(self, model_name: str | None = None, **kwargs: Any) -> None:
        """Initialize the model client or load local weights.

        Args:
            model_name: Optional model identifier used by the underlying
                provider (local or external).
            **kwargs: Additional provider-specific options.
        """
        self.model_name = model_name or "demo_coach_default"
        self._client: Any | None = None
        self._service = GroqService(api_key=kwargs.get("api_key"))

    async def generate_coach_report(
        self,
        demo_input: DemoAnalysisInput,
        language: str = "ru",
    ) -> CoachReport:
        """Generate a CoachReport for the given demo input.

        This method should:
        - build a prompt from DemoAnalysisInput,
        - send it to the underlying model (local or external),
        - parse the response into a CoachReport instance.

        Currently it raises NotImplementedError and must be implemented
        when a real model is available.
        """
        lang = language or demo_input.language
        payload = demo_input.model_dump()
        result = await self._service.generate_demo_coach_report(
            demo_input=payload,
            language=lang,
        )
        if not result:
            return CoachReport()
        return CoachReport.model_validate(result)
