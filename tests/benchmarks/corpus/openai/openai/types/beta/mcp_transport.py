# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class McpTransportResourceHTTP(BaseModel):
    """Connects to an MCP server over HTTP."""
    server_url: str
    type: Literal['http']

class McpTransportResourceStdio(BaseModel):
    """Starts an MCP server as a local process."""
    args: List[str]
    command: str
    cwd: str
    env_vars: List[str]
    type: Literal['stdio']
McpTransport: TypeAlias = Annotated[Union[McpTransportResourceHTTP, McpTransportResourceStdio], PropertyInfo(discriminator='type')]
