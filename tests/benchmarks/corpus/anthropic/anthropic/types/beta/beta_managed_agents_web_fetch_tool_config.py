
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_auto_policy import BetaManagedAgentsAutoPolicy
from .beta_managed_agents_always_ask_policy import BetaManagedAgentsAlwaysAskPolicy
from .beta_managed_agents_always_allow_policy import BetaManagedAgentsAlwaysAllowPolicy
from .beta_managed_agents_web_fetch_url_sources import BetaManagedAgentsWebFetchURLSources
PermissionPolicy: TypeAlias = Annotated[Union[BetaManagedAgentsAlwaysAllowPolicy, BetaManagedAgentsAlwaysAskPolicy, BetaManagedAgentsAutoPolicy], UnionDiscriminator('type')]

class BetaManagedAgentsWebFetchToolConfig(BaseModel):
    """Configuration for the web_fetch tool."""
    enabled: bool
    name: Literal['web_fetch']
    permission_policy: PermissionPolicy
    type: Literal['web_fetch']
    url_sources: Optional[BetaManagedAgentsWebFetchURLSources] = None
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    max_content_tokens: Optional[int] = None
