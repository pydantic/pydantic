# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class McpListToolsFailed(BaseModel):
    """Returned when listing MCP tools has failed for an item."""
    event_id: str
    item_id: str
    type: Literal['mcp_list_tools.failed']
