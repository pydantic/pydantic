
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_web_fetch_url_source_all import BetaManagedAgentsWebFetchURLSourceAll
from .beta_managed_agents_web_fetch_url_source_none import BetaManagedAgentsWebFetchURLSourceNone
BetaManagedAgentsWebFetchURLSourceUserInput: TypeAlias = Annotated[Union[BetaManagedAgentsWebFetchURLSourceAll, BetaManagedAgentsWebFetchURLSourceNone], UnionDiscriminator('type')]
