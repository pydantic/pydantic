# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from collections.abc import Callable, Hashable
from typing import Any
from mcp_types import Icon, ToolAnnotations
from pydantic import BaseModel, Field
from mcp.server.mcpserver.utilities.func_metadata import FuncMetadata

class Tool(BaseModel):
    fn: Callable[..., Any] = Field(exclude=True)
    name: str = Field(description='Name of the tool')
    title: str | None = Field(None, description='Human-readable title of the tool')
    description: str = Field(description='Description of what the tool does')
    parameters: dict[str, Any] = Field(description='JSON schema for tool parameters')
    fn_metadata: FuncMetadata = Field(description='Metadata about the function including a pydantic model for tool arguments')
    is_async: bool = Field(description='Whether the tool is async')
    context_kwarg: str | None = Field(None, description='Name of the kwarg that should receive context')
    resolved_params: dict[str, Any] = Field(default_factory=lambda: {}, exclude=True, description='Parameters filled by resolvers, mapped to (Resolve, wants_union)')
    resolver_plans: dict[Hashable, Any] = Field(default_factory=lambda: {}, exclude=True, description='Static per-resolver parameter plans')
    annotations: ToolAnnotations | None = Field(None, description='Optional annotations for the tool')
    icons: list[Icon] | None = Field(default=None, description='Optional list of icons for this tool')
    meta: dict[str, Any] | None = Field(default=None, description='Optional metadata for this tool')
