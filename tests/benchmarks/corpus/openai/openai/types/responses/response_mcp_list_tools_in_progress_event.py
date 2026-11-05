# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseMcpListToolsInProgressEvent(BaseModel):
    """
    Emitted when the system is in the process of retrieving the list of available MCP tools.
    """
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.mcp_list_tools.in_progress']
