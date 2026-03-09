"""Prompt management router — CRUD API for prompt snippets."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.models.prompt import PromptSnippet, PromptSnippetCreate, PromptSnippetUpdate
from app.storage.prompt_store import (
    list_prompts,
    get_prompt,
    create_prompt,
    update_prompt,
    delete_prompt,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptSnippet])
async def list_all_prompts() -> list[PromptSnippet]:
    """List all prompt snippets."""
    return list_prompts()


@router.post("", response_model=PromptSnippet, status_code=201)
async def create_new_prompt(data: PromptSnippetCreate) -> PromptSnippet:
    """Create a new prompt snippet."""
    return create_prompt(data)


@router.get("/{prompt_id}", response_model=PromptSnippet)
async def get_single_prompt(prompt_id: str) -> PromptSnippet:
    """Get a single prompt snippet by ID."""
    snippet = get_prompt(prompt_id)
    if snippet is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return snippet


@router.put("/{prompt_id}", response_model=PromptSnippet)
async def update_existing_prompt(
    prompt_id: str, data: PromptSnippetUpdate
) -> PromptSnippet:
    """Update an existing prompt snippet."""
    snippet = update_prompt(prompt_id, data)
    if snippet is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return snippet


@router.delete("/{prompt_id}")
async def delete_existing_prompt(prompt_id: str) -> dict:
    """Delete a prompt snippet."""
    if not delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"detail": "Prompt deleted"}


@router.post("/import", response_model=PromptSnippet, status_code=201)
async def import_markdown(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    category: str = Form("general"),
) -> PromptSnippet:
    """Import a Markdown file as a new prompt snippet.

    The file content becomes the prompt content.
    If no name is provided, the filename (without extension) is used.
    """
    if not file.filename or not file.filename.endswith(".md"):
        raise HTTPException(
            status_code=400,
            detail="Only .md (Markdown) files are supported",
        )

    content = await file.read()
    text = content.decode("utf-8")

    if not text.strip():
        raise HTTPException(status_code=400, detail="File is empty")

    snippet_name = name or file.filename.rsplit(".", 1)[0]

    data = PromptSnippetCreate(
        name=snippet_name,
        content=text,
        category=category,
    )
    return create_prompt(data)
