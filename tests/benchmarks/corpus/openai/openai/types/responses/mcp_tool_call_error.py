# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class McpProtocolError(BaseModel):
    code: int
    message: str
    type: Literal['mcp_protocol_error']

class McpToolExecutionError(BaseModel):
    content: object
    type: Literal['mcp_tool_execution_error']

class HTTPError(BaseModel):
    code: int
    message: str
    type: Literal['http_error']
McpToolCallError: TypeAlias = Annotated[Union[McpProtocolError, McpToolExecutionError, HTTPError], PropertyInfo(discriminator='type')]
