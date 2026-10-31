# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseMcpCallArgumentsDelta(BaseModel):
    """Returned when MCP tool call arguments are updated during response generation."""
    delta: str
    event_id: str
    item_id: str
    output_index: int
    response_id: str
    type: Literal['response.mcp_call_arguments.delta']
    obfuscation: Optional[str] = None
