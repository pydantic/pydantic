
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_token_endpoint_auth_none_response import BetaManagedAgentsTokenEndpointAuthNoneResponse
from .beta_managed_agents_token_endpoint_auth_post_response import BetaManagedAgentsTokenEndpointAuthPostResponse
from .beta_managed_agents_token_endpoint_auth_basic_response import BetaManagedAgentsTokenEndpointAuthBasicResponse
TokenEndpointAuth: TypeAlias = Annotated[Union[BetaManagedAgentsTokenEndpointAuthNoneResponse, BetaManagedAgentsTokenEndpointAuthBasicResponse, BetaManagedAgentsTokenEndpointAuthPostResponse], UnionDiscriminator('type')]

class BetaManagedAgentsMCPOAuthRefreshResponse(BaseModel):
    """OAuth refresh token configuration returned in credential responses."""
    client_id: str
    token_endpoint: str
    token_endpoint_auth: TokenEndpointAuth
    resource: Optional[str] = None
    scope: Optional[str] = None
