# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeMcpApprovalRequest(BaseModel):
    """A Realtime item requesting human approval of a tool invocation."""
    id: str
    arguments: str
    name: str
    server_label: str
    type: Literal['mcp_approval_request']
