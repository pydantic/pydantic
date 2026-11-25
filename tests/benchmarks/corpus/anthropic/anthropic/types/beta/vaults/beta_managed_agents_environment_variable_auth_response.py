
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_injection_location_response import BetaManagedAgentsInjectionLocationResponse
from .beta_managed_agents_limited_credential_networking_response import BetaManagedAgentsLimitedCredentialNetworkingResponse
from .beta_managed_agents_unrestricted_credential_networking_response import BetaManagedAgentsUnrestrictedCredentialNetworkingResponse
Networking: TypeAlias = Annotated[Union[BetaManagedAgentsUnrestrictedCredentialNetworkingResponse, BetaManagedAgentsLimitedCredentialNetworkingResponse], UnionDiscriminator('type')]

class BetaManagedAgentsEnvironmentVariableAuthResponse(BaseModel):
    """Environment variable credential details. The secret value is never returned."""
    injection_location: BetaManagedAgentsInjectionLocationResponse
    networking: Networking
    secret_name: str
    type: Literal['environment_variable']
