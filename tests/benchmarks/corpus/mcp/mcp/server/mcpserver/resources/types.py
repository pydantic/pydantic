# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
import pydantic
from pydantic import Field
from mcp.server.mcpserver.resources.base import Resource
_TEXTUAL_APPLICATION_TYPES = frozenset({'application/json', 'application/xml'})

def _default_file_encoding(mime_type: str) -> str | None:
    essence, *params = (part.strip() for part in mime_type.split(';'))
    for param in params:
        name, _, value = param.partition('=')
        if name.strip().lower() == 'charset' and value:
            return value.strip().strip('"')
    essence = essence.lower()
    if essence.startswith('text/') or essence.endswith(('+json', '+xml')) or essence in _TEXTUAL_APPLICATION_TYPES:
        return 'utf-8-sig'
    return None

class TextResource(Resource):
    text: str = Field(description='Text content of the resource')

class BinaryResource(Resource):
    data: bytes = Field(description='Binary content of the resource')

class FunctionResource(Resource):
    fn: Callable[[], Any] = Field(exclude=True)

class FileResource(Resource):
    path: Path = Field(description='Path to the file')
    encoding: str | None = Field(default_factory=lambda data: _default_file_encoding(data['mime_type']), description='Text encoding used to decode the file, or None to serve its bytes as a blob')

    @pydantic.field_validator('path')
    @classmethod
    def validate_absolute_path(cls, path: Path) -> Path:
        if not path.is_absolute():
            raise ValueError('Path must be absolute')
        return path

    @pydantic.field_validator('encoding')
    @classmethod
    def validate_text_encoding(cls, encoding: str | None) -> str | None:
        if encoding is not None:
            try:
                b'x'.decode(encoding)
            except LookupError as e:
                raise ValueError(str(e)) from e
            except UnicodeError:
                pass
        return encoding

class HttpResource(Resource):
    url: str = Field(description='URL to fetch content from')
    mime_type: str = Field(default='application/json', description='MIME type of the resource content')

class DirectoryResource(Resource):
    path: Path = Field(description='Path to the directory')
    recursive: bool = Field(default=False, description='Whether to list files recursively')
    pattern: str | None = Field(default=None, description='Optional glob pattern to filter files')
    mime_type: str = Field(default='application/json', description='MIME type of the resource content')

    @pydantic.field_validator('path')
    @classmethod
    def validate_absolute_path(cls, path: Path) -> Path:
        if not path.is_absolute():
            raise ValueError('Path must be absolute')
        return path
