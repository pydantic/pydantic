# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class PersistedMcpTransportResourceHTTP(BaseModel):
    """Connects to an MCP server over HTTP."""
    headers: Dict[str, str]
    server_url: str
    type: Literal['http']

class PersistedMcpTransportResourceStdio(BaseModel):
    """Starts an MCP server as a local process."""
    args: List[str]
    command: str
    cwd: str
    env_vars: List[str]
    type: Literal['stdio']
PersistedMcpTransport: TypeAlias = Annotated[Union[PersistedMcpTransportResourceHTTP, PersistedMcpTransportResourceStdio], PropertyInfo(discriminator='type')]
