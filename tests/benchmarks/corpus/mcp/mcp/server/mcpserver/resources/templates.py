# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from collections.abc import Callable, Set
from dataclasses import dataclass, field
from typing import Any
from mcp_types import Annotations, Icon
from pydantic import BaseModel, Field
from mcp.shared.uri_template import UriTemplate

@dataclass(frozen=True)
class ResourceSecurity:
    reject_path_traversal: bool = True
    reject_absolute_paths: bool = True
    reject_null_bytes: bool = True
    exempt_params: Set[str] = field(default_factory=frozenset[str])

class ResourceTemplate(BaseModel):
    uri_template: str = Field(description='URI template with parameters (e.g. weather://{city}/current)')
    name: str = Field(description='Name of the resource')
    title: str | None = Field(description='Human-readable title of the resource', default=None)
    description: str | None = Field(description='Description of what the resource does')
    mime_type: str = Field(default='text/plain', description='MIME type of the resource content')
    icons: list[Icon] | None = Field(default=None, description='Optional list of icons for the resource template')
    annotations: Annotations | None = Field(default=None, description='Optional annotations for the resource template')
    meta: dict[str, Any] | None = Field(default=None, description='Optional metadata for this resource template')
    fn: Callable[..., Any] = Field(exclude=True)
    parameters: dict[str, Any] = Field(description='JSON schema for function parameters')
    context_kwarg: str | None = Field(None, description='Name of the kwarg that should receive context')
    parsed_template: UriTemplate = Field(exclude=True, description='Parsed RFC 6570 template')
    security: ResourceSecurity = Field(exclude=True, description='Path-safety policy for extracted parameters')
