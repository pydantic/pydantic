# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
import abc
from typing import Any
from mcp_types import Annotations, Icon
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

class Resource(BaseModel, abc.ABC):
    model_config = ConfigDict(validate_default=True, extra='forbid')
    uri: str = Field(default=..., description='URI of the resource')
    name: str | None = Field(description='Name of the resource', default=None)
    title: str | None = Field(description='Human-readable title of the resource', default=None)
    description: str | None = Field(description='Description of the resource', default=None)
    mime_type: str = Field(default='text/plain', description='MIME type of the resource content')
    icons: list[Icon] | None = Field(default=None, description='Optional list of icons for this resource')
    annotations: Annotations | None = Field(default=None, description='Optional annotations for the resource')
    meta: dict[str, Any] | None = Field(default=None, description='Optional metadata for this resource')

    @field_validator('name', mode='before')
    @classmethod
    def set_default_name(cls, name: str | None, info: ValidationInfo) -> str:
        if name:
            return name
        if (uri := info.data.get('uri')):
            return str(uri)
        raise ValueError('Either name or uri must be provided')
