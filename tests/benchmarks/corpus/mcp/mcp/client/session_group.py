# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Any
from pydantic import BaseModel, Field
from mcp.client.streamable_http import DEFAULT_MAX_SSE_EVENT_SIZE

class SseServerParameters(BaseModel):
    url: str
    headers: dict[str, Any] | None = None
    timeout: float = 5.0
    sse_read_timeout: float = 300.0

class StreamableHttpParameters(BaseModel):
    url: str
    headers: dict[str, Any] | None = None
    timeout: float = 30.0
    sse_read_timeout: float = 300.0
    terminate_on_close: bool = True
    max_sse_event_size: int | None = Field(default=DEFAULT_MAX_SSE_EVENT_SIZE, gt=0)
