
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_managed_agents_web_fetch_url_source_user_input import BetaManagedAgentsWebFetchURLSourceUserInput
from .beta_managed_agents_web_fetch_url_source_tool_filter import BetaManagedAgentsWebFetchURLSourceToolFilter

class BetaManagedAgentsWebFetchURLSources(BaseModel):
    """Which sources contribute URLs the web_fetch tool may fetch.

    A key that is null was not set and allows every URL from that source.
    """
    client_tool_results: Optional[BetaManagedAgentsWebFetchURLSourceToolFilter] = None
    server_tool_results: Optional[BetaManagedAgentsWebFetchURLSourceToolFilter] = None
    user_input: Optional[BetaManagedAgentsWebFetchURLSourceUserInput] = None
