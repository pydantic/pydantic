
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_mcp_oauth_auth_response import BetaManagedAgentsMCPOAuthAuthResponse
from .beta_managed_agents_static_bearer_auth_response import BetaManagedAgentsStaticBearerAuthResponse
from .beta_managed_agents_environment_variable_auth_response import BetaManagedAgentsEnvironmentVariableAuthResponse
Auth: TypeAlias = Annotated[Union[BetaManagedAgentsMCPOAuthAuthResponse, BetaManagedAgentsStaticBearerAuthResponse, BetaManagedAgentsEnvironmentVariableAuthResponse], UnionDiscriminator('type')]

class BetaManagedAgentsCredential(BaseModel):
    """A credential stored in a vault.

    Sensitive fields are never returned in responses.
    """
    id: str
    archived_at: Optional[datetime] = None
    auth: Auth
    created_at: datetime
    metadata: Dict[str, str]
    type: Literal['vault_credential']
    updated_at: datetime
    vault_id: str
    display_name: Optional[str] = None
