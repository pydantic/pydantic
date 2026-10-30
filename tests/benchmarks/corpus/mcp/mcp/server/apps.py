# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ResourcePermissions(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    camera: dict[str, Any] | None = None
    microphone: dict[str, Any] | None = None
    geolocation: dict[str, Any] | None = None
    clipboard_write: dict[str, Any] | None = None

class ResourceCsp(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    connect_domains: list[str] | None = None
    resource_domains: list[str] | None = None
    frame_domains: list[str] | None = None
    base_uri_domains: list[str] | None = None
