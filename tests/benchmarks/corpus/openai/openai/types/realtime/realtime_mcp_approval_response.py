# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeMcpApprovalResponse(BaseModel):
    """A Realtime item responding to an MCP approval request."""
    id: str
    approval_request_id: str
    approve: bool
    type: Literal['mcp_approval_response']
    reason: Optional[str] = None
