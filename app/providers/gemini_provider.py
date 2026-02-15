"""Google Gemini LLM provider."""

import google.generativeai as genai

from app.config import settings
from app.providers.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=model,
            system_instruction=(
                "You are an expert technical analyst and trader. "
                "Analyze the provided market data and return your "
                "trading advice as valid JSON only, no markdown."
            ),
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )

    async def synthesize(self, prompt: str) -> str:
        response = await self.model.generate_content_async(prompt)
        return response.text or ""
