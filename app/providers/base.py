"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base interface for all LLM providers.

    Each provider must implement the `synthesize` method that takes
    a prompt string and returns the LLM's text response.
    """

    @abstractmethod
    async def synthesize(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the response text.

        Args:
            prompt: The full analysis prompt with pattern/indicator/SMC data.

        Returns:
            Raw text response from the LLM (expected to be JSON).

        Raises:
            Exception: If the LLM call fails.
        """
        ...
