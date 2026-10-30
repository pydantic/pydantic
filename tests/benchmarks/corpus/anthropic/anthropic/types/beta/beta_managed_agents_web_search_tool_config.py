
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_auto_policy import BetaManagedAgentsAutoPolicy
from .beta_managed_agents_user_location import BetaManagedAgentsUserLocation
from .beta_managed_agents_always_ask_policy import BetaManagedAgentsAlwaysAskPolicy
from .beta_managed_agents_always_allow_policy import BetaManagedAgentsAlwaysAllowPolicy
PermissionPolicy: TypeAlias = Annotated[Union[BetaManagedAgentsAlwaysAllowPolicy, BetaManagedAgentsAlwaysAskPolicy, BetaManagedAgentsAutoPolicy], UnionDiscriminator('type')]

class BetaManagedAgentsWebSearchToolConfig(BaseModel):
    """Configuration for the web_search tool."""
    enabled: bool
    name: Literal['web_search']
    permission_policy: PermissionPolicy
    type: Literal['web_search']
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    user_location: Optional[BetaManagedAgentsUserLocation] = None
