# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel
from .credential_networking import CredentialNetworking
from .mcp_oauth_token_endpoint_auth import McpOauthTokenEndpointAuth

class VaultCredentialAuthResourceMcpOauthRefresh(BaseModel):
    """Public refresh metadata without refresh tokens or OAuth client secrets."""
    client_id: str
    resource: Optional[str] = None
    scope: Optional[str] = None
    token_endpoint: str
    token_endpoint_auth: McpOauthTokenEndpointAuth

class VaultCredentialAuthResourceMcpOauth(BaseModel):
    """
    Public metadata for an OAuth credential; tokens and client secrets are never returned.
    """
    expires_at: Optional[str] = None
    mcp_server_url: str
    refresh: Optional[VaultCredentialAuthResourceMcpOauthRefresh] = None
    type: Literal['mcp_oauth']

class VaultCredentialAuthResourceStaticBearer(BaseModel):
    """Metadata for a bearer-token credential, without automatic OAuth refresh."""
    mcp_server_url: str
    type: Literal['static_bearer']

class VaultCredentialAuthResourceEnvironmentVariable(BaseModel):
    """Metadata for an HTTP credential used only in OpenAI-hosted environments.

    Sandbox code receives a placeholder. The proxy substitutes the secret for allowed HTTPS destinations on ports 443 and 8443. The real secret is not available to sandbox code for local computation and is never returned in this resource.
    """
    networking: CredentialNetworking
    secret_name: str
    type: Literal['environment_variable']
CredentialAuth: TypeAlias = Annotated[Union[VaultCredentialAuthResourceMcpOauth, VaultCredentialAuthResourceStaticBearer, VaultCredentialAuthResourceEnvironmentVariable], PropertyInfo(discriminator='type')]
