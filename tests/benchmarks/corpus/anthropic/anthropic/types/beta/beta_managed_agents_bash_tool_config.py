
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_auto_policy import BetaManagedAgentsAutoPolicy
from .beta_managed_agents_always_ask_policy import BetaManagedAgentsAlwaysAskPolicy
from .beta_managed_agents_always_allow_policy import BetaManagedAgentsAlwaysAllowPolicy
PermissionPolicy: TypeAlias = Annotated[Union[BetaManagedAgentsAlwaysAllowPolicy, BetaManagedAgentsAlwaysAskPolicy, BetaManagedAgentsAutoPolicy], UnionDiscriminator('type')]

class BetaManagedAgentsBashToolConfig(BaseModel):
    """Configuration for the bash tool."""
    enabled: bool
    name: Literal['bash']
    permission_policy: PermissionPolicy
    type: Literal['bash']
