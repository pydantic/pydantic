# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Literal
from mcp_types import ContentBlock, Icon, InputRequiredResult, TextContent
from pydantic import BaseModel, Field
from mcp.server.mcpserver.utilities.types import Audio, Image

class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: ContentBlock

    def __init__(self, content: str | ContentBlock | Image | Audio, **kwargs: Any):
        if isinstance(content, str):
            content = TextContent(type='text', text=content)
        elif isinstance(content, Image):
            content = content.to_image_content()
        elif isinstance(content, Audio):
            content = content.to_audio_content()
        super().__init__(content=content, **kwargs)

class UserMessage(Message):
    role: Literal['user', 'assistant'] = 'user'

    def __init__(self, content: str | ContentBlock | Image | Audio, **kwargs: Any):
        super().__init__(content=content, **kwargs)

class AssistantMessage(Message):
    role: Literal['user', 'assistant'] = 'assistant'

    def __init__(self, content: str | ContentBlock | Image | Audio, **kwargs: Any):
        super().__init__(content=content, **kwargs)
_PromptResultItem = str | ContentBlock | Image | Audio | Message | dict[str, Any]
SyncPromptResult = _PromptResultItem | InputRequiredResult | Sequence[_PromptResultItem]
PromptResult = SyncPromptResult | Awaitable[SyncPromptResult]

class PromptArgument(BaseModel):
    name: str = Field(description='Name of the argument')
    description: str | None = Field(None, description='Description of what the argument does')
    required: bool = Field(default=False, description='Whether the argument is required')

class Prompt(BaseModel):
    name: str = Field(description='Name of the prompt')
    title: str | None = Field(None, description='Human-readable title of the prompt')
    description: str | None = Field(None, description='Description of what the prompt does')
    arguments: list[PromptArgument] | None = Field(None, description='Arguments that can be passed to the prompt')
    fn: Callable[..., PromptResult | Awaitable[PromptResult]] = Field(exclude=True)
    icons: list[Icon] | None = Field(default=None, description='Optional list of icons for this prompt')
    context_kwarg: str | None = Field(None, description='Name of the kwarg that should receive context', exclude=True)
