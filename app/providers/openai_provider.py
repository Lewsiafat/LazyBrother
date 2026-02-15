"""OpenAI LLM provider."""

from openai import AsyncOpenAI

from app.config import settings
from app.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, model: str = "gpt-4o") -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model

    async def synthesize(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical analyst and trader. "
                        "Analyze the provided market data and return your "
                        "trading advice as valid JSON only, no markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""
