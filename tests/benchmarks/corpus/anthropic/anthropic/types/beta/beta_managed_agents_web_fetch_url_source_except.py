
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_web_fetch_url_source_tool_reference import BetaManagedAgentsWebFetchURLSourceToolReference

class BetaManagedAgentsWebFetchURLSourceExcept(BaseModel):
    """
    Every tool's results contribute URLs that may be fetched, except the named tools' results.
    """
    tools: List[BetaManagedAgentsWebFetchURLSourceToolReference]
    type: Literal['except']
