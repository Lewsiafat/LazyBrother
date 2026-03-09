"""Prompt snippet models for custom analysis instructions."""

from datetime import datetime
from pydantic import BaseModel, Field


class PromptSnippet(BaseModel):
    """A reusable prompt snippet that can be attached to analysis requests."""

    id: str = Field(..., description="Unique identifier (UUID)")
    name: str = Field(..., description="Display name for the snippet")
    content: str = Field(..., description="Prompt content (supports Markdown)")
    category: str = Field(
        default="general",
        description="Category: 'general', 'strategy', 'risk', 'style'",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this snippet is enabled by default",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())


class PromptSnippetCreate(BaseModel):
    """Request body for creating a new prompt snippet."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    content: str = Field(..., min_length=1, description="Prompt content (Markdown)")
    category: str = Field(
        default="general",
        description="Category: 'general', 'strategy', 'risk', 'style'",
    )
    is_active: bool = Field(default=True)


class PromptSnippetUpdate(BaseModel):
    """Request body for updating a prompt snippet (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    content: str | None = Field(None, min_length=1)
    category: str | None = None
    is_active: bool | None = None
