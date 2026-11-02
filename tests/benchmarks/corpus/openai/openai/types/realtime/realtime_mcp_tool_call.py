# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .realtime_mcphttp_error import RealtimeMcphttpError
from .realtime_mcp_protocol_error import RealtimeMcpProtocolError
from .realtime_mcp_tool_execution_error import RealtimeMcpToolExecutionError
Error: TypeAlias = Annotated[Union[RealtimeMcpProtocolError, RealtimeMcpToolExecutionError, RealtimeMcphttpError, None], PropertyInfo(discriminator='type')]

class RealtimeMcpToolCall(BaseModel):
    """A Realtime item representing an invocation of a tool on an MCP server."""
    id: str
    arguments: str
    name: str
    server_label: str
    type: Literal['mcp_call']
    approval_request_id: Optional[str] = None
    error: Optional[Error] = None
    output: Optional[str] = None
