"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """LazyBrother configuration.

    All values are read from environment variables or a .env file.
    """

    # LLM Provider
    llm_provider: str = Field(
        default="openai",
        description="LLM provider to use: 'openai', 'gemini', or 'claude'",
    )

    # LLM API Keys
    openai_api_key: str = Field(default="", description="OpenAI API key")
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # Data Source API Keys
    binance_api_key: str = Field(default="", description="Binance API key")
    binance_api_secret: str = Field(default="", description="Binance API secret")
    alpha_vantage_api_key: str = Field(default="", description="Alpha Vantage API key")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton settings instance
settings = Settings()
