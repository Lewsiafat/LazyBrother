"""Anthropic Claude LLM provider."""

from anthropic import AsyncAnthropic

from app.config import settings
from app.providers.base import LLMProvider


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = model

    async def synthesize(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=(
                "You are an expert technical analyst and trader. "
                "Analyze the provided market data and return your "
                "trading advice as valid JSON only, no markdown."
            ),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        # Extract text from content blocks
        return "".join(
            block.text for block in response.content if hasattr(block, "text")
        )
