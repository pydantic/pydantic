# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseMcpCallInProgress(BaseModel):
    """Returned when an MCP tool call has started and is in progress."""
    event_id: str
    item_id: str
    output_index: int
    type: Literal['response.mcp_call.in_progress']
